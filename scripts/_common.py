"""Shared helpers for spec-driven-qa scripts. Import-only, no side effects."""
import json, os, sys, datetime

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save(obj, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return path

def die(msg, code=1):
    print(f"[sdq] ERROR: {msg}", file=sys.stderr)
    sys.exit(code)

def info(msg):
    print(f"[sdq] {msg}")

# Severity weights used by the readiness score.
SEVERITY_WEIGHT = {"critical": 1.0, "high": 0.6, "medium": 0.3, "low": 0.1}
