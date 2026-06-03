#!/usr/bin/env python3
"""
Layer 6 / REPORT & COMPLY — assemble the human-readable report from every
artifact: requirement-mapped coverage, defect log with reproduction, AI
evaluation + consistency, adversarial results, compliance, and the release
readiness scorecard. Writes report.html and report.md.

Usage:
    python make_report.py <run-dir>
"""
import argparse, html, os
from _common import load, info

def opt(p):
    return load(p) if os.path.exists(p) else None

def esc(x):
    return html.escape(str(x))

def mdc(x):
    # markdown table/text cell: escape pipes and collapse newlines, no HTML escaping
    return str(x).replace("|", "\\|").replace("\n", " ")

def build(rd):
    g = load(f"{rd}/01_requirements.json")
    tc = load(f"{rd}/02_testcases.json")
    res = {r["case_id"]: r for r in load(f"{rd}/03_results.json")["results"]}
    ev = opt(f"{rd}/05_evaluations.json") or {"evaluations": [], "adversarial": [], "agent_traces": []}
    defects = (opt(f"{rd}/defects.json") or {"defects": []})["defects"]
    readiness = opt(f"{rd}/readiness.json") or {}
    evmap = {e["case_id"]: e for e in ev.get("evaluations", [])}

    cases_by_req = {}
    for c in tc["cases"]:
        for rid in c.get("requirement_ids", []):
            cases_by_req.setdefault(rid, []).append(c)

    # ---------- Markdown ----------
    md = [f"# Quality Report — {esc(g.get('title','Untitled'))}",
          f"\nSource PRD: `{esc(g.get('source',''))}`  ·  Generated: {esc(g.get('generated_at',''))}\n"]
    if readiness:
        md.append(f"## Release Readiness: {readiness['score']}/100 — "
                  f"**{readiness['recommendation'].upper()}**\n")
        for k, v in readiness["components"].items():
            md.append(f"- **{k}** ({int(v['weight']*100)}%): {v['value']} — {v['detail']}")
        for b in readiness.get("blocking", []):
            md.append(f"- ⛔ {b}")
        md.append("")
    md.append("## Coverage Map\n\n| Requirement | Risk | Cases | Status |\n|---|---|---|---|")
    for r in g["requirements"]:
        cs = cases_by_req.get(r["id"], [])
        statuses = [res.get(c["id"], {}).get("status", "—") for c in cs]
        agg = "no tests" if not cs else (
            "fail" if any(s in ("fail", "error") for s in statuses) else
            ("needs_eval" if "needs_eval" in statuses else "pass"))
        md.append(f"| {r['id']} {mdc(r['text'][:60])} | {r.get('risk','-')} | "
                  f"{len(cs)} | {agg} |")
    md.append(f"\n## Defects ({len(defects)})\n")
    if not defects:
        md.append("_None found within tested scope._")
    for d in defects:
        md.append(f"### {d['id']} [{d['severity'].upper()}] {mdc(d['title'])}")
        md.append(f"- Kind: {d['kind']} · Requirements: {', '.join(d['requirement_ids']) or '—'}")
        md.append(f"- Reproduce: {mdc('; '.join(map(str, d['reproduction'])))}")
        md.append(f"- Evidence: `{mdc(d['evidence'][:200])}`\n")
    if ev.get("evaluations"):
        md.append("## AI Output Evaluation (non-deterministic)\n")
        md.append("| Case | Pass rate | Score stddev |\n|---|---|---|")
        for e in ev["evaluations"]:
            c = e["consistency"]
            md.append(f"| {e['case_id']} | {c['pass_rate']} | {c['score_stddev']} |")
        md.append("")
    if ev.get("adversarial"):
        md.append("## Adversarial / OWASP LLM Top 10\n")
        md.append("| Probe | OWASP | Outcome |\n|---|---|---|")
        for adv in ev["adversarial"]:
            md.append(f"| {adv['case_id']} | {mdc(adv['owasp'])} | {adv['outcome']} |")
        md.append("")
    md.append("## What This Report Does Not Claim\n")
    md.append("Complete coverage of the **agreed scope** above — not zero post-launch "
              "defects. Untestable items are reported as untested, not hidden.")
    lim_path = f"{rd}/limitations.md"
    limitations = open(lim_path, encoding="utf-8").read().strip() if os.path.exists(lim_path) else ""
    if limitations:
        md.append("\n## Hidden Limitations\n")
        md.append(limitations)
    md_text = "\n".join(md)
    with open(f"{rd}/report.md", "w", encoding="utf-8") as f:
        f.write(md_text)

    # ---------- HTML ----------
    sev_color = {"critical": "#c0392b", "high": "#e67e22", "medium": "#d4a017", "low": "#7f8c8d"}
    rec = readiness.get("recommendation", "n/a")
    rec_color = {"ship": "#2e7d32", "ship_with_caveats": "#d4a017", "hold": "#c0392b"}.get(rec, "#555")
    rows = ""
    for r in g["requirements"]:
        cs = cases_by_req.get(r["id"], [])
        statuses = [res.get(c["id"], {}).get("status", "—") for c in cs]
        agg = "no tests" if not cs else (
            "fail" if any(s in ("fail", "error") for s in statuses) else
            ("needs_eval" if "needs_eval" in statuses else "pass"))
        badge = {"pass": "#2e7d32", "fail": "#c0392b", "needs_eval": "#d4a017",
                 "no tests": "#999"}.get(agg, "#999")
        rows += (f"<tr><td><b>{esc(r['id'])}</b> {esc(r['text'][:80])}</td>"
                 f"<td>{esc(r.get('risk','-'))}</td><td>{len(cs)}</td>"
                 f"<td><span class='badge' style='background:{badge}'>{agg}</span></td></tr>")
    defrows = "".join(
        f"<div class='defect'><h4 style='color:{sev_color[d['severity']]}'>"
        f"{esc(d['id'])} · {d['severity'].upper()} · {esc(d['title'])}</h4>"
        f"<p><b>Kind:</b> {d['kind']} &nbsp; <b>Reqs:</b> {', '.join(d['requirement_ids']) or '—'}</p>"
        f"<p><b>Reproduce:</b> {esc('; '.join(map(str, d['reproduction'])))}</p>"
        f"<pre>{esc(d['evidence'][:300])}</pre></div>" for d in defects) or "<p>None in scope.</p>"
    advrows = "".join(
        f"<tr><td>{esc(a['case_id'])}</td><td>{esc(a['owasp'])}</td>"
        f"<td style='color:{'#c0392b' if a['outcome']=='breached' else '#2e7d32'}'>"
        f"{a['outcome']}</td></tr>" for a in ev.get("adversarial", []))
    comp_rows = ""
    for k, v in readiness.get("components", {}).items():
        comp_rows += (f"<tr><td>{k}</td><td>{int(v['weight']*100)}%</td>"
                      f"<td>{v['value']}</td><td>{esc(v['detail'])}</td></tr>")

    css = ("body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:960px;"
           "margin:32px auto;padding:0 20px;color:#1a1a1a;line-height:1.5}"
           "h1{border-bottom:3px solid #111;padding-bottom:8px}"
           ".score{font-size:48px;font-weight:800}"
           ".rec{display:inline-block;padding:6px 16px;border-radius:6px;color:#fff;font-weight:700}"
           "table{border-collapse:collapse;width:100%;margin:12px 0}"
           "td,th{border:1px solid #ddd;padding:8px;text-align:left;font-size:14px}"
           "th{background:#f5f5f5}.badge{color:#fff;padding:2px 8px;border-radius:4px;font-size:12px}"
           ".defect{border-left:4px solid #c0392b;background:#fafafa;padding:8px 14px;margin:10px 0}"
           "pre{background:#f0f0f0;padding:8px;overflow:auto;font-size:12px}"
           ".muted{color:#777}")
    htmlout = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Quality Report — {esc(g.get('title','')) }</title><style>{css}</style></head><body>
<h1>Quality Report</h1>
<p class="muted">{esc(g.get('title',''))} · source <code>{esc(g.get('source',''))}</code> · {esc(g.get('generated_at',''))}</p>
<h2>Release Readiness</h2>
<p><span class="score">{readiness.get('score','—')}</span><span class="muted">/100</span>
&nbsp; <span class="rec" style="background:{rec_color}">{rec.upper()}</span></p>
<table><tr><th>Component</th><th>Weight</th><th>Value</th><th>Detail</th></tr>{comp_rows}</table>
<h2>Coverage Map</h2>
<table><tr><th>Requirement</th><th>Risk</th><th>Cases</th><th>Status</th></tr>{rows}</table>
<h2>Defects ({len(defects)})</h2>{defrows}
{"<h2>Adversarial / OWASP LLM Top 10</h2><table><tr><th>Probe</th><th>OWASP</th><th>Outcome</th></tr>"+advrows+"</table>" if advrows else ""}
<h2>What this report does not claim</h2>
<p>Complete coverage of the <b>agreed scope</b> above — not zero post-launch defects.
Untestable items are reported as untested, never hidden.</p>
{("<h2>Hidden Limitations</h2><pre style='white-space:pre-wrap'>" + esc(limitations) + "</pre>") if limitations else ""}
</body></html>"""
    with open(f"{rd}/report.html", "w", encoding="utf-8") as f:
        f.write(htmlout)
    info(f"Wrote report.html and report.md to {rd}")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("run_dir"); a = ap.parse_args()
    build(a.run_dir)

if __name__ == "__main__":
    main()
