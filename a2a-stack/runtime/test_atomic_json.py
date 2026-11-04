"""Regression tests for the atomic checkpoint writer.

These cover the failure-reporting contract that the autonomy layer depends on:
``autonomy/runner.py::Journal.record`` maps a ``PermissionError`` whose
``winerror`` is in ``(5, 32, 33)`` to ``OwnedSnapshotUnavailable``, and
``autonomy/manager.py`` then retries that write in a loop with no ceiling.  A
checkpoint writer that reports the wrong error therefore turns a permanent,
non-recoverable fault into an unbounded retry.
"""
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

NORTHSTAR_ROOT = Path(__file__).resolve().parents[2]
TEST_CONTROL = NORTHSTAR_ROOT / "tmp" / "a2a-stack" / "runtime-tests" / "control"
os.environ["A2A_TEST_CONTROL_DIR"] = str(TEST_CONTROL)
import runner

RECOVERABLE = (5, 32, 33)


def permission_error(code, message="synthetic sharing failure"):
    """A PermissionError carrying the Windows winerror the OS would set."""
    error = PermissionError(code, message)
    error.winerror = code
    return error


def cleanup_error_of(exc):
    """The cleanup error attached to `exc`, by either mechanism, or None."""
    for note in getattr(exc, "__notes__", []):
        if "cleanup failed" in note:
            return note
    return getattr(exc, "cleanup_error", None)


def cleanup_error_attached(exc):
    """Whether the cleanup failure was attached rather than substituted."""
    return cleanup_error_of(exc) is not None


class NoAddNote(OSError):
    """An exception shaped like Python 3.10's, where add_note does not exist.

    BaseException.add_note was added in 3.11.  a2a-sdk 1.3.0 declares
    Requires-Python >=3.10, so the writer's attribute fallback is reachable on
    an admitted interpreter and must be exercised by the suite rather than
    left as dead code on 3.11+.
    """

    def __getattribute__(self, name):
        if name == "add_note":
            raise AttributeError(name)
        return object.__getattribute__(self, name)


class AtomicJsonFailureReporting(unittest.TestCase):
    def setUp(self):
        self.directory = TEST_CONTROL.parent / "atomic-json" / os.urandom(8).hex()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "state.json"

    def tearDown(self):
        for entry in self.directory.glob("*"):
            entry.unlink(missing_ok=True)
        self.directory.rmdir()

    def write(self, generation="old"):
        runner.atomic_json(self.path, {"generation": generation})

    def residue(self):
        return list(self.directory.glob("*.tmp"))

    def test_successful_write_leaves_no_residue(self):
        self.write("old")
        self.write("new")
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), {"generation": "new"})
        self.assertEqual(self.residue(), [])

    def test_partial_write_failure_preserves_old_snapshot_and_leaves_no_residue(self):
        self.write("old")
        original = Path.write_text

        def partial_then_fail(path, data, **kwargs):
            if path.name.endswith(".tmp"):
                original(path, "{", encoding="utf-8")
                raise OSError(28, "synthetic disk exhaustion during write")
            return original(path, data, **kwargs)

        with patch.object(Path, "write_text", partial_then_fail):
            with self.assertRaisesRegex(OSError, "synthetic disk exhaustion during write"):
                runner.atomic_json(self.path, {"generation": "new"})
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8")), {"generation": "old"})
        self.assertEqual(self.residue(), [])

    def test_cleanup_failure_does_not_replace_a_non_recoverable_replace_failure(self):
        # The replace failure carries winerror 87, which is NOT in the
        # recoverable set; the cleanup failure carries winerror 5, which IS.
        # Reporting the cleanup error would make an honest failure look like a
        # retryable sharing violation.
        with patch.object(runner.os, "replace", side_effect=permission_error(87)), \
             patch.object(Path, "unlink", side_effect=permission_error(5)):
            with self.assertRaises(PermissionError) as caught:
                runner.atomic_json(self.path, {"generation": "new"})
        self.assertEqual(caught.exception.winerror, 87)
        self.assertNotIn(caught.exception.winerror, RECOVERABLE)

    def test_cleanup_failure_does_not_replace_a_recoverable_replace_failure(self):
        with patch.object(runner.os, "replace", side_effect=permission_error(32)), \
             patch.object(Path, "unlink", side_effect=permission_error(5)):
            with self.assertRaises(PermissionError) as caught:
                runner.atomic_json(self.path, {"generation": "new"})
        self.assertEqual(caught.exception.winerror, 32)
        self.assertIn(caught.exception.winerror, RECOVERABLE)

    def test_cleanup_failure_does_not_replace_a_non_permission_replace_failure(self):
        with patch.object(runner.os, "replace", side_effect=OSError(28, "synthetic disk exhaustion")), \
             patch.object(Path, "unlink", side_effect=permission_error(5)):
            with self.assertRaises(OSError) as caught:
                runner.atomic_json(self.path, {"generation": "new"})
        self.assertNotIsInstance(caught.exception, PermissionError)
        self.assertEqual(caught.exception.errno, 28)

    def test_cleanup_failure_is_attached_to_the_propagating_error(self):
        # The cleanup error must be ATTACHED to the propagating error, not
        # substituted for it.  It is attached as a note on Python 3.11+ and
        # as an attribute on 3.10, where BaseException.add_note does not
        # exist; both mechanisms satisfy this contract.
        with patch.object(runner.os, "replace", side_effect=permission_error(87)), \
             patch.object(Path, "unlink", side_effect=permission_error(5)):
            with self.assertRaises(PermissionError) as caught:
                runner.atomic_json(self.path, {"generation": "new"})
        self.assertEqual(caught.exception.winerror, 87)
        self.assertTrue(cleanup_error_attached(caught.exception), cleanup_error_of(caught.exception))

    def test_cleanup_failure_alone_is_still_raised(self):
        # On the success path there is no in-flight exception, so a failing
        # cleanup must not be silently swallowed.
        with patch.object(Path, "unlink", side_effect=permission_error(5)):
            with self.assertRaises(PermissionError) as caught:
                runner.atomic_json(self.path, {"generation": "new"})
        self.assertEqual(caught.exception.winerror, 5)

    def test_cleanup_failure_inside_an_outer_handler_is_not_swallowed(self):
        # The writer SUCCEEDED here and its cleanup failed.  The pre-fix
        # writer captured the pending exception with sys.exc_info(), which
        # reports the exception the current THREAD is handling -- so inside an
        # outer except handler it named the OUTER error, and the writer
        # concluded there was an in-flight failure to preserve and swallowed
        # its own cleanup failure.  The cleanup failure was lost, with no
        # diagnostic anywhere.  The repair captures the exception in the
        # frame that is unwinding, so on the success path nothing is pending
        # and the cleanup failure is raised.
        with patch.object(Path, "unlink", side_effect=permission_error(5)):
            try:
                try:
                    raise ValueError("the outer in-flight error")
                except ValueError:
                    with self.assertRaises(PermissionError) as caught:
                        runner.atomic_json(self.path, {"generation": "new"})
            except AssertionError:
                raise
            except ValueError:
                self.fail("the outer handler's error replaced the writer's")
        self.assertEqual(caught.exception.winerror, 5)

    def test_writer_failure_inside_an_outer_handler_keeps_the_writer_error(self):
        # The writer's own failure must propagate with its own winerror, and
        # the cleanup failure must be attached to it rather than replacing it.
        with patch.object(runner.os, "replace", side_effect=permission_error(87)), \
             patch.object(Path, "unlink", side_effect=permission_error(5)):
            try:
                try:
                    raise ValueError("the outer in-flight error")
                except ValueError:
                    with self.assertRaises(PermissionError) as caught:
                        runner.atomic_json(self.path, {"generation": "new"})
            except AssertionError:
                raise
            except ValueError:
                self.fail("the outer handler's error replaced the writer's")
        self.assertEqual(caught.exception.winerror, 87)
        self.assertTrue(cleanup_error_attached(caught.exception), cleanup_error_of(caught.exception))

    def test_cleanup_failure_outside_a_handler_keeps_the_writer_error(self):
        # The ordinary shape: the writer's own failure is what propagates and
        # the cleanup failure is attached to it rather than replacing it.
        with patch.object(runner.os, "replace", side_effect=permission_error(87)), \
             patch.object(Path, "unlink", side_effect=permission_error(5)):
            with self.assertRaises(PermissionError) as caught:
                runner.atomic_json(self.path, {"generation": "new"})
        self.assertEqual(caught.exception.winerror, 87)

    def test_cleanup_failure_does_not_replace_a_slotted_exception(self):
        # Some exception types reject arbitrary attributes.  The fallback that
        # attaches the cleanup error on an interpreter without add_note must
        # not itself raise, because that would replace the in-flight error --
        # and the in-flight error's winerror is what the autonomy layer
        # classifies on.
        class Slotted(OSError):
            __slots__ = ("winerror",)

        def slotted_replace(*args, **kwargs):
            error = Slotted(87, "synthetic unrecoverable failure")
            error.winerror = 87
            raise error

        with patch.object(runner.os, "replace", side_effect=slotted_replace), \
             patch.object(Path, "unlink", side_effect=permission_error(5)):
            with self.assertRaises(Slotted) as caught:
                runner.atomic_json(self.path, {"generation": "new"})
        self.assertEqual(caught.exception.winerror, 87)

    def test_attribute_fallback_attaches_the_cleanup_error_without_add_note(self):
        # Force the branch that an interpreter without BaseException.add_note
        # takes.  On 3.11+ the add_note branch is taken for every exception
        # type, so without this test the fallback would be dead code
        # everywhere the suite is green.
        def no_add_note_replace(*args, **kwargs):
            error = NoAddNote(87, "synthetic unrecoverable failure")
            error.winerror = 87
            raise error

        with patch.object(runner.os, "replace", side_effect=no_add_note_replace), \
             patch.object(Path, "unlink", side_effect=permission_error(5)):
            with self.assertRaises(NoAddNote) as caught:
                runner.atomic_json(self.path, {"generation": "new"})
        self.assertEqual(caught.exception.winerror, 87)
        attached = cleanup_error_of(caught.exception)
        self.assertIsNotNone(attached, "the cleanup error was lost")
        self.assertIsInstance(attached, OSError)
        self.assertEqual(attached.winerror, 5)

    def test_attribute_fallback_is_not_taken_when_add_note_exists(self):
        # The complementary check: on an interpreter that HAS add_note the
        # attribute fallback must not be used, so the cleanup error is a note
        # rather than an attribute.
        if not hasattr(BaseException(), "add_note"):
            self.skipTest("add_note is not available on this interpreter")
        with patch.object(runner.os, "replace", side_effect=permission_error(87)), \
             patch.object(Path, "unlink", side_effect=permission_error(5)):
            with self.assertRaises(PermissionError) as caught:
                runner.atomic_json(self.path, {"generation": "new"})
        self.assertTrue(any("cleanup failed" in note
                            for note in getattr(caught.exception, "__notes__", [])),
                        getattr(caught.exception, "__notes__", []))
        self.assertIsNone(getattr(caught.exception, "cleanup_error", None))


if __name__ == "__main__":
    unittest.main()
