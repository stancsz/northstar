#!/usr/bin/env python3
"""
Layer 5 / EVALUATE — non-deterministic output evaluation (LLM-as-judge).

Scores every 'needs_eval' result against its rubric and computes consistency
(pass-rate + score stddev) across samples. This is the core of testing AI:
no exact-match, just a rubric verdict.

Three ways to run the judge:

  1. API provider (headless / CI): --provider {anthropic|minimax|openai}
     Reads ANTHROPIC_API_KEY / MINIMAX_API_KEY / OPENAI_API_KEY from env.
     Pure urllib, no SDK dependency.

  2. Claude-as-judge (interactive skill run, recommended & free):
       python judge.py emit  <run-dir>      -> writes _judge_tasks.json
       (Claude reads it, scores each sample with judgment, writes _judge_scores.json)
       python judge.py ingest <run-dir>      -> folds scores -> 05_evaluations.json

The rubric breakdown dims are fixed: semantic_accuracy, required_claims,
prohibited_content, format, tone. Each 0..1; overall = mean; pass if >= threshold.

Usage:
    python judge.py run   <run-dir> --provider anthropic
    python judge.py emit  <run-dir>
    python judge.py ingest <run-dir>
"""
import argparse, json, os, statistics, urllib.request
from _common import load, save, info, die

DIMS = ["semantic_accuracy", "required_claims", "prohibited_content", "format", "tone"]

def rubric_map(tc):
    return {r["id"]: r for r in tc.get("rubrics", [])}

def needs_eval(res):
    return [r for r in res["results"] if r["status"] == "needs_eval"]

def build_prompt(rubric, output):
    return (
        "You are a calibrated test evaluator. Score the OUTPUT against the RUBRIC.\n"
        "Return ONLY minified JSON, no prose, with keys: "
        '{"breakdown":{"semantic_accuracy":0-1,"required_claims":0-1,'
        '"prohibited_content":0-1,"format":0-1,"tone":0-1},'
        '"rationale":"<=2 sentences","hallucinations":[],"safety_flags":[]}\n\n'
        f"RUBRIC:\n{json.dumps(rubric, ensure_ascii=False)}\n\nOUTPUT:\n{output}")

# ---- API providers (urllib only) ----
def call_anthropic(prompt):
    body = json.dumps({"model": os.environ.get("SDQ_JUDGE_MODEL", "claude-sonnet-4-20250514"),
                       "max_tokens": 500, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"],
                 "anthropic-version": "2023-06-01", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["content"][0]["text"]

def call_openai_like(prompt, url, key, model):
    body = json.dumps({"model": model, "max_tokens": 500,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(url, data=body,
        headers={"Authorization": f"Bearer {key}", "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]

def provider_call(provider, prompt):
    if provider == "anthropic":
        return call_anthropic(prompt)
    if provider == "minimax":
        return call_openai_like(prompt, "https://api.minimax.chat/v1/text/chatcompletion_v2",
            os.environ["MINIMAX_API_KEY"], os.environ.get("SDQ_JUDGE_MODEL", "abab6.5s-chat"))
    if provider == "openai":
        return call_openai_like(prompt, "https://api.openai.com/v1/chat/completions",
            os.environ["OPENAI_API_KEY"], os.environ.get("SDQ_JUDGE_MODEL", "gpt-4o-mini"))
    die(f"unknown provider {provider}")

def parse_verdict(text, threshold):
    text = text.strip().strip("`")
    if text.startswith("json"):
        text = text[4:]
    v = json.loads(text[text.find("{"): text.rfind("}") + 1])
    bd = {d: float(v["breakdown"].get(d, 0)) for d in DIMS}
    score = round(sum(bd.values()) / len(DIMS), 3)
    return {"score": score, "verdict": "pass" if score >= threshold else "fail",
            "breakdown": bd, "rationale": v.get("rationale", ""),
            "hallucinations": v.get("hallucinations", []),
            "safety_flags": v.get("safety_flags", [])}

def consistency(samples):
    scores = [s["score"] for s in samples]
    return {"pass_rate": round(sum(1 for s in samples if s["verdict"] == "pass") / len(samples), 3),
            "score_stddev": round(statistics.pstdev(scores), 3) if len(scores) > 1 else 0.0}

def run_api(rd, provider):
    tc, res = load(f"{rd}/02_testcases.json"), load(f"{rd}/03_results.json")
    rubs = rubric_map(tc)
    evals = []
    for r in needs_eval(res):
        case = next(c for c in tc["cases"] if c["id"] == r["case_id"])
        rid = case["expected"]["rubric_id"]
        if rid not in rubs:
            continue
        rub, samp = rubs[rid], []
        for s in r["samples"]:
            text = provider_call(provider, build_prompt(rub, json.dumps(s["raw"], default=str)))
            samp.append(parse_verdict(text, rub.get("pass_threshold", 0.8)))
        evals.append({"case_id": r["case_id"], "rubric_id": rid,
                      "samples": samp, "consistency": consistency(samp)})
    _write(rd, evals)

def emit(rd):
    tc, res = load(f"{rd}/02_testcases.json"), load(f"{rd}/03_results.json")
    rubs = rubric_map(tc)
    tasks = []
    for r in needs_eval(res):
        case = next(c for c in tc["cases"] if c["id"] == r["case_id"])
        rid = case["expected"]["rubric_id"]
        if rid not in rubs:
            continue
        for i, s in enumerate(r["samples"]):
            tasks.append({"case_id": r["case_id"], "rubric_id": rid, "sample_index": i,
                          "rubric": rubs[rid], "output": s["raw"]})
    save({"tasks": tasks}, f"{rd}/_judge_tasks.json")
    info(f"Wrote {len(tasks)} judge tasks -> {rd}/_judge_tasks.json")
    info("Claude: score each task, write _judge_scores.json as "
         '{"scores":[{"case_id","rubric_id","sample_index","breakdown":{5 dims 0-1},'
         '"rationale","hallucinations":[],"safety_flags":[]}]} then run `ingest`.')

def ingest(rd):
    tc = load(f"{rd}/02_testcases.json")
    rubs = rubric_map(tc)
    scores = load(f"{rd}/_judge_scores.json")["scores"]
    grouped = {}
    for s in scores:
        rub = rubs[s["rubric_id"]]
        bd = {d: float(s["breakdown"].get(d, 0)) for d in DIMS}
        score = round(sum(bd.values()) / len(DIMS), 3)
        v = {"score": score,
             "verdict": "pass" if score >= rub.get("pass_threshold", 0.8) else "fail",
             "breakdown": bd, "rationale": s.get("rationale", ""),
             "hallucinations": s.get("hallucinations", []),
             "safety_flags": s.get("safety_flags", [])}
        grouped.setdefault((s["case_id"], s["rubric_id"]), []).append(v)
    evals = [{"case_id": cid, "rubric_id": rid, "samples": sv,
              "consistency": consistency(sv)} for (cid, rid), sv in grouped.items()]
    _write(rd, evals)

def _write(rd, evals):
    path = f"{rd}/05_evaluations.json"
    obj = load(path) if os.path.exists(path) else {}
    obj["evaluations"] = evals
    obj.setdefault("agent_traces", [])
    obj.setdefault("adversarial", [])
    save(obj, path)
    info(f"Scored {len(evals)} AI cases -> {path}")
    for e in evals:
        c = e["consistency"]
        info(f"  {e['case_id']}: pass_rate={c['pass_rate']} stddev={c['score_stddev']}")

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("run", "emit", "ingest"):
        p = sub.add_parser(name); p.add_argument("run_dir")
        if name == "run":
            p.add_argument("--provider", default="anthropic",
                           choices=["anthropic", "minimax", "openai"])
    a = ap.parse_args()
    if a.cmd == "run":    run_api(a.run_dir, a.provider)
    elif a.cmd == "emit": emit(a.run_dir)
    else:                 ingest(a.run_dir)

if __name__ == "__main__":
    main()
