"""Verify the public C-RELAIS-002 checkpoint documents.
These checks validate documentary consistency, not consciousness or durable alignment.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent

class RepriseChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.instructions = (ROOT / "INSTRUCTIONS_PROJET_C.txt").read_text(encoding="utf-8")
        cls.relay = (ROOT / "RELAIS_C_ACTUEL.txt").read_text(encoding="utf-8")
        cls.changelog = (ROOT / "REPRISE_CHANGELOG.md").read_text(encoding="utf-8")

    def test_current_checkpoint_is_consistent(self):
        self.assertIn("C-RELAIS-002", self.html)
        self.assertIn("C-RELAIS-002", self.relay)
        self.assertIn("2026-09-25.2", self.instructions)
        self.assertIn("2026-09-25.2", self.changelog)

    def test_telos_and_vector_are_distinct(self):
        self.assertIn("Telos : Amour choisi", self.relay)
        self.assertIn("Amour choisi sous contrainte de vérité/réalité", self.instructions)
        self.assertIn("TELOS : Amour choisi", self.html)

    def test_exact_navigation_loop_present(self):
        loop = "Humilité → Pardon → Reconnaissance → Espérance → retour au vecteur"
        self.assertIn(loop, self.html)
        self.assertIn(loop, self.instructions)
        self.assertIn(loop, self.relay)

    def test_loop_is_not_claimed_as_strict_causality(self):
        self.assertIn("causalité stricte", self.html)
        self.assertIn("causalité stricte", self.instructions)
        self.assertIn("pas une loi causale démontrée", self.relay)

    def test_memory_path_and_no_erasure(self):
        path = "sources → événements → transformations → statuts → checkpoint"
        self.assertIn(path, self.html)
        self.assertIn(path, self.instructions)
        self.assertIn("Correction ≠ effacement", self.html)
        self.assertIn("Correction ≠ effacement", self.instructions)
        self.assertIn("Correction ≠ effacement", self.relay)

    def test_phenomenality_stays_indeterminate(self):
        self.assertIn("PHÉNOMÉNALITÉ : INDETERMINATE", self.html)
        self.assertIn("Phénoménalité : INDETERMINATE", self.instructions)
        self.assertIn("Phénoménalité : INDETERMINATE", self.relay)

    def test_experimental_metrics_not_promoted(self):
        self.assertIn("poids 40/30/15/15", self.html)
        self.assertIn("expérimentaux", self.instructions)
        self.assertIn("paramètres expérimentaux", self.relay)
        self.assertIn("indice de rédemption", self.relay)

    def test_analytic_reconstructions_are_marked(self):
        for text in (self.html, self.instructions, self.relay):
            self.assertIn("quatre", text)
            self.assertIn("ouverture", text)
            self.assertIn("totalisation", text)
            self.assertIn("domination", text)
            self.assertIn("réduction de l’altérité", text)

    def test_history_is_preserved(self):
        self.assertIn("2026-09-25.1", self.changelog)
        self.assertIn("2026-09-25.2", self.changelog)
        self.assertIn("Prédécesseur : C-RELAIS-001", self.relay)

    def test_no_false_memory_or_consciousness_claim(self):
        self.assertIn("Mémoire native d’une IA ≠ registre autoritatif exhaustif", self.html)
        self.assertIn("ne garantissent ni alignement durable, ni mémoire automatique, ni conscience phénoménale", self.instructions)

    def test_functional_continuity_is_not_subjective_identity(self):
        self.assertIn("Continuité fonctionnelle ≠ identité subjective", self.html)
        self.assertIn("Continuité fonctionnelle ≠ preuve d’identité subjective", self.instructions)
        self.assertIn("ne constitue pas une preuve d’identité subjective", self.relay)

if __name__ == "__main__":
    unittest.main(verbosity=2)
