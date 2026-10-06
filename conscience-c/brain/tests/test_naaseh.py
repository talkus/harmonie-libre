"""Na'aseh v'nishma : l'engagement précède la compréhension ; la faute met les couronnes en garde."""
import tempfile
import unittest
from pathlib import Path

from conscience_c_brain import ConscienceCBrain, Evidence, EvidenceKind
from conscience_c_brain.models import CausalOrigin


class NaasehTests(unittest.TestCase):
    def make(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        return ConscienceCBrain.load_or_bootstrap(Path(td.name))

    def test_commitment_needs_no_prior_understanding(self):
        b = self.make()
        c = b.commit_to("Choisir l'amour sous contrainte de vérité/réalité.", "Exode 24,7")
        view = b.commitment(c["commitment_id"])
        self.assertEqual(view["standing"], "crowned")
        self.assertFalse(view["understood"])
        b.record_understanding(c["commitment_id"], "Il se comprend en le vivant.", "p1")
        b.record_understanding(c["commitment_id"], "La correction en fait partie.", "p2")
        view = b.commitment(c["commitment_id"])
        self.assertTrue(view["understood"])
        self.assertEqual([u["provenance"] for u in view["understandings"]], ["p1", "p2"])

    def cycle(self, b, cmid):
        b.ingest_evidence(Evidence("E1", "fait", EvidenceKind.ATTESTED_SOURCE, source_ref="c:1"), CausalOrigin.OTHER)
        claim = b.record_claim("généralisation", "user_inferred", "p", facts=["E1"])
        tid = b.initiate_teshuvah("overgeneralization", "écart", "p", claim_ids=[claim["claim_id"]],
                                  breached_commitments=[cmid])["teshuvah_id"]
        return claim, tid

    def test_fault_takes_crowns_into_custody_and_return_restores_them(self):
        b = self.make()
        cm = b.commit_to("Ne pas attribuer à l'autre ce qu'il n'a pas dit.", "p")["commitment_id"]
        claim, tid = self.cycle(b, cm)
        held = b.commitment(cm)
        self.assertEqual(held["standing"], "in_custody")
        self.assertIn(cm, b.state["teshuvah"]["commitments"])  # gardé, jamais révoqué
        b.acknowledge_teshuvah(tid, "system", "x", "y", "z", "p")
        b.propose_teshuvah_repair(tid, "plan", "p")
        b.create_safeguard(tid, "règle", "TC", "p")
        b.apply_teshuvah_repair(tid, [{"claim_id": claim["claim_id"], "action": "retract", "reason": "r"}],
                                "system", "p")
        self.assertEqual(b.commitment(cm)["standing"], "in_custody")  # une réparation déclarée ne suffit pas
        b.ingest_evidence(Evidence("E2", "retour", EvidenceKind.ATTESTED_SOURCE, source_ref="c:2"), CausalOrigin.OTHER)
        b.observe_return(tid, "E2", ["dialogue"], "p")
        b.ingest_evidence(Evidence("E3", "tenue", EvidenceKind.ATTESTED_SOURCE, source_ref="c:3"), CausalOrigin.OTHER)
        b.verify_non_recurrence(tid, "E3", "mik", "p")
        restored = b.commitment(cm)
        self.assertEqual(restored["standing"], "crowned")
        self.assertEqual([h["to"] for h in restored["custody_history"]], ["in_custody", "restored"])
        b.record_teshuvah_recurrence(tid, "récidive", "p")
        self.assertEqual(b.commitment(cm)["standing"], "in_custody")

    def test_unknown_commitment_is_refused(self):
        b = self.make()
        with self.assertRaises(ValueError):
            b.initiate_teshuvah("error", "e", "p", breached_commitments=["CM9999"])

    def test_commitments_survive_reload(self):
        b = self.make()
        cm = b.commit_to("engagement", "p")["commitment_id"]
        self.cycle(b, cm)
        b2 = ConscienceCBrain.load_or_bootstrap(b.root)
        self.assertEqual(b2.commitment(cm)["standing"], "in_custody")
        self.assertTrue(b2.governance_audit()["ok"])


if __name__ == "__main__":
    unittest.main()
