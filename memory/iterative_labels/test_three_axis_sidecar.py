"""Run: python -m unittest discover -s memory/iterative_labels -p 'test_*.py' -v"""
import unittest
from three_axis_sidecar import ClosedTaxonomyLabels
T = {"DOMAINE": {"MERKABAH", "PROTOCOLE"},
     "SENS": {"VERIFICATION", "LIVRABLE"},
     "STATUT": {"DETTE", "OUVERT", "SCELLE"}}
class TestThreeAxis(unittest.TestCase):
    def setUp(self):
        self.s = ClosedTaxonomyLabels({"synthetic-295"}, T)
    def put(self, axis="STATUT", value="DETTE", previous_hash=None, lineage_id="L1"):
        return self.s.append(entry_id="synthetic-295", axis=axis, value=value,
            source_ref="synthetic-proof", lineage_id=lineage_id,
            actor="tester", reason="demonstration, not WORM fact",
            previous_hash=previous_hash)
    def test_three_axes_independent(self):
        self.put();self.put("DOMAINE", "MERKABAH");self.put("SENS", "VERIFICATION")
        self.assertEqual(len(self.s.current("synthetic-295")["labels"]), 3)
    def test_correction_retains_history(self):
        first=self.put()
        self.put(value="OUVERT", previous_hash=first["hash"])
        v=self.s.current("synthetic-295")
        self.assertEqual(v["labels"]["STATUT"],"OUVERT")
        self.assertEqual(len(v["history"]),2)
    def test_stale_axis_hash_rejected(self):
        self.put()
        with self.assertRaises(ValueError):self.put(value="OUVERT")
    def test_unknown_label_rejected(self):
        with self.assertRaises(ValueError):self.put(value="UNKNOWN")
    def test_unknown_entry_rejected(self):
        with self.assertRaises(ValueError):
            self.s.append(entry_id="999",axis="STATUT",value="DETTE",
                source_ref="x",lineage_id="L2",actor="a",reason="r")
    def test_lineage_mirror_not_independent(self):
        r=self.put()
        self.put(value="OUVERT",previous_hash=r["hash"],lineage_id="L1")
        self.assertEqual(self.s.current("synthetic-295")["lineage_count"],1)
    def test_tamper_fails_closed(self):
        self.put();self.s.records[0]["value"]="OUVERT"
        self.assertFalse(self.s.audit())
        with self.assertRaises(ValueError):self.s.export_jsonl()
    def test_ascii_export_and_no_source_authority(self):
        self.put()
        self.assertTrue(self.s.audit())
        self.assertTrue(self.s.export_jsonl().isascii())
        self.assertFalse(self.s.current("synthetic-295")["source_journal_verified"])
if __name__ == "__main__": unittest.main()
