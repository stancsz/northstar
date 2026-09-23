import importlib.util
import json
import subprocess
import tempfile
import zipfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

route = load("northstar_route")
validator = load("validate_contract")

class NorthstarRouteTests(unittest.TestCase):
    def intake(self, risk=None, complexity=None, **extra):
        return {"task": "test", "risk": risk or {}, "complexity": complexity or {}, "rollback_available": True, "rollback_procedure": "revert", "recovery_point": "abc", **extra}

    def valid(self, data):
        return validator.validate(route.contract(data))

    def test_auto_low_risk_low_complexity(self):
        c = route.contract(self.intake({"production_or_system_of_record": False}, {"ambiguous_goal": False}))
        self.assertEqual(c["collaboration"]["mode"], "AUTO")
        self.assertEqual(self.valid(self.intake({"production_or_system_of_record": False}, {"ambiguous_goal": False})), [])

    def test_guard_high_risk(self):
        c = route.contract(self.intake({"production_or_system_of_record": True}, {"ambiguous_goal": False}))
        self.assertEqual(c["collaboration"]["mode"], "GUARD")
        self.assertEqual(c["collaboration"]["human_checkpoint"]["type"], "human.approve_commit")

    def test_cocreate_high_complexity(self):
        c = route.contract(self.intake({"production_or_system_of_record": False}, {"ambiguous_goal": True, "hard_to_verify": True}))
        self.assertEqual(c["collaboration"]["mode"], "COCREATE")

    def test_challenge_high_both(self):
        c = route.contract(self.intake({"privacy": True}, {"ambiguous_goal": True, "hard_to_verify": True}))
        self.assertEqual(c["collaboration"]["mode"], "CHALLENGE")

    def test_human_only_veto(self):
        c = route.contract(self.intake({}, {}, human_only={"authentic_personal_expression": True}))
        self.assertEqual(c["collaboration"]["mode"], "HUMAN_ONLY")
        self.assertEqual(c["collaboration"]["authority"]["execution"], "human")

    def test_missing_evidence_escalates(self):
        c = route.contract({"task": "unknown", "rollback_available": True, "rollback_procedure": "revert", "recovery_point": "abc"})
        self.assertEqual(c["collaboration"]["mode"], "CHALLENGE")

    def test_rejects_approval_by_silence(self):
        c = route.contract(self.intake({"money": True}, {"ambiguous_goal": False}))
        c["collaboration"]["authority"]["commit"] = "approval_by_silence"
        self.assertIn("approval by silence is prohibited", validator.validate(c))

    def test_rejects_parent_permission_expansion(self):
        c = route.contract(self.intake({"production_or_system_of_record": False}, {"ambiguous_goal": False}, permissions=["write"]))
        c["collaboration"]["parent_bounds"] = {"permissions": ["read"], "data_access": [], "token_budget": 1, "monetary_budget": 0}
        self.assertIn("child expands parent permissions", validator.validate(c))

    def test_rejects_parent_prohibition_weakening(self):
        c = route.contract(self.intake({"production_or_system_of_record": False}, {"ambiguous_goal": False}))
        c["collaboration"]["parent_bounds"] = {"permissions": [], "data_access": [], "prohibited_actions": ["delete"], "token_budget": 1, "monetary_budget": 0}
        self.assertIn("child weakens parent prohibited_actions", validator.validate(c))

    def test_rejects_mode_and_high_risk_commit_mismatch(self):
        c = route.contract(self.intake({"security": True}, {"ambiguous_goal": False}))
        c["collaboration"]["mode"] = "AUTO"
        c["collaboration"]["authority"] = route.AUTHORITY["AUTO"]
        errors = validator.validate(c)
        self.assertIn("mode does not match risk and complexity classification", errors)
        self.assertIn("high-risk work cannot commit automatically", errors)

    def test_machine_schema_is_valid_json(self):
        schema = json.loads((ROOT / "assets" / "collaboration-contract.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["title"], "Northstar collaboration contract")

    def test_manifest_builds_portable_skill_zip(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "skill.zip"
            subprocess.run(["py", "-3", str(ROOT / "scripts" / "package_skill.py"), "--output", str(output)], check=True, capture_output=True, text=True)
            with zipfile.ZipFile(output) as archive:
                self.assertIn("northstar/SKILL.md", archive.namelist())
                self.assertIn("northstar/scripts/northstar_route.py", archive.namelist())

if __name__ == "__main__": unittest.main()
