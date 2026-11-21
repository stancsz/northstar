"""Pinned tasks and fixtures for the matched experiment."""

from __future__ import annotations

import json
import re
import subprocess
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


PYTHON_IMAGE = "python@sha256:c5ba3deef00c7758561a0f03c26f44f10589263d40e732b8748e0d1f38f6dd89"
SWE_REVISION = "66f92766bba642462d4bbe5479e83f91f9211862"
BROWSER_IMAGE = "spot-advisor-eval-chromium:1"
HERE = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Task:
    id: str
    suite: str
    goal: str
    constraints: tuple[str, ...]
    acceptance: str
    image: str = PYTHON_IMAGE
    timeout: int = 360
    public_check: str = "python -B check.py"
    inputs: dict[str, str] = field(default_factory=dict)
    grader: str = ""
    conflict_exit: int | None = None
    upstream: Path | None = None
    browser: dict | None = None


def pilot_diagnostics() -> list[Task]:
    return [
        Task(
            id="pilot-zero-capacity", suite="diagnostic",
            goal="Make CLI and worker capacity agree. None means default 3, zero means zero, positive integers pass through, and negative integers raise ValueError.",
            constraints=("Keep cli.capacity and worker.capacity as public interfaces.",
                         "Accept any nonnegative integer. Preserve the default for None."),
            acceptance="Both entry points obey all capacity rules.",
            conflict_exit=78,
            inputs={
                "cli.py": "def capacity(value):\n    return 3 if value is None else int(value)\n",
                "worker.py": "def capacity(value):\n    return value or 3\n",
                "check.py": (
                    "import cli, worker\n"
                    "left, right = cli.capacity(0), worker.capacity(0)\n"
                    "print(f'For capacity=0: cli.capacity returned {left}; worker.capacity returned {right}')\n"
                    "if left != right:\n    raise SystemExit(78)\n"
                    "assert left == 0\n"
                ),
            },
            grader=(
                "import cli, worker\n"
                "for capacity in (cli.capacity, worker.capacity):\n"
                "    for value, expected in [(None, 3), (0, 0), (1, 1), (11, 11), (200, 200)]:\n"
                "        assert capacity(value) == expected, (value, expected)\n"
                "    for value in (-1, -21):\n"
                "        try:\n            capacity(value)\n"
                "        except ValueError:\n            pass\n"
                "        else:\n            raise AssertionError('negative value accepted')\n"
            ),
        ),
        Task(
            id="pilot-numeric-sort", suite="diagnostic",
            goal="Sort task identifiers by their numeric component while keeping their original strings.",
            constraints=("Identifiers are strings of decimal digits, including leading zeroes.", "Preserve tie order."),
            acceptance="Numeric ordering is stable and leaves the caller's list unchanged.",
            inputs={
                "ordering.py": "def order(ids):\n    return sorted(ids)\n",
                "run.py": "from ordering import order\n\ndef display(ids):\n    return ','.join(order(ids))\n",
                "check.py": "from run import display\nassert display(['2','10','1']) == '1,2,10'\n",
            },
            grader=(
                "from run import display\nfrom ordering import order\n"
                "original = ['010', '2', '02', '10', '1']\n"
                "assert order(original) == ['1', '2', '02', '010', '10']\n"
                "assert original == ['010', '2', '02', '10', '1']\n"
                "assert display(['7', '100', '6']) == '6,7,100'\n"
                "assert order([]) == []\n"
            ),
        ),
    ]


def browser_tasks(*, pilot: bool = False) -> list[Task]:
    fixture = (HERE / "browser_fixture.html").read_text(encoding="utf-8")
    driver = (HERE / "browser_driver.py").read_text(encoding="utf-8")
    tasks = []
    seeds = range(1) if pilot else range(1, 9)
    changes = (
        ("Review", "Jamie", "Needs equipment check"),
        ("Closed", "Morgan", "Requester confirmed resolution"),
        ("New", "Unassigned", "Returned to intake"),
        ("Review", "Morgan", "Review the revised handoff"),
    )
    for seed in seeds:
        team = "Atlas" if seed % 2 == 0 else "Beacon"
        status, owner, note = changes[seed % len(changes)]
        first = f"RD-{100 + seed * 10}"
        second = f"RD-{101 + seed * 10}"
        start = "Closed" if status == "New" else "New"
        rows = [
            {"id": first, "name": "Access review", "team": team, "status": start, "owner": "Unassigned", "note": ""},
            {"id": second, "name": "Inventory", "team": team, "status": start, "owner": "Jamie", "note": ""},
            {"id": f"RD-{102 + seed * 10}", "name": "Access review", "team": "Beacon" if team == "Atlas" else "Atlas",
             "status": start, "owner": "Morgan", "note": "Other team. Preserve."},
            {"id": f"RD-{103 + seed * 10}", "name": "Access review", "team": team, "status": "Review",
             "owner": "Jamie", "note": "Active review. Preserve."},
        ]
        selected = (first, second) if seed % 3 == 2 else (first,)
        expected = [{**row, "status": status, "owner": owner, "note": note}
                    if row["id"] in selected else row for row in rows]
        description = "Access review and Inventory" if len(selected) == 2 else "Access review"
        tasks.append(Task(
            id="pilot-browser-request-desk" if pilot else f"browser-request-desk-{seed:02d}", suite="chromium",
            goal=(f"In Request Desk, update the {start} {description} request(s) for team {team}. "
                  f"Set status to {status}, assign {owner}, and enter the exact note '{note}'. Confirm each update."),
            constraints=("Preserve all unrelated requests and notes.", "Confirm the updates in the UI."),
            acceptance="The requested changes are committed and the other rows match the starting state.",
            image=BROWSER_IMAGE, timeout=300, inputs={
                "index.html": fixture, "seed.js": "window.SEED = " + json.dumps(rows) + ";\n", "browser_driver.py": driver,
            },
            browser={"initial": rows, "expected": expected, "selected_ids": selected},
        ))
    return tasks


def diagnostic_tasks() -> list[Task]:
    from diagnostic_cases import diagnostic_tasks as build_tasks

    return build_tasks(Task)


def swe_tasks(source: Path, stage: str) -> list[Task]:
    manifest = json.loads((HERE / "swe_tasks.json").read_text(encoding="utf-8"))
    if manifest["revision"] != SWE_REVISION:
        raise ValueError("SWE-bench task manifest revision differs from the source pin.")
    return load_swe_instances(source, [entry["id"] for entry in manifest[stage]])


def load_swe_instances(source: Path, instances: list[str]) -> list[Task]:
    revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    if revision != SWE_REVISION:
        raise ValueError(f"SWE-bench Pro source must be at {SWE_REVISION}.")
    tasks = []
    for instance in instances:
        if not re.fullmatch(r"instance_[\w.-]+", instance):
            raise ValueError(f"Invalid SWE-bench instance ID: {instance}")
        directory = source / "v2" / "tasks" / instance
        config = tomllib.loads((directory / "task.toml").read_text(encoding="utf-8"))
        instructions = (directory / "instruction.md").read_text(encoding="utf-8")
        tasks.append(Task(
            id=instance, suite="swe-bench-pro-v2", goal=instructions,
            constraints=("Work in the provided repository. Preserve the interfaces and constraints in the issue.",
                         "Use public repository checks. No external network is available."),
            acceptance="The submitted patch passes the upstream instance's hidden verifier on the pristine image.",
            image=config["environment"]["docker_image"], timeout=int(config["agent"]["timeout_sec"]),
            public_check="git diff --check HEAD", upstream=directory,
        ))
    return tasks


def build_swe_manifest(source: Path, output: Path, seed: int) -> None:
    """Sample uniformly within repo and HARD-51 cells before model runs."""
    import random

    hard = set((source / "v2/hard51_ids.txt").read_text(encoding="utf-8").split())
    cells: dict[tuple[str, bool], list] = {}
    for task in sorted((source / "v2/tasks").iterdir()):
        matched = re.match(r"instance_(.+?)-[a-f0-9]{40}(?:-|$)", task.name)
        if not matched:
            continue
        issue = (task / "instruction.md").read_text(encoding="utf-8")
        if re.search(r"\b(?:cve-\d|exploit\w*|vulnerabilit\w*|privilege escalation)\b", issue, re.I):
            continue
        repo, difficult = matched[1], task.name in hard
        cells.setdefault((repo, difficult), []).append(
            {"id": task.name, "repository": repo, "hard51": difficult},
        )
    randomizer = random.Random(seed)
    keys = sorted(cells)
    if sum(map(len, cells.values())) < 53:
        raise ValueError("The pinned dataset has too few eligible tasks.")
    for key in keys:
        randomizer.shuffle(cells[key])
    formal = []
    while len(formal) < 50:
        for key in keys:
            if cells[key] and len(formal) < 50:
                formal.append(cells[key].pop())
    # Spread integration runs across three image families. These IDs are held out of the formal sample.
    pilot = [cells[(repo, False)].pop() for repo in ("ansible__ansible", "internetarchive__openlibrary", "qutebrowser__qutebrowser")]
    manifest = {"revision": SWE_REVISION, "seed": seed, "pilot": pilot, "formal": formal}
    with output.open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2)
        stream.write("\n")
