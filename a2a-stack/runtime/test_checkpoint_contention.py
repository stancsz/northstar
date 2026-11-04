"""Windows file-sharing contention regression for the atomic checkpoint writer.

The fixture holds real Windows file handles with explicit share modes and uses
real child processes, so it is Windows-only by construction.
"""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

NORTHSTAR_ROOT = Path(__file__).resolve().parents[2]
TEST_CONTROL = NORTHSTAR_ROOT / "tmp" / "a2a-stack" / "runtime-tests" / "control"
os.environ["A2A_TEST_CONTROL_DIR"] = str(TEST_CONTROL)
import runner

# The kernel32 binding is loaded lazily: a module-level WinDLL would fail at
# import time on a non-Windows host, which would make the skip guard below
# unreachable and turn the whole module into an import error instead of a
# skip.
K = None


def _kernel():
    global K
    if K is None:
        K = ctypes.WinDLL('kernel32', use_last_error=True)
        K.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        K.CreateFileW.restype = wintypes.HANDLE
        K.CloseHandle.argtypes = [wintypes.HANDLE]
        K.CloseHandle.restype = wintypes.BOOL
    return K


INVALID = ctypes.c_void_p(-1).value


def open_reader(path, share):
    k = _kernel()
    h = k.CreateFileW(str(path), 0x80000000, share, None, 3, 0x80, None)
    if h == INVALID:
        raise ctypes.WinError(ctypes.get_last_error())
    return h


def close_reader(handle):
    _kernel().CloseHandle(handle)


@unittest.skipUnless(os.name == 'nt', 'Windows file sharing fixture')
class CheckpointContention(unittest.TestCase):
    def setUp(self):
        base = Path(__file__).resolve().parents[2] / 'tmp' / 'a2a-stack' / 'checkpoint-fixtures'
        base.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=base)
        self.path = Path(self.tmp.name) / 'state.json'
        self.old = {'generation': 'old', 'payload': 'a' * 10000}
        self.new = {'generation': 'new', 'payload': 'b' * 10000}
        runner.atomic_json(self.path, self.old)

    def tearDown(self):
        self.tmp.cleanup()

    def test_reader_modes_block_and_release_recovers(self):
        # Include FILE_SHARE_DELETE (7) and the ordinary read-sharing case (1).
        for share in (1, 7):
            with self.subTest(share=share):
                runner.atomic_json(self.path, self.old)
                h = open_reader(self.path, share)
                try:
                    with self.assertRaises(PermissionError) as caught:
                        runner.atomic_json(self.path, self.new)
                    self.assertIn(caught.exception.winerror, (5, 32, 33))
                    self.assertEqual(json.loads(self.path.read_text()), self.old)
                    self.assertEqual(list(self.path.parent.glob('*.tmp')), [])
                finally:
                    close_reader(h)
                runner.atomic_json(self.path, self.new)
                self.assertEqual(json.loads(self.path.read_text()), self.new)

    def test_release_during_retry_recovers(self):
        h = open_reader(self.path, 1)
        timer = threading.Timer(.2, close_reader, args=(h,))
        timer.start()
        try:
            runner.atomic_json(self.path, self.new)
        finally:
            timer.join()
        self.assertEqual(json.loads(self.path.read_text()), self.new)
        self.assertEqual(list(self.path.parent.glob('*.tmp')), [])

    def test_concurrent_reader_sees_complete_snapshot(self):
        seen = []
        errors = []
        stop = threading.Event()
        def read():
            while not stop.is_set():
                try:
                    seen.append(json.loads(self.path.read_text()))
                except PermissionError as exc:
                    errors.append((exc.errno, exc.winerror))
                except (OSError, ValueError) as exc:
                    errors.append(repr(exc))
        t = threading.Thread(target=read)
        t.start()
        try:
            for i in range(30):
                runner.atomic_json(self.path, self.new if i % 2 else self.old)
        finally:
            stop.set()
            t.join()
        self.assertTrue(seen)
        self.assertTrue(all(x[0] == 13 and x[1] in (None, 5, 32, 33) for x in errors if isinstance(x, tuple)) and all(isinstance(x, tuple) for x in errors), errors[:3])
        self.assertTrue(all(x in (self.old, self.new) for x in seen))

    def test_journal_same_identity_can_persist_after_real_lock_release(self):
        import importlib.util
        module_path = Path(__file__).resolve().parents[1] / 'autonomy' / 'runner.py'
        spec = importlib.util.spec_from_file_location('isolated_goal_runner', module_path)
        autonomy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(autonomy)
        journal = autonomy.Journal(self.path.parent / 'goal', {'id': 'fixture-goal'})
        journal.record('session', session_id='fixture-session')
        state_path = journal.directory / 'state.json'
        saved = json.loads(state_path.read_text())
        handle = open_reader(state_path, 1)
        try:
            with self.assertRaises(autonomy.OwnedSnapshotUnavailable) as caught:
                journal.record('attempt', status='RECOVERING')
            self.assertIn(caught.exception.winerror, (5, 32, 33))
            self.assertEqual(json.loads(state_path.read_text()), saved)
            self.assertEqual(list(state_path.parent.glob('*.tmp')), [])
        finally:
            close_reader(handle)
        journal.record('recovered', status='RUNNING')
        recovered = json.loads(state_path.read_text())
        self.assertEqual(recovered['id'], 'fixture-goal')
        self.assertEqual(recovered['session_id'], 'fixture-session')
        self.assertEqual(recovered['status'], 'RUNNING')

    def test_temp_write_failure_preserves_old_and_cleans_temp(self):
        from unittest.mock import patch
        original = Path.write_text
        def partial_then_fail(path, data, **kwargs):
            if path.name.endswith('.tmp'):
                original(path, '{', encoding='utf-8')
                raise OSError('injected write failure')
            return original(path, data, **kwargs)
        with patch.object(Path, 'write_text', partial_then_fail):
            with self.assertRaisesRegex(OSError, 'injected write failure'):
                runner.atomic_json(self.path, self.new)
        self.assertEqual(json.loads(self.path.read_text()), self.old)
        residue = list(self.path.parent.glob('*.tmp'))
        self.assertEqual(residue, [])

    def test_process_death_after_replace_preserves_new_and_no_temp(self):
        code = "import os,sys; from pathlib import Path; import runner; original=runner.os.replace; exec('def replace_then_exit(*args):\\n original(*args)\\n os._exit(74)'); runner.os.replace=replace_then_exit; runner.atomic_json(Path(sys.argv[1]), {'generation':'new'})"
        child = subprocess.run([sys.executable, '-c', code, str(self.path)], cwd=Path(__file__).parent)
        self.assertEqual(child.returncode, 74)
        self.assertEqual(json.loads(self.path.read_text()), {'generation': 'new'})
        self.assertEqual(list(self.path.parent.glob('*.tmp')), [])

    def test_process_death_before_replace_preserves_old_but_leaves_temp(self):
        # Abrupt process death bypasses finally; document rather than hide the residue.
        code = "import os,sys; from pathlib import Path; import runner; runner.os.replace=lambda *a: os._exit(73); runner.atomic_json(Path(sys.argv[1]), {'generation':'new'})"
        child = subprocess.run([sys.executable, '-c', code, str(self.path)], cwd=Path(__file__).parent)
        self.assertEqual(child.returncode, 73)
        self.assertEqual(json.loads(self.path.read_text()), self.old)
        residue = list(self.path.parent.glob('*.tmp'))
        self.assertEqual(len(residue), 1)
        self.assertEqual(json.loads(residue[0].read_text()), {'generation': 'new'})
        runner.atomic_json(self.path, self.new)
        self.assertEqual(json.loads(self.path.read_text()), self.new)
        # Existing writer does not clean the prior process's temp file.
        self.assertTrue(residue[0].exists())

if __name__ == '__main__':
    unittest.main()
