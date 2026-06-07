#!/usr/bin/env python3
"""
Layer 3 / EXECUTE — run the test suite against the system under test.

Target kinds:
  http     : HTTP request (urllib, no deps). request = {method,url,headers,body}
  cli      : shell command; result = {stdout, stderr, exit_code}
  python   : import module, call callable(*args, **kwargs); result = return value
  codebase : static check against a repo (glob + regex). result = {files, count, matches, ...}
             (Standards Conformance mode; --repo or $SDQ_REPO supplies the repo path)
  manual   : cannot auto-execute — marked 'skipped' with a note for human run

Expected modes:
  exact     : compare against expected.exact (status/json_path/equals/contains)
  predicate : eval a python expression over `result` (sandboxed-ish; trusted suite)
  rubric    : not scored here — marked 'needs_eval' and handed to judge.py

AI features run N samples (default 3) so Layer 5 can measure consistency.
Self-heal: on a transient failure, retry once; for http 404/selector-style
failures, this is where semantic intent re-derivation would hook in (logged,
not silently mutated).

Usage:
    python run_suite.py <run-dir>/02_testcases.json --out <run-dir>/03_results.json \
        [--samples 3] [--repo /path/to/repo]
"""
import argparse, fnmatch, json, os, re, subprocess, importlib, urllib.request, urllib.error
from _common import load, save, info, now

# Directories and file extensions skipped during a codebase scan. Keep this in sync
# with the limits documented in references/schemas.md and standards_to_testcases.md.
_CODEBASE_SKIP_DIRS = {".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build"}
_CODEBASE_SKIP_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".tar", ".tar.gz", ".bin", ".exe", ".so", ".dll", ".ico", ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".mp3", ".class", ".jar"}
_CODEBASE_MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MiB

def http_call(req):
    body = req.get("body")
    data = json.dumps(body).encode() if isinstance(body, (dict, list)) else (
        body.encode() if isinstance(body, str) else None)
    r = urllib.request.Request(req["url"], data=data,
                               method=req.get("method", "GET"),
                               headers=req.get("headers", {}))
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return {"status": resp.status, "body": raw}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "body": e.read().decode("utf-8", "replace")}

def cli_call(cmd):
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
    return {"stdout": p.stdout, "stderr": p.stderr, "exit_code": p.returncode}

def py_call(t):
    mod = importlib.import_module(t["module"])
    fn = getattr(mod, t["callable"])
    return fn(*t.get("args", []), **t.get("kwargs", {}))

def _glob_match(rel, pattern):
    """Match a relative POSIX path against a glob pattern that may include `**`.
    fnmatch alone does not support `**`; we translate `**/` to 'zero or more
    path components' and fall back to fnmatch."""
    from pathlib import PurePosixPath
    # Normalize: `**` means "any depth"; `**/x` means "x at any depth".
    if "**" not in pattern:
        return fnmatch.fnmatch(rel, pattern)
    # Try matching the rel path against the pattern component-by-component.
    pat_parts = pattern.split("/")
    rel_parts = rel.split("/")
    def _match_parts(p, r):
        if not p:
            return not r
        head, *tail = p
        if head == "**":
            # ** can consume zero or more rel parts; try every split.
            for k in range(len(r) + 1):
                if _match_parts(tail, r[k:]):
                    return True
            return False
        if not r:
            return False
        if head == "*" or fnmatch.fnmatchcase(r[0], head):
            return _match_parts(tail, r[1:])
        return False
    return _match_parts(pat_parts, rel_parts)

def _glob_repo(repo, pattern):
    """Yield (abs_path, rel_path) for every file under `repo` whose relpath
    matches the glob `pattern` (supports ** via Path.rglob, plus multiple
    alternation patterns when passed a list)."""
    patterns = pattern if isinstance(pattern, list) else [pattern]
    seen = set()
    from pathlib import Path
    root = Path(repo)
    if not root.exists():
        return
    for pat in patterns:
        # fnmatch handles '**' poorly; use rglob + relpath match instead.
        if "**" in pat:
            base, _, tail = pat.partition("**/")
            base_path = (root / base) if base and base != "" else root
            base_path = base_path.rstrip("/") if str(base_path) != str(root) else root
            try:
                iterator = base_path.rglob(tail or "*")
            except Exception:
                continue
        else:
            try:
                iterator = root.rglob(pat)
            except Exception:
                continue
        for p in iterator:
            if not p.is_file():
                continue
            rel = p.relative_to(root).as_posix()
            if any(part in _CODEBASE_SKIP_DIRS for part in p.relative_to(root).parts):
                continue
            if p.suffix.lower() in _CODEBASE_SKIP_EXTS:
                continue
            if p.stat().st_size > _CODEBASE_MAX_FILE_BYTES:
                continue
            key = str(p.resolve())
            if key in seen:
                continue
            seen.add(key)
            yield p, rel

def codebase_call(t):
    """Static check against a target repo. See references/schemas.md for the
    result shape. Never raises — errors are captured in result['errors']."""
    from pathlib import Path
    repo = t.get("repo") or os.environ.get("SDQ_REPO")
    pattern = t.get("pattern")
    regex = t.get("regex")
    file_match = t.get("file_match")
    if not repo:
        return {"error": "no repo specified (target.repo or --repo / $SDQ_REPO required)",
                "files": [], "count": 0, "matches": [], "scanned_files": 0, "scanned_bytes": 0}
    if not pattern:
        return {"error": "codebase target requires 'pattern'",
                "files": [], "count": 0, "matches": [], "scanned_files": 0, "scanned_bytes": 0}
    if not os.path.isdir(repo):
        return {"error": f"repo not a directory: {repo}",
                "files": [], "count": 0, "matches": [], "scanned_files": 0, "scanned_bytes": 0}

    rx = re.compile(regex) if regex else None
    fm_fn = (lambda rel: _glob_match(rel, file_match)) if file_match else (lambda rel: True)
    files, matches, scanned_files, scanned_bytes, errors = [], [], 0, 0, []
    for abs_path, rel in _glob_repo(repo, pattern):
        scanned_files += 1
        try:
            size = abs_path.stat().st_size
            scanned_bytes += size
        except OSError:
            continue
        if not fm_fn(rel):
            continue
        if rx is None:
            files.append(str(abs_path))
            continue
        try:
            text = abs_path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError) as e:
            errors.append(f"{rel}: {e}")
            continue
        for n, line in enumerate(text.splitlines(), 1):
            m = rx.search(line)
            if m:
                files.append(str(abs_path))
                matches.append({"file": str(abs_path), "rel": rel, "line": n, "text": line.strip()})
                break
    return {"repo": os.path.abspath(repo), "files": files, "count": len(files),
            "matches": matches, "scanned_files": scanned_files,
            "scanned_bytes": scanned_bytes, "errors": errors}

def execute(target, default_repo=None):
    k = target.get("kind")
    if k == "http":     return http_call(target["request"])
    if k == "cli":      return cli_call(target["command"])
    if k == "python":   return py_call(target)
    if k == "codebase":
        if not target.get("repo"):
            target = dict(target)
            target["repo"] = default_repo or os.environ.get("SDQ_REPO")
        return codebase_call(target)
    return None  # manual

def check_exact(result, spec):
    if result is None:
        return False, "no result"
    if "status" in spec and isinstance(result, dict):
        if result.get("status") != spec["status"]:
            return False, f"status {result.get('status')} != {spec['status']}"
    blob = json.dumps(result, default=str)
    if "contains" in spec and spec["contains"] not in blob:
        return False, f"missing substring {spec['contains']!r}"
    if "json_path" in spec:
        try:
            cur = result if not isinstance(result, dict) else result.get("body", result)
            cur = json.loads(cur) if isinstance(cur, str) else cur
            for part in spec["json_path"].lstrip("$.").split("."):
                cur = cur[int(part)] if part.isdigit() else cur[part]
            if "equals" in spec and cur != spec["equals"]:
                return False, f"{spec['json_path']}={cur!r} != {spec['equals']!r}"
        except Exception as e:
            return False, f"json_path eval failed: {e}"
    return True, "matched expected"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("testcases"); ap.add_argument("--out", required=True)
    ap.add_argument("--samples", type=int, default=3)
    ap.add_argument("--repo", default=None,
                    help="target repo path for `codebase` targets (also: $SDQ_REPO). "
                         "Per-case target.repo overrides this.")
    a = ap.parse_args()
    tc = load(a.testcases)
    default_repo = a.repo or os.environ.get("SDQ_REPO")
    results = []
    for c in tc["cases"]:
        mode = c.get("expected", {}).get("mode")
        target = c.get("target", {})
        if target.get("kind", "manual") == "manual":
            results.append({"case_id": c["id"], "status": "skipped",
                            "samples": [], "assertion_detail": "manual target — run by hand",
                            "self_heal": {"attempted": False, "note": ""}})
            continue
        # AI/rubric cases get N samples; deterministic cases get 1
        n = a.samples if mode == "rubric" else 1
        samples, heal = [], {"attempted": False, "note": ""}
        for _ in range(n):
            try:
                r = execute(target, default_repo=default_repo)
            except Exception as e:
                heal = {"attempted": True, "note": f"retry after error: {e}"}
                try:
                    r = execute(target, default_repo=default_repo)
                except Exception as e2:
                    samples.append({"raw": f"ERROR: {e2}", "latency_ms": None, "meta": {}})
                    continue
            samples.append({"raw": r, "latency_ms": None, "meta": {}})

        if mode == "rubric":
            status, detail = "needs_eval", "rubric-scored in Layer 5"
        elif any("ERROR:" in str(s["raw"]) for s in samples):
            status, detail = "error", "execution error"
        elif mode == "predicate":
            try:
                safe = {"str": str, "len": len, "int": int, "float": float, "abs": abs,
                        "min": min, "max": max, "any": any, "all": all, "bool": bool,
                        "sorted": sorted, "round": round}
                ok = bool(eval(c["expected"]["predicate"], {"__builtins__": safe},
                               {"result": samples[0]["raw"]}))
                status, detail = ("pass" if ok else "fail"), c["expected"]["predicate"]
            except Exception as e:
                status, detail = "error", f"predicate error: {e}"
        else:  # exact
            ok, detail = check_exact(samples[0]["raw"], c["expected"].get("exact", {}))
            status = "pass" if ok else "fail"
        results.append({"case_id": c["id"], "status": status, "samples": samples,
                        "assertion_detail": detail, "self_heal": heal})

    save({"run_for": a.testcases, "executed_at": now(), "results": results}, a.out)
    tally = {}
    for r in results:
        tally[r["status"]] = tally.get(r["status"], 0) + 1
    info("Execution complete: " + ", ".join(f"{k}={v}" for k, v in sorted(tally.items())))

if __name__ == "__main__":
    main()
