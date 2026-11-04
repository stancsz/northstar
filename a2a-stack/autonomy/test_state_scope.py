import asyncio
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

STACK = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('state_scope_manager', STACK / 'autonomy/manager.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class StateScopeTests(unittest.TestCase):
    def test_root_rejected_before_unreadable_state_snapshot_and_goal_creation(self):
        with tempfile.TemporaryDirectory(dir=STACK) as temp:
            workspace = Path(temp) / 'workspace'
            state = workspace / 'tmp/a2a-stack'
            state.mkdir(parents=True)
            (state / 'active.lock').write_text('locked')
            manager = module.GoalManager(state, workspace)
            request = {'workspace': str(workspace), 'goal': 'test', 'acceptance': ['done'], 'write_paths': ['.']}
            with patch.object(module.candidate_scope, 'file_digest', side_effect=PermissionError('locked')) as digest:
                with self.assertRaisesRegex(ValueError, 'state.*overlap'):
                    asyncio.run(manager.create(request))
                digest.assert_not_called()
            self.assertFalse(manager.directory.exists())
    def test_overlap_partitions_and_safe_scope(self):
        with tempfile.TemporaryDirectory(dir=STACK) as temp:
            workspace = Path(temp) / 'workspace'
            state = workspace / 'tmp/a2a-stack'
            state.mkdir(parents=True)
            (workspace / 'src').mkdir()
            (workspace / 'src/code.py').write_text('source')
            manager = module.GoalManager(state, workspace)
            base = {'workspace': str(workspace), 'goal': 'test', 'acceptance': ['done']}
            for path in ('.', 'tmp', 'tmp/a2a-stack', 'tmp/a2a-stack/new/file'):
                with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'state.*overlap'):
                    asyncio.run(manager.create({**base, 'write_paths': [path]}))
            self.assertFalse(manager.directory.exists())
            with patch.object(module.GoalManager, '_launch'):
                result = asyncio.run(manager.create({**base, 'write_paths': ['src']}))
            self.assertEqual(set(manager._read(Path(result['spec_path']))['baseline']), {'src/code.py'})

    def test_external_state_keeps_root_scope_complete(self):
        with tempfile.TemporaryDirectory(dir=STACK) as temp:
            root = Path(temp)
            workspace = root / 'workspace'
            (workspace / '.git').mkdir(parents=True)
            (workspace / '.git/config').write_text('git')
            (workspace / 'source.py').write_text('source')
            manager = module.GoalManager(root / 'state', workspace)
            request = {'workspace': str(workspace), 'goal': 'test', 'acceptance': ['done'], 'write_paths': ['.']}
            with patch.object(module.GoalManager, '_launch'):
                result = asyncio.run(manager.create(request))
            self.assertEqual(set(manager._read(Path(result['spec_path']))['baseline']), {'.git/config', 'source.py'})

    def test_state_root_above_workspace_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=STACK) as temp:
            root = Path(temp)
            workspace = root / 'workspace'
            workspace.mkdir()
            manager = module.GoalManager(root, workspace)
            request = {'workspace': str(workspace), 'goal': 'test', 'acceptance': ['done'], 'write_paths': ['new.py']}
            with self.assertRaisesRegex(ValueError, 'state.*overlap'):
                asyncio.run(manager.create(request))
            self.assertFalse(manager.directory.exists())

    @unittest.skipUnless(__import__('os').name == 'nt', 'Windows lock fixture')
    def test_actual_locked_state_file_is_rejected_before_baseline(self):
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        create = kernel.CreateFileW
        create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        create.restype = wintypes.HANDLE
        close = kernel.CloseHandle
        close.argtypes = [wintypes.HANDLE]
        close.restype = wintypes.BOOL
        with tempfile.TemporaryDirectory(dir=STACK) as temp:
            workspace = Path(temp) / 'workspace'
            state = workspace / 'tmp/a2a-stack'
            state.mkdir(parents=True)
            lock = state / 'active.lock'
            lock.write_text('live state')
            handle = create(str(lock), 0x80000000, 0, None, 3, 0x80, None)
            self.assertNotEqual(handle, ctypes.c_void_p(-1).value, ctypes.get_last_error())
            try:
                with self.assertRaises(PermissionError):
                    module.candidate_scope.baseline_snapshot(workspace, ['.'])
                manager = module.GoalManager(state, workspace)
                request = {'workspace': str(workspace), 'goal': 'test', 'acceptance': ['done'], 'write_paths': ['.']}
                with self.assertRaisesRegex(ValueError, 'state.*overlap'):
                    asyncio.run(manager.create(request))
                self.assertFalse(manager.directory.exists())
            finally:
                close(handle)
