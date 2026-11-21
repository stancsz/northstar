"""Disposable tool and verifier containers for each experimental arm."""

from __future__ import annotations

import subprocess
from math import ceil
from pathlib import Path


class SandboxError(RuntimeError):
    pass


def docker(*arguments: str, timeout: float = 30, data: bytes | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *arguments], input=data, capture_output=True, timeout=timeout, check=False)


def checked(result: subprocess.CompletedProcess) -> str:
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise SandboxError(detail[-500:] or f"Docker returned exit {result.returncode}.")
    return result.stdout.decode("utf-8", errors="replace").strip()


class Sandbox:
    def __init__(self, image: str, *, network: str = "none"):
        self.image = image
        self.network = network
        self.container = None
        self.root = "/work"
        self.base_commit = None

    def __enter__(self):
        self.container = checked(docker(
            "run", "--detach", "--rm", "--pull=never", "--platform=linux/amd64",
            "--network", self.network, "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--pids-limit", "256", "--label", "spot-advisor.eval=true",
            "--entrypoint", "/bin/sh", self.image, "-c", "sleep 7200", timeout=60,
        ))
        return self

    def __exit__(self, *_):
        if self.container:
            docker("rm", "--force", self.container)

    def exec(self, script: str, *, timeout: float = 60, data: bytes | None = None) -> subprocess.CompletedProcess:
        seconds = str(max(1, ceil(timeout)))
        return docker("exec", "-i", "-w", self.root, self.container, "timeout", "-k", "3", seconds,
                      "/bin/sh", "-c", script, timeout=timeout + 10, data=data)

    def copy(self, source: Path, dest: str, timeout: float = 40) -> None:
        checked(docker("cp", str(source.resolve()), f"{self.container}:{dest}", timeout=timeout))

    def initial(self, task, inputs: Path) -> None:
        if task.upstream is not None:
            self.root = checked(docker("exec", self.container, "/bin/sh", "-c",
                                       "for p in /app /testbed; do if git -C \"$p\" rev-parse --is-inside-work-tree >/dev/null 2>&1; then echo \"$p\"; exit; fi; done; exit 1"))
            self.base_commit = checked(self.exec("git rev-parse --verify HEAD"))
            return
        checked(docker("exec", self.container, "mkdir", "-p", self.root))
        self.copy(inputs, "/")

    def patch(self) -> bytes:
        if not self.base_commit or len(self.base_commit) != 40 or any(c not in "0123456789abcdef" for c in self.base_commit):
            raise SandboxError("A public coding task requires its original Git commit.")
        result = self.exec("git add -A -- . && git --no-pager diff --cached --no-ext-diff "
                           f"--no-textconv --binary {self.base_commit} --")
        if result.returncode:
            checked(result)
        return result.stdout

    def archive(self) -> bytes:
        result = self.exec("tar -cf - .")
        if result.returncode:
            checked(result)
        return result.stdout

    def restore(self, content: bytes) -> None:
        checked(self.exec("tar -xf -", data=content))

    def restore_fresh_work(self, content: bytes) -> None:
        """Restore a complete diagnostic workspace, including file deletions."""
        if self.root != "/work" or self.base_commit is not None:
            raise ValueError("Restore requires a fresh diagnostic sandbox.")
        checked(docker("exec", self.container, "mkdir", "-p", "/work"))
        checked(self.exec("test -z \"$(ls -A /work)\""))
        self.restore(content)
