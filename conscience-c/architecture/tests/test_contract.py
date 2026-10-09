"""Regression cases for the published documentary contract."""
from copy import deepcopy
from contextlib import redirect_stdout
from io import StringIO
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from architecture_c_contract import main, validate

MODEL = ROOT / "versions/2026-10-08/architecture-c-continuite-2026-10-08.json"


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.model = json.loads(MODEL.read_text(encoding="utf-8"))
        self.contract = self.model["operational_contract"]
        self.micro = self.contract["nodes"][0]

    def reject(self):
        self.assertTrue(validate(self.model))

    def test_published_document_is_valid(self):
        self.assertEqual(validate(self.model), [])

    def test_objection_cannot_disappear_in_summary(self):
        self.contract["nodes"][1]["review"]["objection_refs"].remove("OBJ-RUNTIME")
        self.reject()

    def test_unknown_cannot_disappear_in_summary(self):
        self.contract["nodes"][2]["review"]["unknown_refs"].remove("UNK-SERVICE")
        self.reject()

    def test_unknown_source_is_not_a_proof(self):
        self.micro["evidence"]["source_refs"].append("MISSING-SOURCE")
        self.reject()

    def test_unknown_input_is_rejected(self):
        self.micro["work"]["input_refs"].append("MISSING-INPUT")
        self.reject()

    def test_purpose_cannot_disappear_across_views(self):
        self.contract["nodes"][1]["purpose"]["goal_refs"].remove("GOAL-RESUME")
        self.reject()

    def test_cyclic_purpose_hierarchy_is_rejected(self):
        self.contract["goals"][0]["parent"] = "GOAL-RESUME"
        self.reject()

    def test_meta_needs_explicit_review_targets(self):
        self.contract["nodes"][3]["scope"]["reviews"] = []
        self.reject()

    def test_meta_cannot_only_review_itself(self):
        self.contract["nodes"][3]["scope"]["reviews"] = ["NODE-META"]
        self.reject()

    def test_completion_without_evidence_is_rejected(self):
        self.micro["continuity"]["state"] = "valide"
        self.reject()

    def test_simulation_cannot_complete_real_work(self):
        self.micro["continuity"]["state"] = "valide"
        self.micro["evidence"].update(proof_refs=["PROOF-SIMULATED"], proof_kind="simulation")
        self.reject()

    def test_retry_budget_is_shared_across_views(self):
        for n in self.contract["nodes"]:
            n["continuity"]["attempts_used"] = 1
        self.reject()

    def test_unknown_external_effect_needs_reconciliation(self):
        self.micro["work"]["external_effect"] = True
        self.micro["continuity"].update(effect_result="unknown", next_action="retry")
        self.reject()

    def test_duplicate_external_effect_identity_is_rejected(self):
        for n in self.contract["nodes"][:2]:
            n["work"].update(external_effect=True, execution_key="SAME-ACTION")
        self.reject()

    def test_document_cannot_certify_runtime_even_with_a_named_proof(self):
        self.micro["evidence"].update(
            claim="fonctionnement_continu_observe", proof_kind="runtime_observation",
            proof_refs=["PROOF-SIMULATED"], observed_interval={"start":"a", "end":"b"})
        self.reject()

    def test_document_cannot_attest_durable_storage(self):
        self.micro["continuity"]["durable_checkpoint_verified"] = True
        self.reject()

    def test_criteria_migration_must_be_declared(self):
        self.contract["nodes"][1]["review"]["criteria_version"] = "new-version"
        self.reject()

    def test_malformed_inputs_fail_closed_without_traceback(self):
        malformed = [None, [], {"operational_contract": []}]
        cases = [
            ("nodes", [None]), ("goals", "not-a-list"),
            ("budgets", [{"id": [], "max_attempts": True, "timeout_seconds_per_attempt": "30"}]),
            ("transfers", [None]), ("registry", {"source_refs": [[]]}),
        ]
        for field, value in cases:
            m = deepcopy(self.model)
            m["operational_contract"][field] = value
            malformed.append(m)
        for field, value in [("goal_refs", [[]]), ("goal_refs", "GOAL-LINK")]:
            m = deepcopy(self.model)
            m["operational_contract"]["nodes"][0]["purpose"][field] = value
            malformed.append(m)
        m = deepcopy(self.model)
        m["operational_contract"]["nodes"][0]["continuity"]["attempts_used"] = True
        malformed.append(m)
        for m in malformed:
            with self.subTest(model=m):
                self.assertTrue(validate(m))

    def test_reference_source_bytes_are_preserved(self):
        source = self.model["sources"]["previous_map"]
        data = (MODEL.parent / source["path"]).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), source["sha256"])


class CLITests(unittest.TestCase):
    def test_valid_model_cli_reports_documentary_scope(self):
        out = StringIO()
        with redirect_stdout(out):
            code = main([str(MODEL)])
        self.assertEqual(code, 0)
        self.assertFalse(json.loads(out.getvalue())["execution_authority"])

    def test_invalid_json_returns_structured_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.json"
            path.write_text("{", encoding="utf-8")
            out = StringIO()
            with redirect_stdout(out):
                code = main([str(path)])
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(out.getvalue())["valid"])

    def test_missing_file_returns_structured_error(self):
        with tempfile.TemporaryDirectory() as directory:
            out = StringIO()
            with redirect_stdout(out):
                code = main([str(Path(directory) / "missing.json")])
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(out.getvalue())["valid"])


if __name__ == "__main__":
    unittest.main()

