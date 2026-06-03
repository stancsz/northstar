#!/usr/bin/env python3
"""
Layer 3 / EXECUTE — run the test suite against the system under test.

Target kinds:
  http   : HTTP request (urllib, no deps). request = {method,url,headers,body}
  cli    : shell command; result = {stdout, stderr, exit_code}
  python : import module, call callable(*args, **kwargs); result = return value
  manual : cannot auto-execute — marked 'skipped' with a note for human run

Expected modes:
  exact     : compare against expected.exact (status/json_path/equals/contains)
  predicate : eval a python expression over `result` (sandboxed-ish; trusted suite)
  rubric    : not scored here — marked 'needs_eval' and handed to judge.py

AI features run N samples (default 3) so Layer 5 can measure consistency.
Self-heal: on a transient failure, retry once; for http 404/selector-style
failures, this is where semantic intent re-derivation would hook in (logged,
not silently mutated).

Usage:
    python run_suite.py <run-dir>/02_testcases.json --out <run-dir>/03_results.json [--samples 3]
"""
import argparse, json, subprocess, importlib, urllib.request, urllib.error
from _common import load, save, info, now

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

def execute(target):
    k = target.get("kind")
    if k == "http":   return http_call(target["request"])
    if k == "cli":    return cli_call(target["command"])
    if k == "python": return py_call(target)
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
    a = ap.parse_args()
    tc = load(a.testcases)
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
                r = execute(target)
            except Exception as e:
                heal = {"attempted": True, "note": f"retry after error: {e}"}
                try:
                    r = execute(target)
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
