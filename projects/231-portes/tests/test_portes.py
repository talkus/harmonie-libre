import doctest
import unittest
from collections import Counter

import portes_231
from portes_231 import (
    ALPHABET, DAGESH, DOUBLES, EXEMPLES, LETTRES, MERES, OPERATEURS, PORTES, RAPHE, REGLES,
    SIMPLES, Categorie, Lecture, Porte, lettre, matrice, par_categories, porte,
)
from portes_231 import portes as module_portes
from portes_231.__main__ import main
from portes_231.statut import RECONSTRUCTION_ANALYTIQUE, SOURCE_ATTESTEE

M, D, S = Categorie.MERE, Categorie.DOUBLE, Categorie.SIMPLE


class LettresSeferYetzirah(unittest.TestCase):
    def test_22_lettres_dans_l_ordre_alphabetique(self):
        self.assertEqual("".join(l.glyphe for l in ALPHABET), "אבגדהוזחטיכלמנסעפצקרשת")
        self.assertEqual([l.rang for l in ALPHABET], list(range(22)))

    def test_trois_meres_sept_doubles_douze_simples(self):
        self.assertEqual("".join(map(str, MERES)), "אמש")
        self.assertEqual("".join(map(str, DOUBLES)), "בגדכפרת")
        self.assertEqual("".join(map(str, SIMPLES)), "הוזחטילנסעצק")

    def test_doubles_raphe_zero_dagesh_un(self):
        bet = LETTRES["ב"]
        self.assertEqual((bet.etat(RAPHE), bet.etat(DAGESH)), ("vide", "plein"))
        self.assertEqual(LETTRES["ת"].etat(DAGESH), "vrai")
        self.assertTrue(all(l.etats for l in DOUBLES))
        with self.assertRaises(ValueError):
            LETTRES["א"].etat(0)
        with self.assertRaises(ValueError):
            bet.etat(2)

    def test_elements_des_meres(self):
        self.assertEqual([l.element for l in MERES], ["Air", "Eau", "Feu"])

    def test_recherche_par_nom(self):
        self.assertIs(lettre("aleph"), LETTRES["א"])
        self.assertIs(lettre("ם"), LETTRES["מ"])
        # Recherche exacte : « Zayin » se termine par « ayin » sans être Ayin.
        self.assertIs(lettre("Ayin"), LETTRES["ע"])
        self.assertIs(lettre("Zayin"), LETTRES["ז"])
        with self.assertRaises(KeyError):
            lettre("yin")
        with self.assertRaises(KeyError):
            lettre("Omega")

    def test_statuts_distincts(self):
        aleph = LETTRES["א"]
        self.assertEqual(aleph.statut_categorie, SOURCE_ATTESTEE)
        self.assertEqual(aleph.statut_primitive, RECONSTRUCTION_ANALYTIQUE)


class Portes(unittest.TestCase):
    def test_231_portes_462_operateurs(self):
        self.assertEqual(len(PORTES), 231)
        self.assertEqual(len(set(PORTES)), 231)
        self.assertEqual(len(OPERATEURS), 462)
        self.assertEqual(len({(o.x, o.y) for o in OPERATEURS}), 462)

    def test_decompte_par_categories(self):
        attendu = {(M, M): 3, (D, D): 21, (S, S): 66, (M, D): 21, (M, S): 36, (D, S): 84}
        for (c1, c2), n in attendu.items():
            self.assertEqual(len(par_categories(c1, c2)), n, (c1, c2))
        self.assertEqual(sum(attendu.values()), 231)

    def test_face_suit_l_alphabet_dos_est_l_inverse(self):
        for p in PORTES:
            self.assertLess(p.face.x.rang, p.face.y.rang)
            self.assertEqual(p.face.lecture, Lecture.FACE)
            self.assertEqual(p.dos.lecture, Lecture.DOS)
            self.assertEqual(p.dos, p.face.inverse)
            self.assertEqual(p.face.porte, p)
            self.assertEqual(p.dos.porte, p)

    def test_non_commutativite(self):
        for p in PORTES:
            self.assertNotEqual(p.face, p.dos)
        # Entre catégories différentes, la règle elle-même change.
        self.assertNotEqual(porte("א", "ב").regle, porte("ב", "א").regle)
        # Dans une même catégorie, la règle est la même : c'est la signature
        # (les primitives) qui distingue X ⊗ Y de Y ⊗ X.
        self.assertEqual(porte("ה", "ו").regle, porte("ו", "ה").regle)
        self.assertEqual(porte("ה", "ו").signature, "Observe ⊗ Concat")
        self.assertEqual(porte("ו", "ה").signature, "Concat ⊗ Observe")
        self.assertEqual(len({o.signature for o in OPERATEURS}), 462)

    def test_porte_de_deux_lettres_distinctes(self):
        with self.assertRaises(ValueError):
            Porte.de("א", "א")
        with self.assertRaises(ValueError):
            porte("מ", "מ")
        with self.assertRaises(ValueError):
            Porte(LETTRES["ב"], LETTRES["א"])

    def test_matrice_triangulaire_et_transposee(self):
        m = matrice()
        self.assertEqual(len(m), 22)
        for i in range(22):
            self.assertIsNone(m[i][i])
            for j in range(22):
                if i != j:
                    self.assertEqual(m[i][j].inverse, m[j][i])
                    attendu = Lecture.FACE if i < j else Lecture.DOS
                    self.assertEqual(m[i][j].lecture, attendu)


class RegleDeComposition(unittest.TestCase):
    def test_neuf_regles(self):
        self.assertEqual(len(REGLES), 9)

    def test_exemple_etape_6(self):
        op = porte("א", "ב")
        self.assertEqual(op("esprit", "contenant"), "État conditionnel: esprit si contenant")

    def test_gabarits_etape_6(self):
        cas = {
            ("א", "מ"): "État fondamental: a ⊗ b",
            ("א", "ה"): "Direction élémentaire: a vers b",
            ("ב", "א"): "Condition sur état: a sur b",
            ("ב", "ג"): "Logique binaire: a ET b",
            ("ב", "ה"): "Opération conditionnelle: si a alors b",
            ("ה", "א"): "Transformation élémentaire: a de b",
            ("ה", "ב"): "Transformation conditionnelle: a si b",
            ("ה", "ו"): "Composition d'axes: a puis b",
        }
        for (x, y), attendu in cas.items():
            self.assertEqual(porte(x, y)("a", "b"), attendu)


class Exemples(unittest.TestCase):
    def test_26_portes_52_operateurs_nommes(self):
        self.assertEqual(len(EXEMPLES), 52)
        portes_nommees = {Porte.de(x, y) for x, y in EXEMPLES}
        self.assertEqual(len(portes_nommees), 26)
        for p in portes_nommees:
            self.assertIsNotNone(p.face.nommage)
            self.assertIsNotNone(p.dos.nommage)

    def test_sens_garde_pour_les_exemples_hors_ordre(self):
        # Le texte appelle « face » מ→ד, מ→ז et ש→ט ; l'alphabet en fait des dos.
        for x, y, nom in (("מ", "ד", "fopen()"), ("מ", "ז", "split()"), ("ש", "ט", "map()")):
            op = porte(x, y)
            self.assertEqual(op.nommage.fonction, nom)
            self.assertEqual(op.lecture, Lecture.DOS)
        self.assertEqual(porte("ט", "ש").nommage.fonction, "reduce()")

    def test_quelques_noms(self):
        self.assertEqual(porte("א", "מ").nommage.fonction, "|")
        self.assertEqual(porte("ת", "ד").nommage.resultat, "Autorisation")
        self.assertEqual(porte("ר", "ש").nommage.resultat, "Compilation")
        self.assertIsNone(porte("ג", "ת").nommage)

    def test_un_nom_n_est_pas_une_cle(self):
        # map() et split() nomment chacun deux opérateurs différents.
        doublons = {f for f, n in Counter(e.fonction for e in EXEMPLES.values()).items() if n > 1}
        self.assertEqual(doublons, {"map()", "split()"})


class Interface(unittest.TestCase):
    def test_doctests(self):
        resultat = doctest.testmod(module_portes)
        self.assertEqual(resultat.failed, 0)
        self.assertGreater(resultat.attempted, 0)

    def test_cli(self):
        import contextlib
        import io

        for args in ([], ["א", "מ"], ["--nommes"]):
            sortie = io.StringIO()
            with contextlib.redirect_stdout(sortie):
                self.assertEqual(main(args), 0)
            self.assertTrue(sortie.getvalue())
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["א"]), 2)

    def test_api_publique(self):
        for nom in portes_231.__all__:
            self.assertTrue(hasattr(portes_231, nom), nom)


if __name__ == "__main__":
    unittest.main()
