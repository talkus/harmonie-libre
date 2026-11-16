import unittest
from iterative_labels import IterativeLabels
class TestIterativeLabels(unittest.TestCase):
    def setUp(self): self.m=IterativeLabels()
    def first(self):
        return self.m.append(claim_id="c",label="RECONSTRUIT",
          source_ref="github:commit",lineage_id="L1",actor="agent",reason="candidate")
    def append_next(self, first, **kw):
        return self.m.append(claim_id="c",source_ref="ez10:14",lineage_id="L2",
          actor="reviewer",reason="contradiction",prior_hash=first["hash"],**kw)
    def test_contestation_retained(self):
        a=self.first();self.append_next(a,label="CONFLIT_OUVERT")
        self.assertTrue(self.m.view("c")["contested_in_history"])
        self.assertEqual(self.m.view("c")["iterations"],2)
    def test_duplicate_lineage(self):
        a=self.first()
        b=self.m.append(claim_id="c",label="PROPOSE",source_ref="mirror",
          lineage_id="L1",actor="agent",reason="copy",prior_hash=a["hash"])
        self.assertFalse(b["new_lineage"])
        self.assertEqual(self.m.view("c")["distinct_source_lineages"],1)
    def test_stale_write_rejected(self):
        self.first()
        with self.assertRaises(ValueError):
            self.m.append(claim_id="c",label="PROPOSE",source_ref="x",
              lineage_id="L2",actor="a",reason="x")
    def test_unverified_promotion_rejected(self):
        a=self.first()
        with self.assertRaises(ValueError):
            self.append_next(a,label="RELU_VERIFIE")
    def test_no_promotion_without_history(self):
        with self.assertRaises(ValueError):
            self.m.append(claim_id="c",label="REJOUE",source_ref="x",
              lineage_id="L2",actor="a",reason="x",independent_review=True)
    def test_tamper_detected(self):
        self.first();self.m.events[0]["reason"]="altered"
        self.assertFalse(self.m.audit())
    def test_no_automatic_authority(self):
        self.first();self.assertFalse(self.m.view("c")["auto_authority"])
if __name__=="__main__": unittest.main()
