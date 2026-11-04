import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('launch', Path(__file__).with_name('launch.py'))
launch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launch)


class LauncherTest(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt', 'Windows taskkill semantics')
    def test_taskkill_failure_is_not_reported_as_successful_cleanup(self):
        class FakeProcess:
            pid = 12345
            killed = False
            def communicate(self, **kwargs): raise launch.subprocess.TimeoutExpired('codex', 1)
            def poll(self): return None
            def kill(self): self.killed = True
            def wait(self, timeout): return 1
        process = FakeProcess()
        with patch.object(launch.subprocess, 'Popen', return_value=process), \
             patch.object(launch.subprocess, 'run', return_value=type('Result', (), {'returncode': 1})()):
            with self.assertRaises(launch.ProcessTreeCleanupError):
                launch.run_worker(['codex'], input='', stdout=None, stderr=None, env={}, timeout=1)
        self.assertTrue(process.killed)

    def test_timeout_stops_real_child_process_tree(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            marker = root / 'orphan-marker.txt'
            child_code = 'import pathlib,time; time.sleep(3); pathlib.Path(%r).write_text("orphan")' % str(marker)
            parent_code = 'import subprocess,sys,time; subprocess.Popen([sys.executable,"-c",%r]); time.sleep(10)' % child_code
            with (root / 'stdout.log').open('w') as out, (root / 'stderr.log').open('w') as err:
                try:
                    with self.assertRaises(launch.subprocess.TimeoutExpired):
                        launch.run_worker([sys.executable, '-u', '-c', parent_code], input='', stdout=out, stderr=err,
                                          env=os.environ.copy(), timeout=1)
                finally:
                    # The synthetic child self-terminates after three seconds.
                    # Let it exit even if the sandbox rejects tree termination,
                    # preserving the actual failure instead of leaking it.
                    time.sleep(4)
            self.assertFalse(marker.exists(), 'A descendant kept running after timeout')

    def test_failed_file_change_is_not_accepted_even_if_turn_completes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            assignment = root / 'assignment.txt'; assignment.write_text('Edit.', encoding='utf-8')
            executable = root / 'codex.exe'; executable.touch()
            args = ['launch.py', '--workdir', str(root), '--assignment', str(assignment),
                    '--receipts', str(root / 'receipts'), '--model', 'test-model', '--codex-executable', str(executable)]
            def fake_run(command, **kwargs):
                for event in ({'type':'item.completed','item':{'type':'file_change','status':'failed'}},
                              {'type':'item.completed','item':{'type':'agent_message','text':'done'}},
                              {'type':'turn.completed'}):
                    kwargs['stdout'].write(json.dumps(event) + '\n')
                return type('Result', (), {'returncode': 0})()
            with patch.dict(os.environ, {'OPENROUTER_API_KEY':'synthetic-test-key'}), patch.object(launch.sys, 'argv', args), \
                 patch.object(launch, 'run_worker', fake_run), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(launch.main(), 1)

    def test_warning_item_and_terminal_failure_are_distinguished(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            assignment = root / 'assignment.txt'; assignment.write_text('Inspect.', encoding='utf-8')
            executable = root / 'codex.exe'; executable.touch()
            args = ['launch.py', '--workdir', str(root), '--assignment', str(assignment),
                    '--receipts', str(root / 'receipts'), '--model', 'test-model', '--codex-executable', str(executable)]
            cases = [({'type': 'item.completed', 'item': {'type': 'error', 'message': 'Skill descriptions were shortened'}}, 0),
                     ({'type': 'error', 'message': 'Reconnecting... 1/5 (temporary failure)'}, 0),
                     ({'type': 'error', 'message': 'provider error'}, 1),
                     ({'type': 'turn.failed'}, 1)]
            for event, expected in cases:
                def fake_run(command, **kwargs):
                    for entry in (event, {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'done'}},
                                  {'type': 'turn.completed'}):
                        kwargs['stdout'].write(json.dumps(entry) + '\n')
                    return type('Result', (), {'returncode': 0})()
                with self.subTest(event=event['type']), \
                     patch.dict(os.environ, {'OPENROUTER_API_KEY': 'synthetic-test-key'}), \
                     patch.object(launch.sys, 'argv', args), patch.object(launch, 'run_worker', fake_run), \
                     contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(launch.main(), expected)

    def test_timeout_returns_failed_receipt(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            assignment = root / 'assignment.txt'; assignment.write_text('Inspect.', encoding='utf-8')
            executable = root / 'codex.exe'; executable.touch()
            args = ['launch.py', '--workdir', str(root), '--assignment', str(assignment),
                    '--receipts', str(root / 'receipts'), '--model', 'test-model', '--codex-executable', str(executable)]
            with patch.dict(os.environ, {'OPENROUTER_API_KEY':'synthetic-test-key'}), patch.object(launch.sys, 'argv', args), \
                 patch.object(launch, 'run_worker', side_effect=launch.subprocess.TimeoutExpired('codex', 600)), \
                 contextlib.redirect_stdout(io.StringIO()) as printed:
                self.assertEqual(launch.main(), 1)
                self.assertEqual(json.loads(printed.getvalue())['error'], 'timeout')

    def test_child_configuration_and_receipts_are_isolated(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            assignment = root / 'assignment.txt'
            assignment.write_text('Read the fixture.', encoding='utf-8')
            executable = root / 'codex.exe'
            executable.touch()
            original_home = os.environ.get('CODEX_HOME')
            calls = []

            def fake_run(command, **kwargs):
                calls.append(command)
                env = kwargs['env']
                self.assertNotEqual(env['CODEX_HOME'], original_home)
                self.assertEqual(env['OPENROUTER_API_KEY'], 'synthetic-test-key')
                config = Path(env['CODEX_HOME'], 'config.toml').read_text(encoding='utf-8')
                self.assertIn('https://openrouter.ai/api/v1', config)
                self.assertIn('env_key = "OPENROUTER_API_KEY"', config)
                if os.name == 'nt':
                    self.assertIn('[windows]\nsandbox = "elevated"', config)
                self.assertNotIn('synthetic-test-key', config)
                self.assertEqual(kwargs['input'], 'Read the fixture.')
                self.assertIsNone(kwargs['timeout'], 'The worker must not be killed by a fixed default deadline')
                kwargs['stdout'].write(json.dumps({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'done'}}) + '\n')
                kwargs['stdout'].write(json.dumps({'type': 'turn.completed'}) + '\n')
                return type('Result', (), {'returncode': 0})()

            args = ['launch.py', '--workdir', str(root), '--assignment', str(assignment),
                    '--receipts', str(root / 'receipts'), '--model', 'test-model',
                    '--codex-executable', str(executable), '--disable-plugins']
            with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'synthetic-test-key'}), \
                 patch.object(launch.sys, 'argv', args), \
                 patch.object(launch, 'run_worker', fake_run), \
                 contextlib.redirect_stdout(io.StringIO()) as printed:
                self.assertEqual(launch.main(), 0)
            self.assertEqual(os.environ.get('CODEX_HOME'), original_home)
            self.assertEqual(len(calls), 1)
            self.assertIn('test-model', calls[0])
            self.assertIn('features.plugins=false', calls[0])
            self.assertIn('shell_environment_policy.exclude=["OPENROUTER_API_KEY"]', calls[0])
            self.assertIn('model_providers.openrouter.request_max_retries=4', calls[0])
            self.assertIn('model_providers.openrouter.stream_max_retries=5', calls[0])
            self.assertNotIn('synthetic-test-key', printed.getvalue())
            self.assertNotIn('synthetic-test-key', (root / 'receipts').joinpath(
                next((root / 'receipts').glob('*.jsonl')).name).read_text())

    def test_missing_key_fails_before_process_launch(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(launch.sys, 'argv', ['launch.py', '--workdir', '.', '--assignment', 'x',
                                              '--receipts', 'x', '--model', 'x', '--codex-executable', 'x']), \
             patch.object(launch, 'run_worker') as run, \
             contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                launch.main()
            run.assert_not_called()

    def test_default_model_is_minimax(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            assignment = root / 'assignment.txt'; assignment.write_text('Inspect.', encoding='utf-8')
            executable = root / 'codex.exe'; executable.touch()
            args = ['launch.py', '--workdir', str(root), '--assignment', str(assignment),
                    '--receipts', str(root / 'receipts'), '--codex-executable', str(executable)]
            def fake_run(command, **kwargs):
                self.assertIn('minimax/minimax-m3.1-flash', command)
                kwargs['stdout'].write('{"type":"item.completed","item":{"type":"agent_message","text":"done"}}\n')
                kwargs['stdout'].write('{"type":"turn.completed"}\n')
                return type('Result', (), {'returncode': 0})()
            with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'synthetic-test-key'}), \
                 patch.object(launch.sys, 'argv', args), patch.object(launch, 'run_worker', fake_run), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(launch.main(), 0)

    def test_nonzero_exit_or_missing_completion_is_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            assignment = root / 'assignment.txt'
            assignment.write_text('Inspect.', encoding='utf-8')
            executable = root / 'codex.exe'
            executable.touch()
            args = ['launch.py', '--workdir', str(root), '--assignment', str(assignment),
                    '--receipts', str(root / 'receipts'), '--model', 'test-model',
                    '--codex-executable', str(executable)]
            for returncode, completed in ((1, True), (0, False)):
                def fake_run(command, **kwargs):
                    if completed:
                        kwargs['stdout'].write('{"type":"turn.completed"}\n')
                    return type('Result', (), {'returncode': returncode})()

                with self.subTest(returncode=returncode, completed=completed), \
                     patch.dict(os.environ, {'OPENROUTER_API_KEY': 'synthetic-test-key'}), \
                     patch.object(launch.sys, 'argv', args), \
                     patch.object(launch, 'run_worker', fake_run), \
                     contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(launch.main(), 1)


if __name__ == '__main__':
    unittest.main()
