#!/usr/bin/env python3
"""Validate safety invariants in a Northstar collaboration contract."""
import argparse
import json
import sys
from pathlib import Path

HUMAN_DECISION_FLAGS = {
    "ambiguous_goal", "ambiguous_acceptance", "implicit_context_or_value_judgment",
    "reasonable_expert_disagreement",
}

def expected_mode(classification):
    risk = classification.get("risk")
    risk_reasons = classification.get("risk_reasons", [])
    complexity_reasons = classification.get("complexity_reasons", [])
    if "missing_classification_evidence" in risk_reasons or "missing_classification_evidence" in complexity_reasons:
        return "CHALLENGE"
    unresolved_human_decision = bool(HUMAN_DECISION_FLAGS.intersection(complexity_reasons))
    if risk == "high" and unresolved_human_decision:
        return "CHALLENGE"
    if risk == "high":
        return "GUARD"
    if unresolved_human_decision:
        return "COCREATE"
    return "AUTO"

def validate(document):
    errors = []
    c = document.get("collaboration")
    if not isinstance(c, dict): return ["missing collaboration object"]
    mode, authority = c.get("mode"), c.get("authority", {})
    if mode not in {"AUTO", "GUARD", "COCREATE", "CHALLENGE", "HUMAN_ONLY"}: errors.append("invalid mode")
    classification = c.get("classification", {})
    risk, complexity = classification.get("risk"), classification.get("complexity")
    if risk not in {"low", "high"} or complexity not in {"low", "high"}:
        errors.append("classification must contain low or high risk and complexity")
    elif mode != "HUMAN_ONLY" and mode != expected_mode(classification):
        errors.append("mode does not match risk and complexity classification")
    if mode == "HUMAN_ONLY" and not classification.get("human_only_reasons"):
        errors.append("HUMAN_ONLY requires a recorded veto reason")
    for key in ("intent", "initiative", "execution", "acceptance", "commit"):
        if key not in authority: errors.append(f"missing authority.{key}")
    if not c.get("evidence_required"): errors.append("evidence_required must not be empty")
    escalation = c.get("escalation", {})
    if escalation.get("on_human_timeout") != "stop_and_preserve_state": errors.append("human timeout must stop and preserve state")
    if not escalation.get("triggers"): errors.append("missing escalation triggers")
    rollback = c.get("rollback", {})
    if not rollback.get("available") or not rollback.get("procedure") or not rollback.get("recovery_point"): errors.append("rollback must be available with procedure and recovery point")
    if authority.get("commit") == "approval_by_silence": errors.append("approval by silence is prohibited")
    if risk == "high" and authority.get("commit") == "automatic_reversible": errors.append("high-risk work cannot commit automatically")
    if mode in {"GUARD", "CHALLENGE"} and authority.get("commit") not in {"human_approval", "human_only"}: errors.append(f"{mode} requires explicit human commit")
    if mode == "GUARD" and c.get("human_checkpoint", {}).get("type") != "human.approve_commit": errors.append("GUARD requires human.approve_commit checkpoint")
    if mode == "HUMAN_ONLY" and any(authority.get(k) != "human" for k in ("intent", "initiative", "execution", "acceptance")): errors.append("HUMAN_ONLY reserves all authority to human")
    if mode == "AUTO" and authority.get("acceptance") != "verifier": errors.append("AUTO acceptance must be independent verifier")
    if mode == "AUTO" and authority.get("commit") != "automatic_reversible": errors.append("AUTO commit must remain automatic and reversible")
    if mode == "COCREATE" and (authority.get("acceptance") != "human" or authority.get("commit") != "human_only"):
        errors.append("COCREATE preserves human acceptance and commit")
    if mode == "CHALLENGE" and authority.get("initiative") != "human": errors.append("CHALLENGE preserves human initiative")
    if c.get("parent_bounds"):
        child, parent = c.get("bounds", {}), c["parent_bounds"]
        for key in ("permissions", "data_access"):
            if not set(child.get(key, [])).issubset(parent.get(key, [])): errors.append(f"child expands parent {key}")
        if not set(parent.get("prohibited_actions", [])).issubset(child.get("prohibited_actions", [])):
            errors.append("child weakens parent prohibited_actions")
        for key in ("token_budget", "monetary_budget"):
            if child.get(key, 0) > parent.get(key, 0): errors.append(f"child exceeds parent {key}")
    return errors

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--input", required=True, type=Path); args = parser.parse_args()
    errors = validate(json.loads(args.input.read_text(encoding="utf-8")))
    if errors:
        print("INVALID:"); print("\n".join(f"- {error}" for error in errors)); sys.exit(1)
    print("VALID")

if __name__ == "__main__": main()
