#!/usr/bin/env python3
"""
Layer 7 / VERIFY (mandatory) — do NOT present results until this passes and you
have looked at the rendered report with your own eyes.

This script does the *mechanical* half of verification: it lints the artifacts
for the failure modes that slip past "the script exited 0" (entity leakage,
unfilled placeholders, empty sections, AI tests with no classical backbone,
missing limitations). It also tries to rasterize report.html to report.png so
you can do the *visual* half — actually inspecting formatting.

verify.py cannot replace your eyes. After it runs, open report.png (or report.html)
and confirm: tables aligned, badges visible, no raw HTML/markdown artifacts, every
section populated, the readiness call matches the data. Fix and regenerate until
both the lint and your visual check are clean.

Usage:
    python verify.py <run-dir>
Exit code is non-zero if any FAIL-level check fails.
"""
import argparse, json, os, re, sys, subprocess
from _common import load, info

def opt(p):
    return load(p) if os.path.exists(p) else None

def rasterize(html_path, png_path):
    """Try several backends; return the one that worked or None."""
    # 1) Playwright (best fidelity if installed)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.goto("file://" + os.path.abspath(html_path))
            pg.screenshot(path=png_path, full_page=True)
            b.close()
        return "playwright"
    except Exception:
        pass
    # 2) wkhtmltoimage binary
    for binary in ("wkhtmltoimage", "chromium", "chromium-browser", "google-chrome"):
        try:
            if binary == "wkhtmltoimage":
                subprocess.run([binary, "-q", html_path, png_path], check=True, timeout=60)
            else:
                subprocess.run([binary, "--headless", "--no-sandbox", "--disable-gpu",
                                f"--screenshot={png_path}", "--window-size=1000,1400",
                                "file://" + os.path.abspath(html_path)],
                               check=True, timeout=60, capture_output=True)
            if os.path.exists(png_path):
                return binary
        except Exception:
            continue
    return None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("run_dir")
    ap.add_argument("--strict", action="store_true",
                    help="treat a failed report rasterization as a blocking FAIL "
                         "(no final report without a successful visual render)")
    a = ap.parse_args()
    rd = a.run_dir
    checks = []  # (level, name, ok, detail) ; level in {FAIL, WARN, INFO}

    def chk(level, name, ok, detail=""):
        checks.append({"level": level, "name": name, "passed": bool(ok), "detail": detail})

    # --- artifact presence ---
    graph = opt(f"{rd}/01_requirements.json")
    tc = opt(f"{rd}/02_testcases.json")
    res = opt(f"{rd}/03_results.json")
    readiness = opt(f"{rd}/readiness.json")
    chk("FAIL", "requirement graph exists", graph is not None)
    chk("FAIL", "test suite exists", tc is not None)
    chk("FAIL", "results exist", res is not None)
    chk("FAIL", "readiness score exists", readiness is not None)
    chk("FAIL", "report.html exists", os.path.exists(f"{rd}/report.html"))
    chk("FAIL", "report.md exists", os.path.exists(f"{rd}/report.md"))

    # --- no unfilled placeholders ---
    if tc:
        chk("FAIL", "no TODO placeholders in suite", "TODO" not in json.dumps(tc),
            "fill every scaffolded TODO before reporting")

    # --- AI tests rest on a classical backbone ---
    if tc and graph:
        ai_reqs = {r["id"] for r in graph["requirements"] if r.get("is_ai_feature")}
        classical_reqs = {rid for c in tc["cases"] if c.get("source") == "classical"
                          for rid in c.get("requirement_ids", [])}
        rubric_reqs = {rid for c in tc["cases"]
                       if c.get("expected", {}).get("mode") == "rubric"
                       for rid in c.get("requirement_ids", [])}
        orphan = sorted((rubric_reqs & ai_reqs) - classical_reqs)
        chk("FAIL", "AI tests grounded in classical tests", not orphan,
            f"AI/rubric cases without a classical backbone: {orphan}" if orphan
            else "every AI feature also has classical (EP/BVA/DT/ST) coverage")
        any_classical = any(c.get("source") == "classical" for c in tc["cases"])
        chk("WARN", "classical backbone present", any_classical,
            "run classical_tests.py expand to generate the backbone" if not any_classical else "")

    # --- coverage: every requirement has a case ---
    if tc and graph:
        covered = {rid for c in tc["cases"] for rid in c.get("requirement_ids", [])}
        uncovered = sorted({r["id"] for r in graph["requirements"]} - covered)
        chk("FAIL", "every requirement covered", not uncovered,
            f"uncovered: {uncovered}" if uncovered else "100% requirement coverage")

    # --- Standards Conformance mode: conformance_criterion reqs have standard_id + clause ---
    if graph:
        conf_reqs = [r for r in graph["requirements"] if r.get("type") == "conformance_criterion"]
        if conf_reqs:
            bad = [r["id"] for r in conf_reqs
                   if not r.get("standard_id") or not r.get("clause")]
            chk("FAIL", "conformance_criterion reqs have standard_id + clause", not bad,
                f"missing standard_id or clause: {bad}" if bad
                else f"all {len(conf_reqs)} conformance reqs tagged with standard_id + clause")
            # standards_index.json must exist at run root
            idx = opt(f"{rd}/standards_index.json")
            any_tagged = any(r.get("standard_id") for r in graph["requirements"])
            chk("FAIL" if any_tagged else "INFO",
                "standards_index.json present when standard_id is used",
                idx is not None,
                ("standards_index.json missing — run ingest_standard.py to create it, "
                 "or remove standard_id from the requirement graph.") if not idx and any_tagged
                else "")

    # --- codebase targets have a valid glob pattern ---
    if tc:
        bad_codebase = []
        for c in tc["cases"]:
            tgt = c.get("target", {})
            if tgt.get("kind") == "codebase":
                pat = tgt.get("pattern")
                if not pat or not isinstance(pat, (str, list)) or (
                        isinstance(pat, str) and not pat.strip()):
                    bad_codebase.append(c["id"])
        chk("FAIL", "codebase targets have a non-empty pattern", not bad_codebase,
            f"codebase targets missing pattern: {bad_codebase}" if bad_codebase else "")

    # --- skipped cases are not silently passed ---
    if res:
        skipped = [r["case_id"] for r in res["results"] if r["status"] == "skipped"]
        chk("INFO", "manual/skipped cases flagged", True,
            f"{len(skipped)} manual cases to run by hand: {skipped}" if skipped else "none")

    # --- report formatting: no entity leakage in markdown ---
    if os.path.exists(f"{rd}/report.md"):
        md = open(f"{rd}/report.md", encoding="utf-8").read()
        bad = [e for e in ("&quot;", "&#x27;", "&amp;", "&lt;", "&gt;") if e in md]
        chk("FAIL", "no HTML entities leaked into markdown", not bad,
            f"found {bad} — fix escaping in make_report.py" if bad else "")
    if os.path.exists(f"{rd}/report.html"):
        h = open(f"{rd}/report.html", encoding="utf-8").read()
        # genuine unrendered f-string fields look like {word}; ignore JSON braces ({"...)
        stray = re.findall(r"\{[A-Za-z_][\w\.\[\]'\"() ]*\}", h.split("<body>")[-1])
        stray = [s for s in stray if not s.startswith('{"') and not s.startswith("{'")]
        chk("FAIL", "no unrendered template fields", not stray,
            f"stray fields {stray[:3]} suggest a broken f-string" if stray else "")
        chk("WARN", "report has a readiness score", "/100" in h)

    # --- hidden limitations enumerated ---
    lim = f"{rd}/limitations.md"
    has_lim = os.path.exists(lim) and len(open(lim, encoding="utf-8").read().strip()) > 120
    chk("FAIL", "hidden limitations documented", has_lim,
        "author limitations.md: what was NOT tested, assumptions made, what could "
        "still fail in production despite a green report")

    # --- readiness sanity: hold iff critical or <70 ---
    if readiness:
        rec, score = readiness["recommendation"], readiness["score"]
        blocking = readiness.get("blocking", [])
        sane = (rec == "hold") == (bool(blocking) or score < 70)
        chk("WARN", "readiness recommendation matches data", sane,
            f"score={score} rec={rec} blocking={blocking}")

    # --- visual half: rasterize for inspection ---
    png = f"{rd}/report.png"
    backend = rasterize(f"{rd}/report.html", png) if os.path.exists(f"{rd}/report.html") else None
    if backend:
        chk("INFO", "report rasterized for visual check", True,
            f"rendered via {backend} -> report.png — NOW OPEN IT AND LOOK")
    else:
        chk("FAIL" if a.strict else "WARN", "report rasterized for visual check", False,
            ("--strict: no headless renderer available and a visual render is required. "
             "Install Playwright (pip install playwright --break-system-packages && "
             "playwright install chromium) or run without --strict and inspect report.html "
             "manually.") if a.strict else
            "no headless renderer available — open report.html directly and inspect formatting")

    # --- write + summarize ---
    from _common import save
    save({"checks": checks}, f"{rd}/verification.json")
    fails = [c for c in checks if c["level"] == "FAIL" and not c["passed"]]
    warns = [c for c in checks if c["level"] == "WARN" and not c["passed"]]
    for c in checks:
        mark = "PASS" if c["passed"] else c["level"]
        info(f"  [{mark}] {c['name']}" + (f" — {c['detail']}" if c["detail"] else ""))
    info("")
    if fails:
        info(f"VERIFICATION FAILED: {len(fails)} blocking issue(s). Fix and re-run before reporting.")
        sys.exit(1)
    info(f"Automated checks passed ({len(warns)} warnings). "
         f"NOW DO THE VISUAL CHECK: open {'report.png' if backend else 'report.html'} and confirm "
         "formatting with your own eyes before presenting to the user.")

if __name__ == "__main__":
    main()
