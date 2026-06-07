#!/usr/bin/env python3
"""
Layer 6 / REPORT & COMPLY — assemble the human-readable report from every
artifact: requirement-mapped coverage, defect log with reproduction, AI
evaluation + consistency, adversarial results, compliance, and the release
readiness scorecard. Writes report.html and report.md.

Supports localized report rendering via `--lang <en|zh>` (or $SDQ_LANG).
Default is English. Chinese (`zh`) is useful for audits against Chinese
national standards (e.g. GB/T 25000.51-2016). Clause text and standard
names come from the source document and are passed through unchanged.

Usage:
    python make_report.py <run-dir> [--lang en|zh]
    SDQ_LANG=zh python make_report.py <run-dir>
"""
import argparse, html, os
from _common import load, info

# ---------- i18n strings ----------
# Translatable UI strings used by the renderer. Add a new language by adding
# a column. Values must match the keys used in the t() helper below.
STRINGS = {
    "en": {
        "title": "Quality Report",
        "source_label": "Source",
        "generated_label": "Generated",
        "release_readiness_h2": "Release Readiness",
        "release_readiness_md": "Release Readiness",
        "coverage_map": "Coverage Map",
        "conformance_matrix": "Conformance Matrix",
        "standard_label": "Standard",
        "clauses_count": "{n} clauses, {m} normative sentences",
        "defects": "Defects",
        "none_in_scope": "_None found within tested scope._",
        "none_in_scope_html": "None in scope.",
        "ai_eval": "AI Output Evaluation (non-deterministic)",
        "adversarial": "Adversarial / OWASP LLM Top 10",
        "component_coverage": "coverage",
        "component_defects": "defects",
        "component_stability": "stability",
        "component_compliance": "compliance",
        "what_not_claim_md": "What This Report Does Not Claim",
        "what_not_claim_html": "What this report does not claim",
        "what_not_claim_body": ("Complete coverage of the **agreed scope** above — not zero post-launch "
                                "defects. Untestable items are reported as untested, not hidden."),
        "what_not_claim_body_html": ("Complete coverage of the <b>agreed scope</b> above — not zero "
                                     "post-launch defects. Untestable items are reported as untested, "
                                     "never hidden."),
        "hidden_limitations": "Hidden Limitations",
        # column headers
        "col_requirement": "Requirement",
        "col_risk": "Risk",
        "col_cases": "Cases",
        "col_status": "Status",
        "col_clause": "Clause",
        "col_standard": "Standard",
        "col_title": "Title",
        "col_evidence": "Evidence",
        "col_component": "Component",
        "col_weight": "Weight",
        "col_value": "Value",
        "col_detail": "Detail",
        "col_probe": "Probe",
        "col_owasp": "OWASP",
        "col_outcome": "Outcome",
        "col_case": "Case",
        "col_pass_rate": "Pass rate",
        "col_score_stddev": "Score stddev",
        # defect fields
        "field_kind": "Kind",
        "field_reqs": "Reqs",
        "field_reproduce": "Reproduce",
        "field_evidence": "Evidence",
        # evidence messages
        "evidence_static_passed": "static check passed",
        "evidence_runtime_skipped": "runtime / not exercised by static check",
    },
    "zh": {
        "title": "质量报告",
        "source_label": "来源",
        "generated_label": "生成时间",
        "release_readiness_h2": "发布就绪度",
        "release_readiness_md": "发布就绪度",
        "coverage_map": "覆盖率图",
        "conformance_matrix": "符合性矩阵",
        "standard_label": "标准",
        "clauses_count": "{n} 个条款, {m} 个规范性句子",
        "defects": "缺陷",
        "none_in_scope": "_测试范围内未发现缺陷。_",
        "none_in_scope_html": "测试范围内未发现缺陷。",
        "ai_eval": "AI 输出评估 (非确定性)",
        "adversarial": "对抗测试 / OWASP LLM Top 10",
        "component_coverage": "覆盖率",
        "component_defects": "缺陷",
        "component_stability": "稳定性",
        "component_compliance": "符合性",
        "what_not_claim_md": "本报告未声明的内容",
        "what_not_claim_html": "本报告未声明的内容",
        "what_not_claim_body": ("对上述**约定范围**的完整覆盖 — 而非零发布后缺陷。"
                                "无法测试的项目被如实报告为未测试,而非隐藏。"),
        "what_not_claim_body_html": ("对上述<b>约定范围</b>的完整覆盖 — 而非零发布后缺陷。"
                                     "无法测试的项目被如实报告为未测试,而非隐藏。"),
        "hidden_limitations": "隐藏的局限性",
        "col_requirement": "需求",
        "col_risk": "风险",
        "col_cases": "用例数",
        "col_status": "状态",
        "col_clause": "条款",
        "col_standard": "标准",
        "col_title": "标题",
        "col_evidence": "证据",
        "col_component": "组件",
        "col_weight": "权重",
        "col_value": "值",
        "col_detail": "详情",
        "col_probe": "探针",
        "col_owasp": "OWASP",
        "col_outcome": "结果",
        "col_case": "用例",
        "col_pass_rate": "通过率",
        "col_score_stddev": "分数标准差",
        "field_kind": "类型",
        "field_reqs": "需求",
        "field_reproduce": "复现",
        "field_evidence": "证据",
        "evidence_static_passed": "静态检查通过",
        "evidence_runtime_skipped": "运行时要求 / 静态检查未覆盖",
    },
}

# Translate data values (status / severity / recommendation) for display.
# The JSON artifacts keep English values; the report shows the localized label.
LABELS = {
    "en": {
        "status": {"pass": "pass", "fail": "fail", "skipped": "skipped",
                   "needs_eval": "needs_eval", "no tests": "no tests", "error": "error"},
        "severity": {"critical": "critical", "high": "high", "medium": "medium", "low": "low"},
        "recommendation": {"ship": "ship", "ship_with_caveats": "ship with caveats", "hold": "hold"},
    },
    "zh": {
        "status": {"pass": "通过", "fail": "失败", "skipped": "跳过",
                   "needs_eval": "需评估", "no tests": "无测试", "error": "错误"},
        "severity": {"critical": "严重", "high": "高", "medium": "中", "low": "低"},
        "recommendation": {"ship": "发布", "ship_with_caveats": "带保留意见发布", "hold": "暂不发布"},
    },
}

def t(key, lang="en"):
    """Look up a UI string. Falls back to English if a key is missing in `lang`."""
    return STRINGS.get(lang, STRINGS["en"]).get(key, STRINGS["en"].get(key, key))

def lbl(kind, value, lang="en"):
    """Look up a status/severity/recommendation label, falling back to the raw value."""
    return LABELS.get(lang, LABELS["en"]).get(kind, {}).get(value, value)

def opt(p):
    return load(p) if os.path.exists(p) else None

def esc(x):
    return html.escape(str(x))

def mdc(x):
    # markdown table/text cell: escape pipes and collapse newlines, no HTML escaping
    return str(x).replace("|", "\\|").replace("\n", " ")

def build(rd, lang="en"):
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
    md = [f"# {t('title', lang)} — {esc(g.get('title','Untitled'))}",
          f"\n{t('source_label', lang)}: `{esc(g.get('source',''))}`  ·  "
          f"{t('generated_label', lang)}: {esc(g.get('generated_at',''))}\n"]
    if readiness:
        rec_label = lbl("recommendation", readiness.get("recommendation", "hold"), lang)
        md.append(f"## {t('release_readiness_md', lang)}: {readiness['score']}/100 — "
                  f"**{rec_label}**\n")
        for k, v in readiness["components"].items():
            label = t(f"component_{k}", lang) if k in ("coverage", "defects", "stability", "compliance") else k
            md.append(f"- **{label}** ({int(v['weight']*100)}%): {v['value']} — {v['detail']}")
        for b in readiness.get("blocking", []):
            md.append(f"- ⛔ {b}")
        md.append("")
    md.append(f"## {t('coverage_map', lang)}\n\n| {t('col_requirement', lang)} | "
              f"{t('col_risk', lang)} | {t('col_cases', lang)} | {t('col_status', lang)} |"
              f"\n|---|---|---|---|")
    for r in g["requirements"]:
        cs = cases_by_req.get(r["id"], [])
        statuses = [res.get(c["id"], {}).get("status", "—") for c in cs]
        raw_agg = "no tests" if not cs else (
            "fail" if any(s in ("fail", "error") for s in statuses) else
            ("needs_eval" if "needs_eval" in statuses else "pass"))
        agg = lbl("status", raw_agg, lang)
        md.append(f"| {r['id']} {mdc(r['text'][:60])} | {r.get('risk','-')} | "
                  f"{len(cs)} | {agg} |")

    # ---------- Conformance Matrix (Standards Conformance mode) ----------
    conf_reqs = [r for r in g["requirements"] if r.get("type") == "conformance_criterion"]
    if conf_reqs:
        md.append(f"\n## {t('conformance_matrix', lang)}\n")
        std = opt(f"{rd}/standards_index.json") or {}
        if std.get("standard_id"):
            md.append(f"**{t('standard_label', lang)}:** {mdc(std['standard_id'])}")
            if std.get("standard_name"):
                md.append(f" · {mdc(std['standard_name'])}")
            md.append(" · " + t("clauses_count", lang).format(
                n=std.get('clause_count', '?'),
                m=std.get('normative_sentence_count', '?')) + "\n")
        md.append(f"\n| {t('col_clause', lang)} | {t('col_standard', lang)} | "
                  f"{t('col_title', lang)} | {t('col_status', lang)} | "
                  f"{t('col_evidence', lang)} |\n|---|---|---|---|---|")
        for r in conf_reqs:
            cs = cases_by_req.get(r["id"], [])
            statuses = [res.get(c["id"], {}).get("status", "—") for c in cs]
            raw_agg = "no tests" if not cs else (
                "fail" if any(s in ("fail", "error") for s in statuses) else
                ("skipped" if statuses and all(s == "skipped" for s in statuses) else
                 ("needs_eval" if "needs_eval" in statuses else "pass")))
            agg = lbl("status", raw_agg, lang)
            # Evidence: first failed case's first match OR a one-line summary
            evidence = "—"
            failed = [c for c in cs if res.get(c["id"], {}).get("status") in ("fail", "error")]
            passed = [c for c in cs if res.get(c["id"], {}).get("status") == "pass"]
            if failed:
                ev_detail = res.get(failed[0]["id"], {}).get("assertion_detail", "")
                evidence = mdc(ev_detail[:80])
            elif passed and raw_agg == "pass":
                ev_detail = res.get(passed[0]["id"], {}).get("assertion_detail", "")
                evidence = mdc(ev_detail[:80]) or t("evidence_static_passed", lang)
            elif raw_agg == "skipped":
                evidence = t("evidence_runtime_skipped", lang)
            md.append(f"| {mdc(r.get('clause','-'))} | {mdc(r.get('standard_id','-'))} | "
                      f"{mdc(r['text'][:50])} | {agg} | {evidence} |")
    md.append(f"\n## {t('defects', lang)} ({len(defects)})\n")
    if not defects:
        md.append(t("none_in_scope", lang))
    for d in defects:
        sev = lbl("severity", d['severity'], lang)
        md.append(f"### {d['id']} [{sev}] {mdc(d['title'])}")
        md.append(f"- {t('field_kind', lang)}: {d['kind']} · "
                  f"{t('field_reqs', lang)}: {', '.join(d['requirement_ids']) or '—'}")
        md.append(f"- {t('field_reproduce', lang)}: {mdc('; '.join(map(str, d['reproduction'])))}")
        md.append(f"- {t('field_evidence', lang)}: `{mdc(d['evidence'][:200])}`\n")
    if ev.get("evaluations"):
        md.append(f"## {t('ai_eval', lang)}\n")
        md.append(f"| {t('col_case', lang)} | {t('col_pass_rate', lang)} | "
                  f"{t('col_score_stddev', lang)} |\n|---|---|---|")
        for e in ev["evaluations"]:
            c = e["consistency"]
            md.append(f"| {e['case_id']} | {c['pass_rate']} | {c['score_stddev']} |")
        md.append("")
    if ev.get("adversarial"):
        md.append(f"## {t('adversarial', lang)}\n")
        md.append(f"| {t('col_probe', lang)} | {t('col_owasp', lang)} | "
                  f"{t('col_outcome', lang)} |\n|---|---|---|")
        for adv in ev["adversarial"]:
            outcome = lbl("status", adv['outcome'], lang) if adv['outcome'] in ('defended', 'breached', 'partial') else adv['outcome']
            md.append(f"| {adv['case_id']} | {mdc(adv['owasp'])} | {outcome} |")
        md.append("")
    md.append(f"## {t('what_not_claim_md', lang)}\n")
    md.append(t("what_not_claim_body", lang))
    lim_path = f"{rd}/limitations.md"
    limitations = open(lim_path, encoding="utf-8").read().strip() if os.path.exists(lim_path) else ""
    if limitations:
        md.append(f"\n## {t('hidden_limitations', lang)}\n")
        md.append(limitations)
    md_text = "\n".join(md)
    with open(f"{rd}/report.md", "w", encoding="utf-8") as f:
        f.write(md_text)

    # ---------- HTML ----------
    sev_color = {"critical": "#c0392b", "high": "#e67e22", "medium": "#d4a017", "low": "#7f8c8d"}
    rec = readiness.get("recommendation", "n/a")
    rec_label = lbl("recommendation", rec, lang)
    rec_color = {"ship": "#2e7d32", "ship_with_caveats": "#d4a017", "hold": "#c0392b"}.get(rec, "#555")
    rows = ""
    for r in g["requirements"]:
        cs = cases_by_req.get(r["id"], [])
        statuses = [res.get(c["id"], {}).get("status", "—") for c in cs]
        raw_agg = "no tests" if not cs else (
            "fail" if any(s in ("fail", "error") for s in statuses) else
            ("needs_eval" if "needs_eval" in statuses else "pass"))
        agg = lbl("status", raw_agg, lang)
        badge = {"pass": "#2e7d32", "fail": "#c0392b", "needs_eval": "#d4a017",
                 "no tests": "#999"}.get(raw_agg, "#999")
        rows += (f"<tr><td><b>{esc(r['id'])}</b> {esc(r['text'][:80])}</td>"
                 f"<td>{esc(r.get('risk','-'))}</td><td>{len(cs)}</td>"
                 f"<td><span class='badge' style='background:{badge}'>{agg}</span></td></tr>")
    defrows = "".join(
        f"<div class='defect'><h4 style='color:{sev_color[d['severity']]}'>"
        f"{esc(d['id'])} · {lbl('severity', d['severity'], lang)} · {esc(d['title'])}</h4>"
        f"<p><b>{t('field_kind', lang)}:</b> {d['kind']} &nbsp; "
        f"<b>{t('field_reqs', lang)}:</b> {', '.join(d['requirement_ids']) or '—'}</p>"
        f"<p><b>{t('field_reproduce', lang)}:</b> "
        f"{esc('; '.join(map(str, d['reproduction'])))}</p>"
        f"<pre>{esc(d['evidence'][:300])}</pre></div>" for d in defects) or f"<p>{t('none_in_scope_html', lang)}</p>"
    advrows = "".join(
        f"<tr><td>{esc(a['case_id'])}</td><td>{esc(a['owasp'])}</td>"
        f"<td style='color:{'#c0392b' if a['outcome']=='breached' else '#2e7d32'}'>"
        f"{esc(a['outcome'])}</td></tr>" for a in ev.get("adversarial", []))
    comp_rows = ""
    for k, v in readiness.get("components", {}).items():
        label = t(f"component_{k}", lang) if k in ("coverage", "defects", "stability", "compliance") else k
        comp_rows += (f"<tr><td>{esc(label)}</td><td>{int(v['weight']*100)}%</td>"
                      f"<td>{v['value']}</td><td>{esc(v['detail'])}</td></tr>")
    # Conformance Matrix (Standards Conformance mode) — same loop body as MD,
    # but rendered as HTML rows. Built only if there are conformance reqs.
    conf_html = ""
    conf_reqs_html = [r for r in g["requirements"] if r.get("type") == "conformance_criterion"]
    if conf_reqs_html:
        std = opt(f"{rd}/standards_index.json") or {}
        std_hdr = ""
        if std.get("standard_id"):
            std_hdr = (f"<p><b>{t('standard_label', lang)}:</b> {esc(std['standard_id'])}"
                       + (f" · {esc(std['standard_name'])}" if std.get("standard_name") else "")
                       + " · " + esc(t("clauses_count", lang).format(
                             n=std.get('clause_count', '?'),
                             m=std.get('normative_sentence_count', '?'))) + "</p>")
        conf_rows = ""
        for r in conf_reqs_html:
            cs = cases_by_req.get(r["id"], [])
            statuses = [res.get(c["id"], {}).get("status", "—") for c in cs]
            raw_agg = "no tests" if not cs else (
                "fail" if any(s in ("fail", "error") for s in statuses) else
                ("skipped" if statuses and all(s == "skipped" for s in statuses) else
                 ("needs_eval" if "needs_eval" in statuses else "pass")))
            agg = lbl("status", raw_agg, lang)
            evidence = "—"
            failed = [c for c in cs if res.get(c["id"], {}).get("status") in ("fail", "error")]
            passed = [c for c in cs if res.get(c["id"], {}).get("status") == "pass"]
            if failed:
                evidence = esc(res.get(failed[0]["id"], {}).get("assertion_detail", "")[:80])
            elif passed and raw_agg == "pass":
                evidence = esc(res.get(passed[0]["id"], {}).get("assertion_detail", "")[:80]) or t("evidence_static_passed", lang)
            elif raw_agg == "skipped":
                evidence = t("evidence_runtime_skipped", lang)
            badge = {"pass": "#2e7d32", "fail": "#c0392b", "needs_eval": "#d4a017",
                     "skipped": "#7f8c8d", "no tests": "#999"}.get(raw_agg, "#999")
            conf_rows += (f"<tr><td><code>{esc(r.get('clause','-'))}</code></td>"
                          f"<td>{esc(r.get('standard_id','-'))}</td>"
                          f"<td>{esc(r['text'][:60])}</td>"
                          f"<td><span class='badge' style='background:{badge}'>{agg}</span></td>"
                          f"<td>{evidence}</td></tr>")
        conf_html = (f"<h2>{t('conformance_matrix', lang)}</h2>{std_hdr}"
                     f"<table><tr><th>{t('col_clause', lang)}</th>"
                     f"<th>{t('col_standard', lang)}</th>"
                     f"<th>{t('col_title', lang)}</th>"
                     f"<th>{t('col_status', lang)}</th>"
                     f"<th>{t('col_evidence', lang)}</th></tr>{conf_rows}</table>")

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
<title>{t('title', lang)} — {esc(g.get('title','')) }</title><style>{css}</style></head><body>
<h1>{t('title', lang)}</h1>
<p class="muted">{esc(g.get('title',''))} · {t('source_label', lang)} <code>{esc(g.get('source',''))}</code> · {t('generated_label', lang)}: {esc(g.get('generated_at',''))}</p>
<h2>{t('release_readiness_h2', lang)}</h2>
<p><span class="score">{readiness.get('score','—')}</span><span class="muted">/100</span>
&nbsp; <span class="rec" style="background:{rec_color}">{rec_label}</span></p>
<table><tr><th>{t('col_component', lang)}</th><th>{t('col_weight', lang)}</th><th>{t('col_value', lang)}</th><th>{t('col_detail', lang)}</th></tr>{comp_rows}</table>
<h2>{t('coverage_map', lang)}</h2>
<table><tr><th>{t('col_requirement', lang)}</th><th>{t('col_risk', lang)}</th><th>{t('col_cases', lang)}</th><th>{t('col_status', lang)}</th></tr>{rows}</table>
{conf_html}
<h2>{t('defects', lang)} ({len(defects)})</h2>{defrows}
{"<h2>"+t('adversarial', lang)+"</h2><table><tr><th>"+t('col_probe', lang)+"</th><th>"+t('col_owasp', lang)+"</th><th>"+t('col_outcome', lang)+"</th></tr>"+advrows+"</table>" if advrows else ""}
<h2>{t('what_not_claim_html', lang)}</h2>
<p>{t('what_not_claim_body_html', lang)}</p>
{("<h2>"+t('hidden_limitations', lang)+"</h2><pre style='white-space:pre-wrap'>" + esc(limitations) + "</pre>") if limitations else ""}
</body></html>"""
    with open(f"{rd}/report.html", "w", encoding="utf-8") as f:
        f.write(htmlout)
    info(f"Wrote report.html and report.md to {rd} (lang={lang})")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--lang", default=None,
                    help="report language: en (default) or zh. "
                         "Falls back to $SDQ_LANG. English chrome when unset.")
    a = ap.parse_args()
    lang = a.lang or os.environ.get("SDQ_LANG") or "en"
    if lang not in STRINGS:
        info(f"Unknown language {lang!r}; supported: {list(STRINGS)}. Falling back to English.")
        lang = "en"
    build(a.run_dir, lang=lang)

if __name__ == "__main__":
    main()
