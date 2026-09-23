#!/usr/bin/env python3
"""Classify a task intake into a conservative Northstar collaboration contract."""
import argparse
import json
from pathlib import Path

MODES = ("AUTO", "GUARD", "COCREATE", "CHALLENGE", "HUMAN_ONLY")
HIGH_RISK_FLAGS = (
    "irreversible", "production_or_system_of_record", "money", "permissions",
    "privacy", "security", "compliance", "external_representation",
    "outside_isolated_sandbox", "cannot_simulate_before_commit",
)
HIGH_COMPLEXITY_FLAGS = (
    "ambiguous_goal", "ambiguous_acceptance", "novel_condition", "multiple_dependencies",
    "implicit_context_or_value_judgment", "hard_to_verify", "reasonable_expert_disagreement",
)
HUMAN_DECISION_FLAGS = (
    "ambiguous_goal", "ambiguous_acceptance", "implicit_context_or_value_judgment",
    "reasonable_expert_disagreement",
)

AUTHORITY = {
    "AUTO": {"intent": "human", "initiative": "ai", "execution": "ai", "acceptance": "verifier", "commit": "automatic_reversible"},
    "GUARD": {"intent": "human", "initiative": "ai", "execution": "ai", "acceptance": "human_and_verifier", "commit": "human_approval"},
    "COCREATE": {"intent": "human", "initiative": "shared", "execution": "shared", "acceptance": "human", "commit": "human_only"},
    "CHALLENGE": {"intent": "human", "initiative": "human", "execution": "ai_analysis_human_decision", "acceptance": "human_or_independent_review", "commit": "human_only"},
    "HUMAN_ONLY": {"intent": "human", "initiative": "human", "execution": "human", "acceptance": "human", "commit": "human_only"},
}

def selected(flags, names):
    return [name for name in names if flags.get(name) is True]

def classify(data):
    risk = data.get("risk", {})
    complexity = data.get("complexity", {})
    veto = data.get("human_only", {})
    veto_reasons = [key for key, value in veto.items() if value is True]
    risk_reasons = selected(risk, HIGH_RISK_FLAGS)
    complexity_reasons = selected(complexity, HIGH_COMPLEXITY_FLAGS)
    human_decision_reasons = selected(complexity, HUMAN_DECISION_FLAGS)
    missing = not isinstance(risk, dict) or not isinstance(complexity, dict) or not risk or not complexity
    high_risk = bool(risk_reasons) or missing
    high_complexity = len(complexity_reasons) >= 2 or missing
    if veto_reasons:
        mode = "HUMAN_ONLY"
    elif missing:
        mode = "CHALLENGE"
    elif high_risk and human_decision_reasons:
        mode = "CHALLENGE"
    elif high_risk:
        mode = "GUARD"
    elif human_decision_reasons:
        mode = "COCREATE"
    else:
        mode = "AUTO"
    return mode, risk_reasons or (["missing_classification_evidence"] if missing else []), complexity_reasons or (["missing_classification_evidence"] if missing else []), veto_reasons

def contract(data):
    mode, risk_reasons, complexity_reasons, veto_reasons = classify(data)
    rollback = bool(data.get("rollback_available", False))
    return {"collaboration": {
        "mode": mode,
        "classification": {"risk": "high" if risk_reasons else "low", "risk_reasons": risk_reasons, "complexity": "high" if complexity_reasons else "low", "complexity_reasons": complexity_reasons, "confidence_in_classification": "low" if "missing_classification_evidence" in risk_reasons else "high", "human_only_reasons": veto_reasons},
        "authority": AUTHORITY[mode],
        "bounds": {"scope": data.get("task", ""), "permissions": data.get("permissions", []), "prohibited_actions": data.get("prohibited_actions", []), "data_access": data.get("data_access", []), "token_budget": data.get("token_budget", 0), "monetary_budget": data.get("monetary_budget", 0), "max_retries": data.get("max_retries", 0)},
        "evidence_required": data.get("evidence_required", ["tests", "diff", "logs"]),
        "human_checkpoint": {"type": "human.approve_commit"} if mode == "GUARD" else None,
        "escalation": {"triggers": ["verifier_failure", "novel_condition", "scope_expansion", "permission_expansion", "budget_exceeded", "unresolved_disagreement", "irreversible_side_effect", "security_or_privacy_concern"], "target_mode": "GUARD" if mode == "AUTO" else "CHALLENGE", "on_human_timeout": "stop_and_preserve_state"},
        "rollback": {"available": rollback, "procedure": data.get("rollback_procedure", ""), "recovery_point": data.get("recovery_point", "")},
        "audit": {"decision_log": True, "override_reason_required": True, "artifacts": []},
    }}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    args.output.write_text(json.dumps(contract(data), indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
