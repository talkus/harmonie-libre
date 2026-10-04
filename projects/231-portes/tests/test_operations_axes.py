import unittest
from pathlib import Path

from portes_231 import (
    ALPHABET, AXES, DAGESH, DOUBLES, LETTRES, OPERATEURS, PORTES, RAPHE, SIMPLES, Balance,
    Categorie, Etat, Ordre, Porte, axes_de, espace, haqaq, hamir, hatsav, maisons, refleter,
    shaqal, tourner, tsaraf,
)
from portes_231.systemes import SENTIERS_DE_L_ARBRE, SYSTEMES, VOIES_DE_SAGESSE
from portes_231.table import lignes, markdown

RACINE = Path(__file__).resolve().parent.parent


class CinqOperations(unittest.TestCase):
    def test_haqaq_grave_l_alphabet(self):
        self.assertEqual(haqaq(), ALPHABET)

    def test_hatsav_taille_3_7_12(self):
        t = hatsav()
        self.assertEqual([len(t[c]) for c in Categorie], [3, 7, 12])
        self.assertEqual(hatsav("שלום")[Categorie.SIMPLE], (LETTRES["ל"], LETTRES["ו"]))

    def test_shaqal_deux_balances(self):
        self.assertEqual([shaqal(c) for c in "אבה"], [3, 2, 1])
        self.assertEqual(sum(shaqal(l) for l in ALPHABET), 3 * 3 + 7 * 2 + 12)
        self.assertEqual(shaqal("ת", Balance.GUEMATRIA), 400)
        self.assertEqual(sum(shaqal(l, Balance.GUEMATRIA) for l in ALPHABET), 1495)

    def test_hamir_et_les_maisons_du_chapitre_4(self):
        # « Deux pierres bâtissent deux maisons … sept en bâtissent 5040. »
        self.assertEqual([maisons(n) for n in range(2, 8)], [2, 6, 24, 120, 720, 5040])
        self.assertEqual(len(list(hamir("אמש"))), 6)
        self.assertEqual(next(hamir("אב")), (LETTRES["א"], LETTRES["ב"]))
        with self.assertRaises(ValueError):
            list(hamir("אא"))
        with self.assertRaises(ValueError):
            maisons(-1)

    def test_tsaraf_combine(self):
        self.assertEqual(tsaraf("ב", "א"), Porte.de("א", "ב"))
        self.assertEqual(len(tsaraf()), 231)
        with self.assertRaises(TypeError):
            tsaraf("א")


class MeresEtDoubles(unittest.TestCase):
    def test_sept_doubles_sept_parties_non_vides(self):
        parties = [axes_de(d) for d in DOUBLES]
        self.assertEqual(len(set(parties)), 7)
        self.assertTrue(all(parties))
        self.assertEqual(axes_de("ב"), {LETTRES["א"]})
        self.assertEqual(axes_de("ת"), set(AXES))
        with self.assertRaises(ValueError):
            axes_de("א")

    def test_raphe_laisse_dagesh_bascule(self):
        e = Etat()
        self.assertEqual(e.appliquer("ד", RAPHE), e)
        self.assertEqual(e.appliquer("ד", DAGESH).coordonnees, (1, 1, 0))
        with self.assertRaises(ValueError):
            e.appliquer("ד", 2)

    def test_bistable_sur_z2(self):
        for e in espace():
            for d in DOUBLES:
                self.assertEqual(e.appliquer(d).appliquer(d), e)

    def test_les_doubles_parcourent_tout_z2_cube(self):
        origine = Etat()
        atteints = {origine} | {origine.appliquer(d) for d in DOUBLES}
        self.assertEqual(atteints, set(espace()))
        self.assertEqual(len(espace()), 8)

    def test_z3_cube(self):
        self.assertEqual(len(espace(3)), 27)
        e = Etat(modulo=3)
        trois_fois = e.appliquer("ת").appliquer("ת").appliquer("ת")
        self.assertNotEqual(e.appliquer("ת").appliquer("ת"), e)
        self.assertEqual(trois_fois, e)
        with self.assertRaises(ValueError):
            Etat(air=2)
        with self.assertRaises(ValueError):
            Etat(modulo=1)

    def test_simples_hors_des_axes(self):
        for s in SIMPLES:
            with self.assertRaises(ValueError):
                axes_de(s)


class Reflexion(unittest.TestCase):
    def test_involution_et_231_portes(self):
        for ordre in (Ordre.ALPHABETIQUE, Ordre.CATEGORIES):
            for op in OPERATEURS:
                self.assertEqual(refleter(refleter(op, ordre), ordre), op)
            self.assertEqual({refleter(p, ordre) for p in PORTES}, set(PORTES))
        self.assertEqual(refleter(LETTRES["א"]), LETTRES["א"])
        self.assertEqual(refleter(LETTRES["ב"]), LETTRES["ת"])

    def test_diedral(self):
        # Refléter, tourner de k, refléter revient à tourner de −k.
        for op in OPERATEURS[:40]:
            self.assertEqual(refleter(tourner(refleter(op), 3)), tourner(op, -3))

    def test_type_inconnu(self):
        with self.assertRaises(TypeError):
            refleter("א")


class Table(unittest.TestCase):
    def test_231_lignes(self):
        self.assertEqual(len(lignes()), 231)
        self.assertIn("| 1 | א–ב | א Aleph | Mère | ב Bet | Double |", lignes()[0])
        self.assertIn("| 231 | ש–ת | ש Shin | Mère | ת Tav | Double |", lignes()[-1])

    def test_le_fichier_est_a_jour(self):
        self.assertEqual((RACINE / "TABLE_231.md").read_text(encoding="utf-8"), markdown())


class Comparaison(unittest.TestCase):
    def test_decomptes(self):
        attendu = {
            "231 portes (face seule)": 231,
            "462 opérateurs (face et dos)": 462,
            "Trigrammes du Yi Jing": 8,
            "Hexagrammes du Yi Jing": 64,
            "Hexagrammes comme paires de trigrammes": 64,
            "Paires de sefirot possibles": 45,
            "Troisième figure de Lulle": 36,
            "Codons du code génétique": 64,
        }
        self.assertEqual({s.nom: s.combinaisons for s in SYSTEMES}, attendu)
        self.assertEqual(VOIES_DE_SAGESSE, 32)
        self.assertEqual(SENTIERS_DE_L_ARBRE, len(ALPHABET))

    def test_trigrammes_et_doubles(self):
        # 8 trigrammes = 2³ = les 8 états de l'espace des mères sur Z₂.
        trigrammes = next(s for s in SYSTEMES if s.nom.startswith("Trigrammes"))
        self.assertEqual(trigrammes.combinaisons, len(espace()))


if __name__ == "__main__":
    unittest.main()
