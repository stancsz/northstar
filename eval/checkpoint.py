"""In-memory snapshots for continuation trials on local diagnostic workspaces."""

from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass

from sandbox import checked, docker


@contextmanager
def repository_snapshot(sandbox):
    """Hold a disposable image of the repository and its container filesystem."""
    if sandbox.base_commit is None:
        raise ValueError("A repository snapshot requires an initialized Git task.")
    mounts = checked(docker("inspect", "--format", "{{len .Mounts}}", sandbox.container))
    if mounts != "0":
        raise ValueError("Mounted volumes are outside the repository snapshot.")
    image = checked(docker("commit", sandbox.container, timeout=120))
    try:
        yield image
    finally:
        checked(docker("image", "rm", image, timeout=60))



@dataclass(frozen=True)
class Checkpoint:
    workspace: bytes
    messages: list[dict]
    remaining_tools: int

    @classmethod
    def capture(cls, sandbox, turn: dict, remaining_tools: int) -> Checkpoint:
        if turn["status"] != "checkpoint" or remaining_tools < 1:
            raise ValueError("A continuation needs a completed tool batch and a positive tool allowance.")
        if sandbox.root != "/work" or sandbox.base_commit is not None:
            raise ValueError("Checkpoint archives currently support local diagnostic workspaces.")
        return cls(sandbox.archive(), deepcopy(turn["messages"]), remaining_tools)

    def restore(self, sandbox) -> list[dict]:
        sandbox.restore_fresh_work(self.workspace)
        return deepcopy(self.messages)
