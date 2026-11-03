"""The scheduled action must survive Windows native argv parsing unchanged."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest


@unittest.skipUnless(os.name == "nt" and shutil.which("powershell.exe"), "Windows PowerShell required")
class InstallerWindowsQuotingTests(unittest.TestCase):
    def test_workspace_roundtrip_through_native_windows_parser(self):
        paths = ["C:\\Users\\sample\\plain", "C:\\Users\\sample\\space path",
                 "C:\\", "C:\\space path\\", "\\\\server\\share\\"]
        script = r"""
$ErrorActionPreference='Stop'
$inputData=([Console]::In.ReadToEnd() | ConvertFrom-Json)
$tokens=$null; $parseErrors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile($inputData.installer,[ref]$tokens,[ref]$parseErrors)
if ($parseErrors.Count) {throw 'Installer syntax error'}
$node=$ast.Find({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Get-HostTaskWorkspaceArgument'},$true)
if ($null -eq $node) {throw 'Workspace helper missing'}
Invoke-Expression $node.Extent.Text
@($inputData.paths | ForEach-Object {Get-HostTaskWorkspaceArgument -Workspace $_}) | ConvertTo-Json -Compress
"""
        installer = Path(__file__).with_name("install-host-task.ps1")
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            input=json.dumps({"installer": str(installer), "paths": paths}),
            text=True, capture_output=True, check=True,
        )
        rendered = json.loads(result.stdout)
        self.assertEqual(len(rendered), len(paths))
        shell = ctypes.windll.shell32
        shell.CommandLineToArgvW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
        shell.CommandLineToArgvW.restype = ctypes.POINTER(wintypes.LPWSTR)
        ctypes.windll.kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        for expected, argument in zip(paths, rendered):
            with self.subTest(workspace=expected):
                count = ctypes.c_int()
                values = shell.CommandLineToArgvW("python.exe service.py " + argument, ctypes.byref(count))
                self.assertTrue(values)
                try:
                    actual = [values[index] for index in range(count.value)]
                finally:
                    ctypes.windll.kernel32.LocalFree(values)
                self.assertEqual(actual, ["python.exe", "service.py", "--workspace", expected])


if __name__ == "__main__":
    unittest.main()
