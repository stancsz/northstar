"""Offline regression for the Invoke-CodexChild helper reference.

The helper body is read from the PowerShell fence in
``skills/codex-subagents/references/cli-dispatch.md`` and executed with pwsh against a local
PowerShell function stub named ``codex``. The stub records the public argument
strings and the child-visible environment, so neither the Codex CLI, the
Subroute gateway, nor any network service is contacted. Every asserted value
is a public argument string or a synthetic sentinel.
"""

import contextlib
import functools
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "codex-subagents" / "references" / "cli-dispatch.md"
PWSH = shutil.which("pwsh")

BASE_URL_OVERRIDE = 'model_providers.subroute.base_url="http://127.0.0.1:4000/v1"'
OBSERVED_OVERRIDES = (
    "features.shell_tool=true",
    "features.apps=false",
    "features.remote_plugin=false",
    "features.multi_agent=false",
    'mcp_servers.browseros-neo.transport="streamable_http"',
    "mcp_servers.browseros-neo.enabled=false",
)
PLUGIN_OVERRIDE = "features.plugins=false"
SKILL_DISCOVERY_ENABLE_FLAG = "--enable"
SKILL_DISCOVERY_FEATURE = "skip_host_skill_discovery"
SKILL_DISCOVERY_ARGUMENTS = (SKILL_DISCOVERY_ENABLE_FLAG, SKILL_DISCOVERY_FEATURE)
ADAPTER_RELATIVE = Path("skills") / "task-completion-review" / "scripts" / "guard_stop.py"
SYNTHETIC_ASSIGNMENT = "Synthetic assignment: report the scoped handoff."

pytestmark = pytest.mark.skipif(
    PWSH is None, reason="pwsh (PowerShell 7) is required to execute the documented helper"
)


DRIVER = r"""
$ErrorActionPreference = 'Stop'
$stubEventPath = __EVENTS__
$stubResultPath = __RESULT__

function Get-EnvState {
    $state = [ordered]@{}
    foreach ($name in @('HOME', 'USERPROFILE', 'CODEX_HOME', 'DONT_STOP_EARLY_REVIEW_CHILD')) {
        $present = Test-Path -Path ('Env:{0}' -f $name)
        $value = [Environment]::GetEnvironmentVariable($name)
        $state[$name] = @{ present = $present; value = $value }
    }
    return $state
}

function codex {
    $stdinLines = @()
    foreach ($item in $input) { $stdinLines += [string]$item }
    $record = [ordered]@{
        arguments = @($args | ForEach-Object { [string]$_ })
        stdin = ($stdinLines -join "`n")
        environment = Get-EnvState
        location = (Get-Location).Path
    }
    ($record | ConvertTo-Json -Compress -Depth 8) | Add-Content -LiteralPath $stubEventPath -Encoding utf8
    if ($env:SYNTHETIC_CODEX_LAUNCH_FAILURE -eq '1') {
        throw 'synthetic codex launch failure'
    }
}

__HELPER__

__SETUP__

$stubCommandType = [string](Get-Command codex -ErrorAction SilentlyContinue).CommandType
$before = Get-EnvState
$errorRecord = $null
try {
    Invoke-CodexChild __INVOCATION__
}
catch {
    $errorRecord = @{ message = [string]$_.Exception.Message; type = [string]$_.Exception.GetType().FullName }
}
$after = Get-EnvState

[ordered]@{
    stub_command_type = $stubCommandType
    before = $before
    after = $after
    error = $errorRecord
} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $stubResultPath -Encoding utf8
exit 0
"""


@functools.lru_cache(maxsize=1)
def extract_helper_function() -> str:
    """Return the Invoke-CodexChild function body from the CLI reference fence."""

    text = SKILL.read_text(encoding="utf-8")
    blocks = re.findall(r"```powershell\r?\n(.*?)```", text, re.DOTALL)
    candidates = [block for block in blocks if "function Invoke-CodexChild" in block]
    assert len(candidates) == 1, "expected exactly one PowerShell fence defining Invoke-CodexChild"
    block = candidates[0]
    start = block.index("function Invoke-CodexChild")
    lines = block[start:].splitlines()
    closing = None
    for index in range(len(lines) - 1, -1, -1):
        if lines[index].strip() == "}":
            closing = index
            break
    assert closing is not None, "Invoke-CodexChild fence has no closing brace"
    helper = "\n".join(lines[: closing + 1])
    assert "function Invoke-CodexChild" in helper and helper.rstrip().endswith("}")
    for expected in (
        "--profile",
        "subroute-subagents",
        "--sandbox",
        "features.plugins=false",
        *OBSERVED_OVERRIDES,
        *SKILL_DISCOVERY_ARGUMENTS,
    ):
        assert expected in helper, f"extracted helper lost {expected!r}"
    return helper


def ps_literal(value) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def set_env(name: str, value) -> str:
    return f"$env:{name} = {ps_literal(value)}"


def unset_env(name: str) -> str:
    return f"Remove-Item Env:{name} -ErrorAction SilentlyContinue"


def normalize(arguments) -> list:
    """Normalize only the resolved working-directory argument."""

    normalized = []
    for value in arguments:
        if normalized and normalized[-1] == "--cd":
            normalized.append(os.path.normcase(os.path.normpath(value)))
        else:
            normalized.append(value)
    return normalized


def expected_arguments(working_directory, sandbox="read-only", overrides=(), extra=(), model=None) -> list:
    arguments = [
        "exec",
        "--json",
        "--cd",
        os.path.normcase(os.path.normpath(str(working_directory))),
        "--profile",
        "subroute-subagents",
        "--ephemeral",
        "--skip-git-repo-check",
        "--sandbox",
        sandbox,
        "-c",
        BASE_URL_OVERRIDE,
    ]
    if model is not None:
        arguments.extend(["--model", model])
    for override in overrides:
        arguments.extend(["-c", override])
    arguments.extend(extra)
    arguments.append("-")
    return arguments


def run_helper(
    root,
    *,
    name,
    working_directory,
    assignment=SYNTHETIC_ASSIGNMENT,
    sandbox=None,
    observed=False,
    disable_plugins=False,
    skip_host_skill_discovery=False,
    model=None,
    setup=(),
    location=None,
):
    """Execute the documented helper in pwsh against the local codex stub."""

    script = root / f"driver-{name}.ps1"
    events = root / f"events-{name}.jsonl"
    result = root / f"result-{name}.json"

    invocation = [
        f"-Assignment {ps_literal(assignment)}",
        f"-WorkingDirectory {ps_literal(working_directory)}",
    ]
    if sandbox is not None:
        invocation.append(f"-Sandbox {ps_literal(sandbox)}")
    if model is not None:
        invocation.append(f"-Model {ps_literal(model)}")
    if observed:
        invocation.append("-UseObservedSubrouteSettings")
    if disable_plugins:
        invocation.append("-DisablePlugins")
    if skip_host_skill_discovery:
        invocation.append("-SkipHostSkillDiscovery")

    setup_lines = []
    if location is not None:
        setup_lines.append(f"Set-Location -LiteralPath {ps_literal(location)}")
    setup_lines.extend(setup)

    driver = (
        DRIVER.replace("__HELPER__", extract_helper_function())
        .replace("__EVENTS__", ps_literal(events))
        .replace("__RESULT__", ps_literal(result))
        .replace("__SETUP__", "\n".join(setup_lines))
        .replace("__INVOCATION__", " ".join(invocation))
    )
    script.write_text(driver, encoding="utf-8")
    try:
        completed = subprocess.run(
            [PWSH, "-NoProfile", "-NonInteractive", "-File", str(script)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    finally:
        script.unlink(missing_ok=True)

    assert completed.returncode == 0, (
        f"driver script for {name} exited {completed.returncode}\n"
        f"stdout: {completed.stdout}\nstderr: {completed.stderr}"
    )
    assert result.exists(), f"driver for {name} wrote no receipt\n{completed.stderr}"
    payload = json.loads(result.read_text(encoding="utf-8-sig"))

    invocations = []
    if events.exists():
        for line in events.read_text(encoding="utf-8-sig").splitlines():
            if line.strip():
                invocations.append(json.loads(line))
    payload["invocations"] = invocations
    return payload


@contextlib.contextmanager
def synthetic_root():
    """Yield a disposable directory that is always removed again."""

    try:
        root = Path(tempfile.mkdtemp(prefix="codex-subagents-helper-"))
    except OSError:
        root = ROOT / "tmp" / f"codex-subagents-helper-{uuid.uuid4().hex}"
        root.mkdir(parents=True, exist_ok=True)
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


@pytest.fixture
def workspace():
    """Synthetic directories used in place of any real working directory."""

    with synthetic_root() as root:
        project = root / "project"
        project.mkdir()
        user_profile = root / "userprofile"
        user_profile.mkdir()
        codex_home = root / "codexhome"
        codex_home.mkdir()
        yield {
            "root": root,
            "project": project,
            "user_profile": user_profile,
            "codex_home": codex_home,
        }


def child_environment(invocation):
    return invocation["environment"]


def test_helper_dispatches_exact_route_profile_and_sandbox_arguments(workspace):
    payload = run_helper(
        workspace["root"],
        name="exact-route",
        working_directory=workspace["project"],
        setup=[set_env("USERPROFILE", workspace["user_profile"]), unset_env("HOME")],
    )
    assert payload["stub_command_type"] == "Function", "codex must be a local function stub"
    assert payload["error"] is None, payload["error"]
    assert len(payload["invocations"]) == 1
    invocation = payload["invocations"][0]
    assert normalize(invocation["arguments"]) == expected_arguments(workspace["project"])
    assert invocation["stdin"] == SYNTHETIC_ASSIGNMENT
    assert invocation["arguments"][-1] == "-"


def test_helper_resolves_relative_working_directory_and_honours_workspace_write(workspace):
    child = workspace["project"] / "child"
    child.mkdir()
    payload = run_helper(
        workspace["root"],
        name="relative-cwd",
        working_directory="child",
        sandbox="workspace-write",
        location=workspace["project"],
        setup=[set_env("USERPROFILE", workspace["user_profile"]), unset_env("HOME")],
    )
    assert payload["error"] is None, payload["error"]
    invocation = payload["invocations"][0]
    assert normalize(invocation["arguments"]) == expected_arguments(child, sandbox="workspace-write")


def test_observed_subroute_settings_add_each_override_exactly_once(workspace):
    payload = run_helper(
        workspace["root"],
        name="observed",
        working_directory=workspace["project"],
        observed=True,
        setup=[set_env("USERPROFILE", workspace["user_profile"]), unset_env("HOME")],
    )
    assert payload["error"] is None, payload["error"]
    arguments = payload["invocations"][0]["arguments"]
    for override in OBSERVED_OVERRIDES:
        assert arguments.count(override) == 1, f"{override} must be added exactly once"
    assert arguments.count(BASE_URL_OVERRIDE) == 1
    assert arguments.count("-c") == 7
    assert normalize(arguments) == expected_arguments(workspace["project"], overrides=OBSERVED_OVERRIDES)

    plain = run_helper(
        workspace["root"],
        name="not-observed",
        working_directory=workspace["project"],
        setup=[set_env("USERPROFILE", workspace["user_profile"]), unset_env("HOME")],
    )
    plain_arguments = plain["invocations"][0]["arguments"]
    for override in OBSERVED_OVERRIDES:
        assert override not in plain_arguments, f"{override} must not appear without the switch"
    assert plain_arguments.count("-c") == 1


def test_disable_plugins_adds_only_its_opt_in_plugin_flag(workspace):
    payload = run_helper(
        workspace["root"],
        name="plugins-only",
        working_directory=workspace["project"],
        disable_plugins=True,
        setup=[set_env("USERPROFILE", workspace["user_profile"]), unset_env("HOME")],
    )
    assert payload["error"] is None, payload["error"]
    arguments = payload["invocations"][0]["arguments"]
    assert arguments.count(PLUGIN_OVERRIDE) == 1
    assert arguments.count("-c") == 2
    for override in OBSERVED_OVERRIDES:
        assert override not in arguments, f"{override} must not appear without the observed switch"
    assert normalize(arguments) == expected_arguments(workspace["project"], overrides=(PLUGIN_OVERRIDE,))

    both = run_helper(
        workspace["root"],
        name="observed-and-plugins",
        working_directory=workspace["project"],
        observed=True,
        disable_plugins=True,
        setup=[set_env("USERPROFILE", workspace["user_profile"]), unset_env("HOME")],
    )
    both_arguments = both["invocations"][0]["arguments"]
    assert both_arguments.count("-c") == 8
    for override in (*OBSERVED_OVERRIDES, PLUGIN_OVERRIDE):
        assert both_arguments.count(override) == 1, f"{override} must be added exactly once"


def test_default_invocation_keeps_the_documented_arguments_unchanged(workspace):
    payload = run_helper(
        workspace["root"],
        name="default-unchanged",
        working_directory=workspace["project"],
        setup=[set_env("USERPROFILE", workspace["user_profile"]), unset_env("HOME")],
    )
    assert payload["error"] is None, payload["error"]
    arguments = payload["invocations"][0]["arguments"]
    assert normalize(arguments) == expected_arguments(workspace["project"])
    assert arguments.count(SKILL_DISCOVERY_ENABLE_FLAG) == 0, "the enable flag must stay opt-in"
    assert arguments.count(SKILL_DISCOVERY_FEATURE) == 0, "the feature must stay opt-in"
    assert arguments.count("-c") == 1


def test_any_supported_model_id_or_alias_can_override_the_profile_default(workspace):
    selected = "provider/model-with-slashes"
    payload = run_helper(
        workspace["root"],
        name="explicit-model",
        working_directory=workspace["project"],
        model=selected,
        setup=[set_env("USERPROFILE", workspace["user_profile"]), unset_env("HOME")],
    )
    assert payload["error"] is None, payload["error"]
    arguments = payload["invocations"][0]["arguments"]
    assert arguments.count("--model") == 1
    assert normalize(arguments) == expected_arguments(workspace["project"], model=selected)


def test_explicit_blank_model_selection_fails_before_launch(workspace):
    payload = run_helper(
        workspace["root"],
        name="blank-model",
        working_directory=workspace["project"],
        model="   ",
        setup=[set_env("USERPROFILE", workspace["user_profile"]), unset_env("HOME")],
    )
    assert payload["error"]["message"] == (
        "Model must not be empty or whitespace-only: provide a model ID or alias supported by the configured endpoint."
    )
    assert payload["invocations"] == []


def test_skip_host_skill_discovery_adds_the_enable_flag_exactly_once(workspace):
    payload = run_helper(
        workspace["root"],
        name="skill-discovery",
        working_directory=workspace["project"],
        skip_host_skill_discovery=True,
        setup=[set_env("USERPROFILE", workspace["user_profile"]), unset_env("HOME")],
    )
    assert payload["error"] is None, payload["error"]
    arguments = payload["invocations"][0]["arguments"]
    assert arguments.count(SKILL_DISCOVERY_ENABLE_FLAG) == 1
    assert arguments.count(SKILL_DISCOVERY_FEATURE) == 1
    index = arguments.index(SKILL_DISCOVERY_ENABLE_FLAG)
    assert arguments[index : index + 2] == list(SKILL_DISCOVERY_ARGUMENTS)
    assert arguments[-1] == "-", "the stdin marker stays the final argument"
    assert normalize(arguments) == expected_arguments(
        workspace["project"], extra=SKILL_DISCOVERY_ARGUMENTS
    )


def test_skip_host_skill_discovery_stays_independent_of_observed_and_plugin_switches(workspace):
    observed = run_helper(
        workspace["root"],
        name="observed-and-skill-discovery",
        working_directory=workspace["project"],
        observed=True,
        skip_host_skill_discovery=True,
        setup=[set_env("USERPROFILE", workspace["user_profile"]), unset_env("HOME")],
    )
    assert observed["error"] is None, observed["error"]
    observed_arguments = observed["invocations"][0]["arguments"]
    assert observed_arguments.count("-c") == 7
    for override in OBSERVED_OVERRIDES:
        assert observed_arguments.count(override) == 1, f"{override} must be added exactly once"
    assert observed_arguments.count(SKILL_DISCOVERY_ENABLE_FLAG) == 1
    assert observed_arguments.count(SKILL_DISCOVERY_FEATURE) == 1
    assert normalize(observed_arguments) == expected_arguments(
        workspace["project"],
        overrides=OBSERVED_OVERRIDES,
        extra=SKILL_DISCOVERY_ARGUMENTS,
    )

    plugins = run_helper(
        workspace["root"],
        name="plugins-and-skill-discovery",
        working_directory=workspace["project"],
        disable_plugins=True,
        skip_host_skill_discovery=True,
        setup=[set_env("USERPROFILE", workspace["user_profile"]), unset_env("HOME")],
    )
    assert plugins["error"] is None, plugins["error"]
    plugin_arguments = plugins["invocations"][0]["arguments"]
    assert plugin_arguments.count("-c") == 2
    assert plugin_arguments.count(PLUGIN_OVERRIDE) == 1
    for override in OBSERVED_OVERRIDES:
        assert override not in plugin_arguments, f"{override} must not appear without the observed switch"
    assert plugin_arguments.count(SKILL_DISCOVERY_ENABLE_FLAG) == 1
    assert plugin_arguments.count(SKILL_DISCOVERY_FEATURE) == 1
    assert normalize(plugin_arguments) == expected_arguments(
        workspace["project"],
        overrides=(PLUGIN_OVERRIDE,),
        extra=SKILL_DISCOVERY_ARGUMENTS,
    )

    combined = run_helper(
        workspace["root"],
        name="all-opt-in-switches",
        working_directory=workspace["project"],
        observed=True,
        disable_plugins=True,
        skip_host_skill_discovery=True,
        setup=[set_env("USERPROFILE", workspace["user_profile"]), unset_env("HOME")],
    )
    assert combined["error"] is None, combined["error"]
    combined_arguments = combined["invocations"][0]["arguments"]
    assert combined_arguments.count("-c") == 8
    for override in (*OBSERVED_OVERRIDES, PLUGIN_OVERRIDE):
        assert combined_arguments.count(override) == 1, f"{override} must be added exactly once"
    assert combined_arguments.count(SKILL_DISCOVERY_ENABLE_FLAG) == 1
    assert combined_arguments.count(SKILL_DISCOVERY_FEATURE) == 1
    assert normalize(combined_arguments) == expected_arguments(
        workspace["project"],
        overrides=(*OBSERVED_OVERRIDES, PLUGIN_OVERRIDE),
        extra=SKILL_DISCOVERY_ARGUMENTS,
    )


def test_overrides_stay_process_only_and_never_write_codex_home(workspace):
    config = workspace["codex_home"] / "config.toml"
    config.write_text("# synthetic sentinel: must stay untouched\n", encoding="utf-8")
    before = config.read_text(encoding="utf-8")
    payload = run_helper(
        workspace["root"],
        name="process-only",
        working_directory=workspace["project"],
        observed=True,
        disable_plugins=True,
        setup=[
            set_env("USERPROFILE", workspace["user_profile"]),
            unset_env("HOME"),
            set_env("CODEX_HOME", workspace["codex_home"]),
        ],
    )
    assert payload["error"] is None, payload["error"]
    assert config.read_text(encoding="utf-8") == before
    assert sorted(item.name for item in workspace["codex_home"].iterdir()) == ["config.toml"]


def test_home_fallback_uses_existing_userprofile_and_restores_absent_home(workspace):
    payload = run_helper(
        workspace["root"],
        name="home-absent",
        working_directory=workspace["project"],
        setup=[set_env("USERPROFILE", workspace["user_profile"]), unset_env("HOME")],
    )
    assert payload["error"] is None, payload["error"]
    assert payload["before"]["HOME"] == {"present": False, "value": None}
    child = child_environment(payload["invocations"][0])
    assert child["HOME"]["present"] is True
    assert os.path.normcase(os.path.normpath(child["HOME"]["value"])) == os.path.normcase(
        os.path.normpath(str(workspace["user_profile"]))
    )
    assert payload["after"]["HOME"] == {"present": False, "value": None}


def test_home_fallback_restores_an_empty_caller_home(workspace):
    payload = run_helper(
        workspace["root"],
        name="home-empty",
        working_directory=workspace["project"],
        setup=[set_env("USERPROFILE", workspace["user_profile"]), set_env("HOME", "")],
    )
    assert payload["error"] is None, payload["error"]
    assert payload["before"]["HOME"] == {"present": True, "value": ""}
    child = child_environment(payload["invocations"][0])
    assert child["HOME"]["present"] is True
    assert os.path.normcase(os.path.normpath(child["HOME"]["value"])) == os.path.normcase(
        os.path.normpath(str(workspace["user_profile"]))
    )
    assert payload["after"]["HOME"] == {"present": True, "value": ""}


def test_existing_home_is_passed_through_to_the_child_and_restored(workspace):
    home = workspace["root"] / "caller-home"
    home.mkdir()
    payload = run_helper(
        workspace["root"],
        name="home-existing",
        working_directory=workspace["project"],
        setup=[set_env("USERPROFILE", workspace["user_profile"]), set_env("HOME", home)],
    )
    assert payload["error"] is None, payload["error"]
    child = child_environment(payload["invocations"][0])
    assert os.path.normcase(os.path.normpath(child["HOME"]["value"])) == os.path.normcase(
        os.path.normpath(str(home))
    )
    assert payload["after"]["HOME"] == payload["before"]["HOME"]


def test_invalid_home_falls_back_to_userprofile_and_restores_the_original_path(workspace):
    invalid_home = workspace["root"] / "absent-home"
    payload = run_helper(
        workspace["root"],
        name="home-invalid",
        working_directory=workspace["project"],
        setup=[set_env("USERPROFILE", workspace["user_profile"]), set_env("HOME", invalid_home)],
    )
    assert payload["error"] is None, payload["error"]
    assert not invalid_home.exists(), "the missing HOME directory must not be created"
    assert payload["before"]["HOME"] == {"present": True, "value": str(invalid_home)}
    assert len(payload["invocations"]) == 1, "the codex stub must dispatch exactly once"
    child = child_environment(payload["invocations"][0])
    assert child["HOME"]["present"] is True
    assert os.path.normcase(os.path.normpath(child["HOME"]["value"])) == os.path.normcase(
        os.path.normpath(str(workspace["user_profile"]))
    )
    assert payload["after"]["HOME"] == {"present": True, "value": str(invalid_home)}


def test_file_valued_home_falls_back_to_userprofile_and_leaves_the_file_untouched(workspace):
    home_file = workspace["root"] / "caller-home-is-a-file"
    sentinel = "synthetic home sentinel\n"
    home_file.write_text(sentinel, encoding="utf-8")

    payload = run_helper(
        workspace["root"],
        name="home-file",
        working_directory=workspace["project"],
        setup=[set_env("USERPROFILE", workspace["user_profile"]), set_env("HOME", home_file)],
    )

    assert payload["error"] is None, payload["error"]
    assert len(payload["invocations"]) == 1, "the codex stub must dispatch exactly once"
    child = child_environment(payload["invocations"][0])
    assert child["HOME"]["present"] is True
    assert os.path.normcase(os.path.normpath(child["HOME"]["value"])) == os.path.normcase(
        os.path.normpath(str(workspace["user_profile"]))
    )
    assert payload["before"]["HOME"] == {"present": True, "value": str(home_file)}
    assert payload["after"]["HOME"] == {"present": True, "value": str(home_file)}
    assert payload["after"]["HOME"] == payload["before"]["HOME"]
    assert home_file.is_file(), "the file-valued HOME must stay a regular file"
    assert home_file.read_text(encoding="utf-8") == sentinel


def test_missing_home_and_userprofile_is_rejected_before_dispatch(workspace):
    missing_profile = workspace["root"] / "absent-userprofile"
    payload = run_helper(
        workspace["root"],
        name="no-home",
        working_directory=workspace["project"],
        setup=[set_env("USERPROFILE", missing_profile), unset_env("HOME")],
    )
    assert payload["error"] is not None
    assert "home directory unavailable" in payload["error"]["message"]
    assert payload["invocations"] == [], "the codex stub must not run without a usable home"


@pytest.mark.parametrize("home_state", ["absent", "invalid-path"])
def test_file_valued_userprofile_is_rejected_before_the_codex_stub_runs(workspace, home_state):
    invalid_profile = workspace["root"] / "userprofile-is-a-file"
    invalid_profile.write_text("synthetic userprofile sentinel\n", encoding="utf-8")
    profile_before = invalid_profile.read_text(encoding="utf-8")

    setup = [set_env("USERPROFILE", invalid_profile)]
    if home_state == "absent":
        setup.append(unset_env("HOME"))
    else:
        setup.append(set_env("HOME", workspace["root"] / "absent-home"))

    payload = run_helper(
        workspace["root"],
        name=f"userprofile-file-{home_state}",
        working_directory=workspace["project"],
        setup=setup,
    )

    assert payload["error"] is not None, "a file-valued USERPROFILE must fail the dispatch"
    assert "home directory unavailable" in payload["error"]["message"]
    assert payload["invocations"] == [], "the codex stub must not run without a usable home"
    assert payload["before"]["USERPROFILE"] == {"present": True, "value": str(invalid_profile)}
    assert invalid_profile.is_file(), "the invalid profile path must stay a file"
    assert invalid_profile.read_text(encoding="utf-8") == profile_before
    assert payload["after"]["HOME"] == payload["before"]["HOME"]
    assert payload["after"]["USERPROFILE"] == payload["before"]["USERPROFILE"]


@pytest.mark.parametrize("kind", ["file", "missing-directory"])
def test_invalid_nonempty_codex_home_is_rejected_before_adapter_probe_or_dispatch(workspace, kind):
    if kind == "file":
        codex_home = workspace["root"] / "codex-home-is-a-file"
        codex_home.write_text("synthetic CODEX_HOME sentinel\n", encoding="utf-8")
    else:
        codex_home = workspace["root"] / "absent-codex-home"

    payload = run_helper(
        workspace["root"],
        name=f"invalid-codex-home-{kind}",
        working_directory=workspace["project"],
        setup=[
            set_env("USERPROFILE", workspace["user_profile"]),
            unset_env("HOME"),
            set_env("CODEX_HOME", codex_home),
            set_env("DONT_STOP_EARLY_REVIEW_CHILD", "caller-prior-marker"),
        ],
    )

    assert payload["error"] is not None, "an invalid nonempty CODEX_HOME must fail the dispatch"
    assert "CODEX_HOME must resolve to an existing directory" in payload["error"]["message"]
    assert payload["invocations"] == [], "the codex stub must not run for an invalid CODEX_HOME"
    assert payload["before"] == payload["after"], "the caller environment must remain unchanged"
    if kind == "file":
        assert codex_home.is_file(), "the invalid CODEX_HOME file must remain a file"


def test_stop_review_marker_is_set_for_the_child_only_when_the_adapter_file_exists(workspace):
    adapter = workspace["codex_home"] / ADAPTER_RELATIVE
    adapter.parent.mkdir(parents=True)
    adapter.write_text("# synthetic adapter sentinel\n", encoding="utf-8")
    payload = run_helper(
        workspace["root"],
        name="marker-present",
        working_directory=workspace["project"],
        setup=[
            set_env("USERPROFILE", workspace["user_profile"]),
            unset_env("HOME"),
            set_env("CODEX_HOME", workspace["codex_home"]),
            unset_env("DONT_STOP_EARLY_REVIEW_CHILD"),
        ],
    )
    assert payload["error"] is None, payload["error"]
    child = child_environment(payload["invocations"][0])
    assert child["DONT_STOP_EARLY_REVIEW_CHILD"] == {"present": True, "value": "1"}
    assert payload["after"]["DONT_STOP_EARLY_REVIEW_CHILD"] == {"present": False, "value": None}


def test_stop_review_marker_is_cleared_for_the_child_when_the_adapter_is_absent(workspace):
    payload = run_helper(
        workspace["root"],
        name="marker-absent",
        working_directory=workspace["project"],
        setup=[
            set_env("USERPROFILE", workspace["user_profile"]),
            unset_env("HOME"),
            set_env("CODEX_HOME", workspace["codex_home"]),
            set_env("DONT_STOP_EARLY_REVIEW_CHILD", "caller-prior-value"),
        ],
    )
    assert payload["error"] is None, payload["error"]
    child = child_environment(payload["invocations"][0])
    assert child["DONT_STOP_EARLY_REVIEW_CHILD"] == {"present": False, "value": None}
    assert payload["after"]["DONT_STOP_EARLY_REVIEW_CHILD"] == {
        "present": True,
        "value": "caller-prior-value",
    }


def test_adapter_directory_is_not_treated_as_the_adapter_file(workspace):
    adapter = workspace["codex_home"] / ADAPTER_RELATIVE
    adapter.mkdir(parents=True)
    payload = run_helper(
        workspace["root"],
        name="marker-directory",
        working_directory=workspace["project"],
        setup=[
            set_env("USERPROFILE", workspace["user_profile"]),
            unset_env("HOME"),
            set_env("CODEX_HOME", workspace["codex_home"]),
            unset_env("DONT_STOP_EARLY_REVIEW_CHILD"),
        ],
    )
    assert payload["error"] is None, payload["error"]
    child = child_environment(payload["invocations"][0])
    assert child["DONT_STOP_EARLY_REVIEW_CHILD"] == {"present": False, "value": None}


@pytest.mark.parametrize("kind", ["missing-directory", "not-a-directory"])
def test_invalid_working_directory_is_rejected_before_the_codex_stub_runs(workspace, kind):
    if kind == "missing-directory":
        working_directory = workspace["root"] / "absent-project"
        expected_message = None
    else:
        working_directory = workspace["root"] / "not-a-directory.txt"
        working_directory.write_text("synthetic\n", encoding="utf-8")
        expected_message = "is not an existing directory"
    payload = run_helper(
        workspace["root"],
        name=f"invalid-cwd-{kind}",
        working_directory=working_directory,
        setup=[set_env("USERPROFILE", workspace["user_profile"]), unset_env("HOME")],
    )
    assert payload["error"] is not None, "an invalid working directory must fail the dispatch"
    assert payload["invocations"] == [], "the codex stub must not be invoked for an invalid directory"
    if expected_message is None:
        assert str(working_directory) in payload["error"]["message"]
    else:
        assert expected_message in payload["error"]["message"]


@pytest.mark.parametrize(
    ("case", "assignment"),
    [("empty", ""), ("whitespace-newline", "   \n\t ")],
)
def test_blank_assignment_is_rejected_before_the_codex_stub_runs(workspace, case, assignment):
    payload = run_helper(
        workspace["root"],
        name=f"blank-assignment-{case}",
        working_directory=workspace["project"],
        assignment=assignment,
        setup=[set_env("USERPROFILE", workspace["user_profile"]), unset_env("HOME")],
    )
    assert payload["error"] is not None, "a blank assignment must fail the dispatch"
    assert (
        "must not be empty or whitespace-only" in payload["error"]["message"]
    ), "a blank assignment must report the documented guard message"
    assert payload["invocations"] == [], "the codex stub must not be invoked for a blank assignment"
    assert (
        payload["before"] == payload["after"]
    ), "a blank assignment must not mutate the caller environment"

    # The guard must also precede working-directory resolution, so a blank
    # assignment reports the same message even when the directory is invalid.
    missing = workspace["root"] / "absent-project"
    ordered = run_helper(
        workspace["root"],
        name=f"blank-assignment-{case}-missing-cwd",
        working_directory=missing,
        assignment=assignment,
        setup=[set_env("USERPROFILE", workspace["user_profile"]), unset_env("HOME")],
    )
    assert ordered["error"] is not None
    assert "must not be empty or whitespace-only" in ordered["error"]["message"]
    assert ordered["invocations"] == []
    assert ordered["before"] == ordered["after"]


def test_caller_environment_is_restored_when_the_codex_stub_raises(workspace):
    adapter = workspace["codex_home"] / ADAPTER_RELATIVE
    adapter.parent.mkdir(parents=True)
    adapter.write_text("# synthetic adapter sentinel\n", encoding="utf-8")

    payload = run_helper(
        workspace["root"],
        name="codex-launch-failure",
        working_directory=workspace["project"],
        setup=[
            set_env("USERPROFILE", workspace["user_profile"]),
            unset_env("HOME"),
            set_env("CODEX_HOME", workspace["codex_home"]),
            set_env("DONT_STOP_EARLY_REVIEW_CHILD", "caller-prior-marker"),
            set_env("SYNTHETIC_CODEX_LAUNCH_FAILURE", "1"),
        ],
    )

    assert payload["stub_command_type"] == "Function", "failure injection must stay in the local stub"
    assert payload["error"] is not None
    assert "synthetic codex launch failure" in payload["error"]["message"]
    assert len(payload["invocations"]) == 1, "the failing local stub must run exactly once"

    child = child_environment(payload["invocations"][0])
    assert child["HOME"] == {"present": True, "value": str(workspace["user_profile"])}
    assert child["DONT_STOP_EARLY_REVIEW_CHILD"] == {"present": True, "value": "1"}

    assert payload["before"]["HOME"] == {"present": False, "value": None}
    assert payload["after"]["HOME"] == payload["before"]["HOME"]
    assert payload["before"]["DONT_STOP_EARLY_REVIEW_CHILD"] == {
        "present": True,
        "value": "caller-prior-marker",
    }
    assert payload["after"]["DONT_STOP_EARLY_REVIEW_CHILD"] == payload["before"][
        "DONT_STOP_EARLY_REVIEW_CHILD"
    ]
    assert payload["after"]["USERPROFILE"] == payload["before"]["USERPROFILE"]
    assert payload["after"]["CODEX_HOME"] == payload["before"]["CODEX_HOME"]
