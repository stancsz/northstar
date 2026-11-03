"""Focused tests for durable host workspace selection and state isolation.

These are pure tests: nothing here launches the A2A server, binds a port,
registers or touches a Scheduled Task, or interrupts the running host service.
The service module is loaded in-process with its side effects stubbed, and the
installer's pure decision helpers are extracted from the real script and run
under PowerShell without touching ScheduledTasks.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

AGENT_DIR = Path(__file__).resolve().parent
STACK_ROOT = AGENT_DIR.parent
REPO_ROOT = STACK_ROOT.parent
SERVICE_PATH = AGENT_DIR / "service.py"
INSTALLER_PATH = AGENT_DIR / "install-host-task.ps1"

POWERSHELL = shutil.which("powershell.exe") or shutil.which("powershell")

INSTALLER_HELPERS = (
    "Get-HostTaskArguments",
    "Get-HostTaskWorkspaceArgument",
    "Split-HostTaskArguments",
    "Compare-HostTaskAction",
)

HARNESS_TEMPLATE = r"""
$ErrorActionPreference = 'Stop'
$installerPath = '__INSTALLER__'
$source = Get-Content -LiteralPath $installerPath -Raw
$tokens = $null
$parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseInput(
    $source, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors -and $parseErrors.Count -gt 0) { throw ($parseErrors | Out-String) }
$definitions = @($ast.FindAll({
    param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst]
}, $true))
foreach ($name in @('__HELPERS__')) {
    $found = @($definitions | Where-Object { $_.Name -eq $name })
    if ($found.Count -ne 1) { throw "helper function not found exactly once: $name" }
    Invoke-Expression $found[0].Extent.Text
}

__BODY__
"""

INSTALLER_PROBE_BODY = r"""
$service = 'D:\github\northstar\a2a-stack\agent\service.py'
$execute = 'C:\host\pythonw.exe'
$workdir = 'D:\github\northstar'
$workspace = 'C:\authorized workspace'
$defaultArguments = Get-HostTaskArguments -ServicePath $service -Workspace ''
$workspaceArguments = Get-HostTaskArguments -ServicePath $service -Workspace $workspace
$splitDefault = Split-HostTaskArguments -Arguments $defaultArguments
$splitWorkspace = Split-HostTaskArguments -Arguments $workspaceArguments

$compare = {
    param($expected, $existing, $exec, $dir, $owner)
    Compare-HostTaskAction -ExpectedArguments $expected -ExistingArguments $existing `
        -ExpectedExecute $execute -ExistingExecute $exec `
        -ExpectedWorkingDirectory $workdir -ExistingWorkingDirectory $dir `
        -SameOwner $owner
}

$quoteRejected = ''
try {
    $null = Get-HostTaskArguments -ServicePath $service -Workspace ('bad"path')
}
catch {
    $quoteRejected = $_.Exception.Message
}

[ordered]@{
    defaultArguments   = $defaultArguments
    workspaceArguments = $workspaceArguments
    splitDefaultBase   = $splitDefault.BaseArguments
    splitDefaultWs     = $splitDefault.Workspace
    splitWorkspaceBase = $splitWorkspace.BaseArguments
    splitWorkspaceWs   = $splitWorkspace.Workspace
    splitGarbage       = $null -eq (Split-HostTaskArguments -Arguments 'not-an-action')
    splitEmpty         = $null -eq (Split-HostTaskArguments -Arguments '')
    splitPlain         = (Split-HostTaskArguments -Arguments ('"{0}" --workspace C:\plain' -f $service)).Workspace
    matchSame          = & $compare $defaultArguments $defaultArguments $execute $workdir $true
    matchSameWorkspace = & $compare $workspaceArguments $workspaceArguments $execute $workdir $true
    workspaceUpdate    = & $compare $workspaceArguments $defaultArguments $execute $workdir $true
    workspaceRevert    = & $compare $defaultArguments $workspaceArguments $execute $workdir $true
    refuseExecute      = & $compare $defaultArguments $defaultArguments 'C:\other\pythonw.exe' $workdir $true
    refuseWorkdir      = & $compare $defaultArguments $defaultArguments $execute 'D:\other' $true
    refuseOwner        = & $compare $defaultArguments $defaultArguments $execute $workdir $false
    refuseBase         = & $compare ('"{0}"' -f 'C:\other\service.py') $defaultArguments $execute $workdir $true
    refuseGarbage      = & $compare $defaultArguments 'garbage arguments' $execute $workdir $true
    quoteRejected      = $quoteRejected
} | ConvertTo-Json -Depth 5
"""

# The installer body is exercised with the ScheduledTasks cmdlets replaced by
# stubs, so the real script runs end to end without registering, starting,
# stopping or disabling any task.
INSTALLER_SCRIPT_HARNESS = r"""
$ErrorActionPreference = 'Stop'
$installer = $args[0]
$inputPath = $args[1]
$inputData = Get-Content -LiteralPath $inputPath -Raw | ConvertFrom-Json
$currentName = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$global:stubCalls = New-Object System.Collections.ArrayList
$global:stubRegistered = $null
$global:stubGetCount = 0

function Get-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName)
    $global:stubGetCount++
    $null = $global:stubCalls.Add('Get-ScheduledTask')
    if ($global:stubGetCount -eq 1) {
        if ($null -eq $inputData.existing) { return $null }
        $action = [pscustomobject]@{
            Execute          = $inputData.existing.execute
            Arguments        = $inputData.existing.arguments
            WorkingDirectory = $inputData.existing.workingDirectory
        }
        $userId = $currentName
        if ($inputData.existing.owner) { $userId = $inputData.existing.owner }
        return [pscustomobject]@{
            TaskName  = $TaskName
            State     = 'Ready'
            Principal = [pscustomobject]@{ UserId = $userId }
            Actions   = @($action)
        }
    }
    return [pscustomobject]@{
        TaskName  = $TaskName
        State     = 'Ready'
        Principal = [pscustomobject]@{ UserId = $currentName }
        Actions   = @()
    }
}

function Register-ScheduledTask {
    [CmdletBinding()]
    param(
        [string]$TaskName,
        $Action,
        $Trigger,
        $Principal,
        $Settings,
        [string]$Description,
        [switch]$Force
    )
    $null = $global:stubCalls.Add('Register-ScheduledTask')
    $global:stubRegistered = [pscustomobject]@{
        TaskName          = $TaskName
        Execute           = $Action.Execute
        Arguments         = $Action.Arguments
        WorkingDirectory  = $Action.WorkingDirectory
    }
}

function New-ScheduledTaskAction {
    [CmdletBinding()]
    param([string]$Execute, [string]$Argument, [string]$WorkingDirectory)
    [pscustomobject]@{
        Execute          = $Execute
        Arguments        = $Argument
        WorkingDirectory = $WorkingDirectory
    }
}

function New-ScheduledTaskTrigger {
    [CmdletBinding()]
    param(
        [string]$User,
        [datetime]$At,
        [timespan]$RepetitionInterval,
        [switch]$AtLogOn,
        [switch]$Once
    )
    [pscustomobject]@{ User = $User; At = $At }
}

function New-ScheduledTaskPrincipal {
    [CmdletBinding()]
    param([string]$UserId, [string]$LogonType, [string]$RunLevel)
    [pscustomobject]@{ UserId = $UserId; LogonType = $LogonType; RunLevel = $RunLevel }
}

function New-ScheduledTaskSettingsSet {
    [CmdletBinding()]
    param(
        [switch]$Hidden,
        [switch]$AllowStartIfOnBatteries,
        [switch]$DontStopIfGoingOnBatteries,
        [switch]$StartWhenAvailable,
        [string]$MultipleInstances,
        [timespan]$ExecutionTimeLimit
    )
    [pscustomobject]@{
        Hidden             = [bool]$Hidden
        MultipleInstances  = $MultipleInstances
        ExecutionTimeLimit = $ExecutionTimeLimit
    }
}

function Start-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName)
    $null = $global:stubCalls.Add('Start-ScheduledTask')
}

function Stop-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName)
    $null = $global:stubCalls.Add('Stop-ScheduledTask')
}

function Disable-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName)
    $null = $global:stubCalls.Add('Disable-ScheduledTask')
}

$errorText = ''
try {
    if ($inputData.start) {
        $null = & $installer -Workspace $inputData.workspace -Start
    }
    else {
        $null = & $installer -Workspace $inputData.workspace
    }
}
catch {
    $errorText = $_.Exception.Message
}

$registered = $null -ne $global:stubRegistered
[ordered]@{
    calls                   = @($global:stubCalls | ForEach-Object { $_ })
    registered              = $registered
    registeredArguments     = if ($registered) { $global:stubRegistered.Arguments } else { '' }
    registeredExecute       = if ($registered) { $global:stubRegistered.Execute } else { '' }
    registeredWorkingDir    = if ($registered) { $global:stubRegistered.WorkingDirectory } else { '' }
    error                   = $errorText
} | ConvertTo-Json -Depth 5
"""


def _load_service_module() -> types.ModuleType:
    """Load a fresh copy of the service module (it holds mutable global state)."""
    spec = importlib.util.spec_from_file_location("host_workspace_service", SERVICE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _escaped_ps(text: str) -> str:
    return text.replace("'", "''")


def _discard_namespace(state_root: Path) -> None:
    """Drop the throwaway namespace a probe created.

    Only namespaces under the shared state's ``workspaces`` directory are
    removed, and only when they hold no files, so the real Northstar state
    tree is never touched.
    """
    namespace_root = (REPO_ROOT / "tmp" / "a2a-stack" / "workspaces").resolve()
    try:
        resolved = Path(state_root).resolve()
    except OSError:
        return
    if resolved.parent != namespace_root:
        return
    if any(item.is_file() for item in resolved.rglob("*")):
        return
    shutil.rmtree(resolved, ignore_errors=True)


class ServiceWorkspaceResolutionTests(unittest.TestCase):
    """--workspace / A2A_WORKSPACE / default precedence at service startup."""

    def _run_main(self, args: list[str], env_workspace: str | None = None):
        """Run service.main() with stubbed lock, app builder and uvicorn."""
        module = _load_service_module()
        calls: list[str] = []
        observed: dict[str, object] = {}

        class Lock:
            def __init__(self, *a):
                calls.append("lock-init")

            def acquire(self):
                calls.append("lock")

            def release(self):
                pass

        def build():
            observed["workspace"] = Path(module.REPO_ROOT).resolve()
            calls.append("build")
            return object(), object()

        module.OwnerLock = Lock
        module.build_app = build

        env = {k: v for k, v in os.environ.items() if k != "A2A_WORKSPACE"}
        if env_workspace is not None:
            env["A2A_WORKSPACE"] = str(env_workspace)
        fake_uvicorn = types.SimpleNamespace(run=lambda *a, **k: calls.append("serve"))

        error: BaseException | None = None
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch.dict(sys.modules, {"uvicorn": fake_uvicorn}):
                with mock.patch.object(sys, "argv", [str(SERVICE_PATH), *args]):
                    try:
                        module.main()
                    except BaseException as exc:  # noqa: BLE001 - recorded for assertions
                        error = exc
        # The namespace is only known after main() selected it.
        self.addCleanup(_discard_namespace, Path(module.STATE_ROOT))
        return calls, observed, error, module

    def test_default_workspace_is_the_repository_root(self) -> None:
        calls, observed, error, _module = self._run_main([])
        self.assertIsNone(error)
        self.assertEqual(observed["workspace"], REPO_ROOT.resolve())
        self.assertEqual(calls, ["lock-init", "lock", "build", "serve"])

    def test_env_fallback_selects_the_workspace(self) -> None:
        with tempfile.TemporaryDirectory(prefix="env workspace ") as workspace:
            calls, observed, error, _module = self._run_main([], env_workspace=workspace)
            self.assertIsNone(error)
            self.assertEqual(observed["workspace"], Path(workspace).resolve())
            self.assertEqual(calls, ["lock-init", "lock", "build", "serve"])

    def test_explicit_option_wins_over_environment(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cli workspace ") as chosen:
            with tempfile.TemporaryDirectory(prefix="env workspace ") as ignored:
                calls, observed, error, _module = self._run_main(
                    ["--workspace", chosen], env_workspace=ignored
                )
                self.assertIsNone(error)
                self.assertEqual(observed["workspace"], Path(chosen).resolve())
                self.assertEqual(calls, ["lock-init", "lock", "build", "serve"])

    def test_workspace_path_with_spaces_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory(prefix="authorized workspace ") as workspace:
            calls, observed, error, _module = self._run_main(["--workspace", workspace])
            self.assertIsNone(error)
            self.assertEqual(observed["workspace"], Path(workspace).resolve())
            self.assertEqual(calls, ["lock-init", "lock", "build", "serve"])

    def test_missing_workspace_fails_before_lock_and_build(self) -> None:
        with tempfile.TemporaryDirectory(prefix="authorized workspace ") as workspace:
            missing = str(Path(workspace) / "missing")
            calls, _observed, error, _module = self._run_main(["--workspace", missing])
            self.assertIsNotNone(error)
            self.assertIsInstance(error, (SystemExit, ValueError))
            self.assertEqual(calls, [])

    def test_file_workspace_fails_before_lock_and_build(self) -> None:
        with tempfile.TemporaryDirectory(prefix="authorized workspace ") as workspace:
            target = Path(workspace) / "not-a-directory.txt"
            target.write_text("not a directory", encoding="utf-8")
            calls, _observed, error, _module = self._run_main(["--workspace", str(target)])
            self.assertIsNotNone(error)
            self.assertIsInstance(error, (SystemExit, ValueError))
            self.assertEqual(calls, [])

    def test_invalid_workspace_does_not_create_the_directory(self) -> None:
        with tempfile.TemporaryDirectory(prefix="authorized workspace ") as workspace:
            missing = Path(workspace) / "missing"
            _calls, _observed, error, _module = self._run_main(["--workspace", str(missing)])
            self.assertIsNotNone(error)
            self.assertFalse(missing.exists())


class WorkspaceStateIsolationTests(unittest.TestCase):
    """Each authorized workspace owns one durable state namespace.

    These tests never start the host service.  The service module is loaded
    in-process with its owner lock, app builder and uvicorn runner stubbed, so
    only the workspace-selection and state-namespace logic is exercised.
    """

    def _probe(self, workspace: Path | None) -> dict[str, Path]:
        """Run service.main() and report the selected module-level paths."""
        module = _load_service_module()
        seen: dict[str, Path] = {}

        class Lock:
            def __init__(self, *a):
                pass

            def acquire(self):
                pass

            def release(self):
                pass

        def build():
            for key in ("REPO_ROOT", "STATE_ROOT", "JOBS_DIR", "TASKS_DIR", "LOCK_PATH"):
                seen[key] = Path(getattr(module, key)).resolve()
            return object(), object()

        module.OwnerLock = Lock
        module.build_app = build

        env = {k: v for k, v in os.environ.items() if k != "A2A_WORKSPACE"}
        fake_uvicorn = types.SimpleNamespace(run=lambda *a, **k: None)
        argv = [str(SERVICE_PATH)]
        if workspace is not None:
            argv += ["--workspace", str(workspace)]

        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch.dict(sys.modules, {"uvicorn": fake_uvicorn}):
                with mock.patch.object(sys, "argv", argv):
                    module.main()
        self.addCleanup(_discard_namespace, seen["STATE_ROOT"])
        return seen

    def test_default_workspace_keeps_the_original_state_tree(self) -> None:
        seen = self._probe(None)
        self.assertEqual(seen["REPO_ROOT"], REPO_ROOT.resolve())
        self.assertEqual(seen["STATE_ROOT"], REPO_ROOT / "tmp" / "a2a-stack")
        self.assertEqual(seen["JOBS_DIR"], seen["STATE_ROOT"] / "jobs")
        self.assertEqual(seen["TASKS_DIR"], seen["STATE_ROOT"] / "tasks")

    def test_non_default_workspace_gets_its_own_namespace(self) -> None:
        with tempfile.TemporaryDirectory(prefix="isolated workspace ") as workspace:
            seen = self._probe(Path(workspace))
            self.assertEqual(seen["REPO_ROOT"], Path(workspace).resolve())
            self.assertNotEqual(seen["STATE_ROOT"], REPO_ROOT / "tmp" / "a2a-stack")
            self.assertTrue(
                seen["STATE_ROOT"].is_relative_to(REPO_ROOT / "tmp" / "a2a-stack"),
                f"namespace {seen['STATE_ROOT']} escaped the shared state tree",
            )
            self.assertEqual(seen["JOBS_DIR"], seen["STATE_ROOT"] / "jobs")
            self.assertEqual(seen["TASKS_DIR"], seen["STATE_ROOT"] / "tasks")

    def test_namespace_is_stable_across_path_spelling_aliases(self) -> None:
        with tempfile.TemporaryDirectory(prefix="isolated workspace ") as workspace:
            target = Path(workspace)
            canonical = self._probe(target)["STATE_ROOT"]
            aliases = [
                target / ".",
                target / ".." / target.name,
                Path(str(target) + "/"),
            ]
            if os.name == "nt" and target.drive:
                aliases.append(Path(target.drive.lower() + str(target)[2:]))
            for alias in aliases:
                with self.subTest(alias=str(alias)):
                    self.assertEqual(self._probe(alias)["STATE_ROOT"], canonical)

    def test_owner_lock_is_one_shared_lock_for_every_workspace(self) -> None:
        default = self._probe(None)
        with tempfile.TemporaryDirectory(prefix="isolated workspace ") as workspace:
            alternate = self._probe(Path(workspace))
        self.assertEqual(default["LOCK_PATH"], alternate["LOCK_PATH"])
        self.assertEqual(default["LOCK_PATH"], REPO_ROOT / "tmp" / "a2a-stack" / "control" / "owner.lock")
        self.assertNotEqual(alternate["STATE_ROOT"], alternate["LOCK_PATH"].parent)

    def test_namespace_owns_its_stacks_and_goals(self) -> None:
        """One namespace cannot see the other namespace's persisted stacks."""
        with tempfile.TemporaryDirectory(prefix="isolated workspace ") as workspace:
            other_workspace = Path(workspace).resolve()
            alternate = self._probe(other_workspace)
            default = self._probe(None)

            sys.path.insert(0, str(AGENT_DIR))
            from stacks import StackManager

            # Both namespaces are exercised against throwaway state roots, so
            # the real Northstar state tree is never read, written or migrated.
            with tempfile.TemporaryDirectory() as default_root, tempfile.TemporaryDirectory() as other_root:
                default_root_path = Path(default_root).resolve()
                other_root_path = Path(other_root).resolve()
                default_manager = StackManager(default_root_path, REPO_ROOT.resolve(), lambda *a: None)
                other_manager = StackManager(other_root_path, other_workspace, lambda *a: None)

                default_manager.create_stack({"workspace": str(REPO_ROOT.resolve()), "goal": "northstar goal",
                                              "template_name": "code-review", "name": "northstar"})

                self.assertEqual(len(default_manager.list_stacks()), 1)
                self.assertEqual(other_manager.list_stacks(), [])
                self.assertNotEqual(default_manager.stacks_dir, other_manager.stacks_dir)

                # The persisted-workspace check in stacks.py is not bypassed: a
                # stack recorded for another workspace is still refused, so
                # isolation cannot be faked by copying state across namespaces.
                foreign = other_root_path / "stacks" / "s-foreign" / "stack.json"
                foreign.parent.mkdir(parents=True, exist_ok=True)
                foreign.write_text(json.dumps({
                    "stack_id": "s-foreign", "name": "foreign", "template_name": None,
                    "workspace": str(REPO_ROOT.resolve()), "goal": "foreign goal",
                    "roles": [{"id": "coder", "profile": "coder"}],
                    "created_at": "2026-01-01T00:00:00+00:00", "goal_id": None,
                }), encoding="utf-8")
                with self.assertRaises(ValueError):
                    other_manager.list_stacks()

        self.assertNotEqual(default["STATE_ROOT"], alternate["STATE_ROOT"])

    def test_task_store_and_job_task_dirs_follow_the_selected_state_root(self) -> None:
        """The per-agent task store is rooted in the selected namespace."""
        sys.path.insert(0, str(AGENT_DIR))
        from task_store import create_task_store

        with tempfile.TemporaryDirectory(prefix="isolated workspace ") as workspace:
            seen = self._probe(Path(workspace))
            selected = seen["STATE_ROOT"]
            self.assertEqual(seen["JOBS_DIR"], selected / "jobs")
            self.assertEqual(seen["TASKS_DIR"], selected / "tasks")

            # The store is built against the selected state root, so its
            # protocol database and its task receipts land in that namespace.
            store = create_task_store(selected, "probe-key")

            async def close_store() -> None:
                await store.close()

            try:
                engine_path = Path(store.engine.url.database)
                self.assertEqual(engine_path.parent, selected / "protocol")
                self.assertEqual(store.state_root, selected)
                self.assertEqual(store._task_dir("task-1"), selected / "tasks" / "task-1")
                self.assertTrue(engine_path.is_relative_to(selected))
            finally:
                asyncio.run(close_store())


class InstallerScriptTests(unittest.TestCase):
    """Static, side-effect-free checks of the Scheduled Task installer."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.source = INSTALLER_PATH.read_text(encoding="utf-8")

    def test_declares_workspace_parameter(self) -> None:
        self.assertIn("[string]$Workspace", self.source)
        self.assertIn("-Workspace", self.source)

    def test_workspace_argument_is_quoted(self) -> None:
        self.assertIn('--workspace "{0}"', self.source)

    def test_default_arguments_stay_the_service_path_only(self) -> None:
        self.assertIn("Get-HostTaskArguments -ServicePath $servicePath -Workspace $workspacePath", self.source)
        self.assertIn("$base = '\"{0}\"' -f $ServicePath", self.source)

    def test_task_settings_remain_uncapped_and_per_user(self) -> None:
        self.assertIn("-MultipleInstances IgnoreNew", self.source)
        self.assertIn("-ExecutionTimeLimit ([TimeSpan]::Zero)", self.source)
        self.assertIn("-LogonType Interactive", self.source)
        self.assertIn("-RunLevel Limited", self.source)
        self.assertIn("-Hidden", self.source)
        self.assertIn("-AllowStartIfOnBatteries", self.source)
        self.assertIn("-DontStopIfGoingOnBatteries", self.source)

    def test_owner_and_action_refusal_is_preserved(self) -> None:
        self.assertIn(
            "Refusing to replace task '$taskName': its owner or action differs from this installer.",
            self.source,
        )
        self.assertIn("Refusing to replace task '$taskName': its owner cannot be resolved to a SID.", self.source)
        self.assertIn("$sameOwner", self.source)
        self.assertIn("Compare-HostTaskAction", self.source)

    def test_workspace_must_exist_and_is_not_created(self) -> None:
        self.assertIn("Workspace directory does not exist: $Workspace", self.source)
        self.assertIn("Test-Path -LiteralPath $Workspace -PathType Container", self.source)
        self.assertNotIn("New-Item", self.source)
        self.assertNotIn("mkdir", self.source)


@unittest.skipIf(POWERSHELL is None, "powershell.exe is unavailable on this machine")
class InstallerHelperTests(unittest.TestCase):
    """Runs the installer's pure helper functions, extracted from the script."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.results = cls._run_probe()

    @classmethod
    def _run_probe(cls) -> dict:
        script = (
            HARNESS_TEMPLATE
            .replace("__INSTALLER__", _escaped_ps(str(INSTALLER_PATH)))
            .replace("__HELPERS__", "', '".join(INSTALLER_HELPERS))
            .replace("__BODY__", INSTALLER_PROBE_BODY)
        )
        with tempfile.TemporaryDirectory(prefix="host workspace probe ") as directory:
            path = Path(directory) / "probe.ps1"
            path.write_text(script, encoding="utf-8")
            completed = subprocess.run(
                [POWERSHELL, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                 "-File", str(path)],
                capture_output=True,
                text=True,
            )
        if completed.returncode != 0:
            raise AssertionError(
                "installer helper probe failed:\n"
                f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
            )
        return json.loads(completed.stdout)

    def test_default_arguments_are_the_service_path_only(self) -> None:
        self.assertEqual(
            self.results["defaultArguments"],
            '"D:\\github\\northstar\\a2a-stack\\agent\\service.py"',
        )
        self.assertNotIn("--workspace", self.results["defaultArguments"])

    def test_workspace_arguments_are_quoted_as_one_argument(self) -> None:
        self.assertEqual(
            self.results["workspaceArguments"],
            '"D:\\github\\northstar\\a2a-stack\\agent\\service.py" --workspace "C:\\authorized workspace"',
        )

    def test_split_separates_base_service_argument_from_workspace(self) -> None:
        self.assertEqual(
            self.results["splitDefaultBase"],
            '"D:\\github\\northstar\\a2a-stack\\agent\\service.py"',
        )
        self.assertEqual(self.results["splitDefaultWs"], "")
        self.assertEqual(
            self.results["splitWorkspaceBase"],
            '"D:\\github\\northstar\\a2a-stack\\agent\\service.py"',
        )
        self.assertEqual(self.results["splitWorkspaceWs"], "C:\\authorized workspace")

    def test_unparsable_arguments_are_not_treated_as_base_form(self) -> None:
        self.assertTrue(self.results["splitGarbage"])
        self.assertTrue(self.results["splitEmpty"])
        self.assertEqual(self.results["splitPlain"], "C:\\plain")

    def test_identical_action_is_a_match(self) -> None:
        self.assertEqual(self.results["matchSame"], "match")
        self.assertEqual(self.results["matchSameWorkspace"], "match")

    def test_workspace_only_difference_is_allowed_in_both_directions(self) -> None:
        self.assertEqual(self.results["workspaceUpdate"], "workspace-update")
        self.assertEqual(self.results["workspaceRevert"], "workspace-update")

    def test_unrelated_action_differences_are_refused(self) -> None:
        self.assertEqual(self.results["refuseExecute"], "refuse")
        self.assertEqual(self.results["refuseWorkdir"], "refuse")
        self.assertEqual(self.results["refuseOwner"], "refuse")
        self.assertEqual(self.results["refuseBase"], "refuse")
        self.assertEqual(self.results["refuseGarbage"], "refuse")

    def test_double_quote_in_workspace_path_is_rejected(self) -> None:
        self.assertIn("double-quote", self.results["quoteRejected"])


@unittest.skipIf(POWERSHELL is None, "powershell.exe is unavailable on this machine")
class InstallerBodyTests(unittest.TestCase):
    """Runs the whole installer script with the ScheduledTasks cmdlets stubbed.

    The real script body executes (argument building, ownership check, action
    comparison, registration call) but every task cmdlet is replaced, so no
    task is registered, started, stopped or disabled and the live host is
    never touched.
    """

    def _run_installer(self, workspace: str, existing: dict | None, start: bool = False) -> dict:
        payload = {"workspace": workspace, "existing": existing, "start": start}
        with tempfile.TemporaryDirectory(prefix="host workspace installer ") as directory:
            base = Path(directory)
            input_path = base / "input.json"
            input_path.write_text(json.dumps(payload), encoding="utf-8")
            script_path = base / "harness.ps1"
            script_path.write_text(INSTALLER_SCRIPT_HARNESS, encoding="utf-8")
            completed = subprocess.run(
                [POWERSHELL, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                 "-File", str(script_path), str(INSTALLER_PATH), str(input_path)],
                capture_output=True,
                text=True,
            )
        if completed.returncode != 0:
            raise AssertionError(
                "installer body run failed:\n"
                f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
            )
        return json.loads(completed.stdout)

    def _existing(self, arguments: str) -> dict:
        return {
            "execute": str(REPO_ROOT / "tmp" / "a2a-stack" / "venv" / "Scripts" / "pythonw.exe"),
            "arguments": arguments,
            "workingDirectory": str(REPO_ROOT),
            "owner": None,
        }

    def test_default_run_registers_the_original_arguments(self) -> None:
        result = self._run_installer("", None)
        self.assertEqual(result["error"], "")
        self.assertTrue(result["registered"])
        self.assertEqual(
            result["registeredArguments"],
            '"D:\\github\\northstar\\a2a-stack\\agent\\service.py"',
        )
        self.assertNotIn("--workspace", result["registeredArguments"])
        self.assertIn("Register-ScheduledTask", result["calls"])
        self.assertNotIn("Start-ScheduledTask", result["calls"])

    def test_workspace_run_persists_the_quoted_workspace_argument(self) -> None:
        workspace = str(REPO_ROOT)
        result = self._run_installer(workspace, None)
        self.assertEqual(result["error"], "")
        self.assertTrue(result["registered"])
        self.assertEqual(
            result["registeredArguments"],
            '"D:\\github\\northstar\\a2a-stack\\agent\\service.py" '
            '--workspace "D:\\github\\northstar"',
        )
        self.assertEqual(result["registeredExecute"], self._existing("")["execute"])
        self.assertEqual(result["registeredWorkingDir"], str(REPO_ROOT))

    def test_workspace_only_change_is_allowed_for_the_same_owner(self) -> None:
        existing = self._existing(
            '"D:\\github\\northstar\\a2a-stack\\agent\\service.py" '
            '--workspace "D:\\github\\northstar\\authorized workspace"'
        )
        result = self._run_installer(str(REPO_ROOT), existing)
        self.assertEqual(result["error"], "")
        self.assertTrue(result["registered"])
        self.assertIn("--workspace", result["registeredArguments"])

    def test_workspace_with_spaces_stays_one_quoted_argument(self) -> None:
        with tempfile.TemporaryDirectory(prefix="authorized workspace ") as workspace:
            result = self._run_installer(workspace, None)
            self.assertEqual(result["error"], "")
            self.assertTrue(result["registered"])
            self.assertEqual(
                result["registeredArguments"],
                '"D:\\github\\northstar\\a2a-stack\\agent\\service.py" '
                f'--workspace "{workspace}"',
            )

    def test_unrelated_existing_task_is_still_refused(self) -> None:
        existing = self._existing('"C:\\other\\service.py"')
        result = self._run_installer("", existing)
        self.assertIn("Refusing to replace task", result["error"])
        self.assertFalse(result["registered"])
        self.assertNotIn("Register-ScheduledTask", result["calls"])

    def test_missing_workspace_is_refused_without_registering(self) -> None:
        missing = str(REPO_ROOT / "tmp" / "a2a-stack" / "no-such-workspace")
        result = self._run_installer(missing, None)
        self.assertIn("Workspace directory does not exist", result["error"])
        self.assertFalse(result["registered"])
        self.assertFalse(Path(missing).exists())

    def test_start_flag_is_forwarded_to_the_stubbed_task_cmdlet(self) -> None:
        result = self._run_installer("", None, start=True)
        self.assertEqual(result["error"], "")
        self.assertIn("Start-ScheduledTask", result["calls"])


if __name__ == "__main__":
    unittest.main()
