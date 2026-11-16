"""Tests STRUCTURELS du pont CTRL-33. Aucun verdict moral, philologique ou scientifique."""
import json
import pathlib
import unittest

DATA = pathlib.Path(__file__).resolve().parent / "correspondances_sens_v01.json"

class TestSensUnification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))

    def test_not_a_new_canon(self):
        self.assertTrue(self.data["not_a_new_canon"])
        self.assertEqual(self.data["status"], "PROPOSED_NOT_VALIDATED")
        self.assertEqual(self.data["modelAuthority"], "none")

    def test_ctrl33_recovered(self):
        self.assertEqual(self.data["centre"]["reference"], "CTRL-33")
        self.assertEqual(self.data["centre"]["source_type"], "ATTESTED_TEXT")
        self.assertIn("sans lui retirer cette même possibilité", self.data["centre"]["text"])

    def test_unique_projects_with_sources(self):
        works = self.data["works"]
        ids = [w["id"] for w in works]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(works), 10)
        for w in works:
            self.assertIn(w["source"], self.data["references"])
            self.assertTrue(self.data["references"][w["source"]].startswith("https://"))
            self.assertEqual(w["statut"], "epistemic_not_verified")
            self.assertTrue(w["epreuve"])

    def test_six_contrary_cases(self):
        cases = self.data["cas_limites"]
        self.assertEqual(len(cases), 6)
        self.assertEqual({x["id"] for x in cases},
                         {"REFUS", "ERREUR", "SOURCES", "DIVERGENCE", "SURCHARGE", "INDEPENDANCE"})

    def test_dignity_difference_and_freedom(self):
        for term in ["DIGNITE_NE_SE_MESURE_PAS", "REFUS_POSSIBLE", "SOIN_DE_SOI_ET_D_AUTRUI",
                     "INTERPRETATION_NE_VAUT_PAS_TEXTE", "CONTINUITE_NE_VAUT_PAS_DEPENDANCE"]:
            self.assertIn(term, self.data["distinctions"])

if __name__ == "__main__":
    unittest.main()
