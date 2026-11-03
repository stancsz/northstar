"""Pure scope-baseline and candidate-coverage helpers for autonomous goals.

The host manager (freeze) and the goal controller (completion validation and
provenance) must agree on which files actually changed inside a goal scope, so
both load this module instead of reimplementing the comparison.
"""
from __future__ import annotations

import hashlib
from pathlib import Path


def file_digest(path):
    """sha256 of a file's bytes."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _inside_workspace(path, workspace):
    return path.is_file() and path.resolve().is_relative_to(workspace)


def _scope_prefix(name):
    """Relative-path prefix selecting the files inside one scope entry.

    The workspace root normalizes to ".", and canonical relative paths never
    carry a "./" prefix, so the root must match every path instead.
    """
    return None if name in ("", ".") else name + "/"


def scope_files(workspace, scope_paths):
    """Current content of every file inside the scope: relative path -> sha256."""
    workspace = Path(workspace).resolve()
    current = {}
    for value in scope_paths or []:
        entry = (workspace / value).resolve()
        if not entry.is_relative_to(workspace):
            continue
        if _inside_workspace(entry, workspace):
            current[entry.relative_to(workspace).as_posix()] = file_digest(entry)
        elif entry.is_dir():
            for path in sorted(entry.rglob("*")):
                if _inside_workspace(path, workspace):
                    current[path.relative_to(workspace).as_posix()] = file_digest(path)
    return dict(sorted(current.items()))


def baseline_snapshot(workspace, scope_paths):
    """Original content of every file inside the scope at goal creation.

    An exact-file scope entry records its own digest, or None when it did not
    exist yet. A directory scope entry records the digest of every file it
    contains, so later additions, edits and deletions are all detectable.
    """
    workspace = Path(workspace).resolve()
    baseline = {}
    for value in scope_paths or []:
        entry = (workspace / value).resolve()
        if not entry.is_relative_to(workspace):
            continue
        name = entry.relative_to(workspace).as_posix()
        if _inside_workspace(entry, workspace):
            baseline[name] = file_digest(entry)
        elif entry.is_dir():
            for path in sorted(entry.rglob("*")):
                if _inside_workspace(path, workspace):
                    baseline[path.relative_to(workspace).as_posix()] = file_digest(path)
        else:
            baseline[name] = None
    return dict(sorted(baseline.items()))


def scope_changes(workspace, scope_paths, baseline):
    """Files inside the scope that differ from the immutable baseline.

    Maps a relative path to its current sha256 for added or modified files and
    to None for deleted files. Content that already existed and did not change
    during the goal is never reported.
    """
    workspace = Path(workspace).resolve()
    baseline = baseline if isinstance(baseline, dict) else {}
    current = scope_files(workspace, scope_paths)
    if not baseline:
        # Without a reference every file in the scope counts as this goal's
        # work; nothing may be accepted on an unproven baseline.
        return dict(current)
    changes = {}

    for value in scope_paths or []:
        entry = (workspace / value).resolve()
        if not entry.is_relative_to(workspace):
            continue
        name = entry.relative_to(workspace).as_posix()
        prefix = _scope_prefix(name)
        nested = {key: baseline[key] for key in baseline
                  if isinstance(baseline[key], str)
                  and (prefix is None or key.startswith(prefix))}
        recorded = baseline.get(name)
        if entry.is_dir():
            now = {key: digest for key, digest in current.items()
                   if prefix is None or key.startswith(prefix)}
            if nested:
                # Directory scope recorded per original contained file.
                originals = dict(nested)
            else:
                # No per-file reference: every file the directory holds now is
                # treated as this goal's work rather than silently ignored.
                originals = {}
            if isinstance(recorded, str):
                # The scope entry was a file at baseline and is now a directory.
                changes[name] = None
        elif isinstance(recorded, str):
            # Exact-file scope entry with a recorded original digest.
            originals = {name: recorded}
            now = {name: current[name]} if name in current else {}
        elif nested:
            # The scope entry was a directory at baseline and is now gone or
            # replaced by a regular file: its original files were deleted with
            # it. A directory baseline records only its nested files, so the
            # recorded value for the directory itself is absent and this
            # check must precede the recorded-is-None branch below.
            originals = dict(nested)
            now = {name: current[name]} if name in current else {}
        elif recorded is None:
            # Exact-file scope entry that did not exist at baseline.
            originals = {}
            now = {name: current[name]} if name in current else {}
        else:
            # No usable reference for this entry; fail closed on its content.
            originals = {}
            now = {key: digest for key, digest in current.items() if key == name}
        for key, digest in originals.items():
            if key not in now:
                changes[key] = None
            elif now[key] != digest:
                changes[key] = now[key]
        for key, digest in now.items():
            if key not in originals:
                changes[key] = digest
    return dict(sorted(changes.items()))


def validate_scope_coverage(workspace, scope_paths, baseline, manifest_files):
    """Fail closed when a candidate omits a real scoped change."""
    changes = scope_changes(workspace, scope_paths, baseline)
    deleted = sorted(name for name, digest in changes.items() if digest is None)
    if deleted:
        raise ValueError("Scoped file was deleted and cannot be represented in a candidate: "
                         + ", ".join(deleted))
    listed = set(manifest_files or {})
    omitted = sorted(name for name in changes if name not in listed)
    if omitted:
        raise ValueError("Candidate omits scoped changes; it must cover every changed scoped file: "
                         + ", ".join(omitted))
