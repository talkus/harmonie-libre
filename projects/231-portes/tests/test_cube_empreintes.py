import csv
import io
import unittest
from collections import Counter
from pathlib import Path

from portes_231 import (
    DOUBLES, MERES, PORTES, SIMPLES, Ordre, Porte, espace, etat_suivant,
    periode, porte, trajectoire,
)
from portes_231 import empreintes
from portes_231.cube import CASES, COINS, PALAIS, PLACES, genre, place
from portes_231.table_etendue import COLONNES, STATUTS, csv_texte, rangees

RACINE = Path(__file__).resolve().parent.parent


class CubeDesChapitres4et5(unittest.TestCase):
    def test_27_cases_sans_reste(self):
        genres = Counter(genre(p) for p in CASES)
        self.assertEqual(genres, {"centre": 1, "face": 6, "arête": 12, "coin": 8})

    def test_doubles_six_cotes_et_le_palais(self):
        self.assertEqual(Counter(genre(place(d)) for d in DOUBLES), {"face": 6, "centre": 1})
        self.assertEqual(place("ת"), PALAIS)

    def test_simples_douze_bordures(self):
        self.assertEqual({genre(place(s)) for s in SIMPLES}, {"arête"})
        self.assertEqual(len({place(s) for s in SIMPLES}), 12)

    def test_chaque_case_au_plus_une_lettre(self):
        self.assertEqual(len(set(PLACES.values())), 19)

    def test_les_meres_sont_des_axes(self):
        for m in MERES:
            with self.assertRaises(ValueError):
                place(m)

    def test_les_coins_sont_les_huit_etats(self):
        self.assertEqual(len(COINS), len(espace()))
        self.assertEqual({tuple((v + 1) // 2 for v in c) for c in COINS},
                         {e.coordonnees for e in espace()})


class Empreintes(unittest.TestCase):
    def test_les_deux_tables_different(self):
        self.assertNotEqual(empreintes.table(Ordre.ALPHABETIQUE), empreintes.table(Ordre.CATEGORIES))

    def test_relues_par_lettres_elles_donnent_les_memes_portes(self):
        for ordre in (Ordre.ALPHABETIQUE, Ordre.CATEGORIES):
            relue = empreintes.relire_par_lettres(empreintes.serialisation_table(ordre))
            self.assertEqual(relue, empreintes.serialisation_portes())

    def test_convention(self):
        for texte in (empreintes.serialisation_table(), empreintes.serialisation_portes(),
                      empreintes.serialisation_bijection()):
            self.assertFalse(texte.startswith("\ufeff"))
            self.assertTrue(texte.endswith("\n"))
            self.assertFalse(texte.endswith("\n\n"))

    def test_231_lignes(self):
        self.assertEqual(len(empreintes.serialisation_table().splitlines()), 231)
        self.assertEqual(len(empreintes.serialisation_bijection().splitlines()), 22)

    def test_valeurs_scellees(self):
        # Une modification de la table doit être visible : changer ces valeurs
        # demande de changer aussi EMPREINTES.md.
        self.assertEqual(empreintes.table(Ordre.ALPHABETIQUE),
                         "578db9d53b98c2281b156d56515912af68cc2c6e7c564a7fcc93fb3a83276e27")
        self.assertEqual(empreintes.table(Ordre.CATEGORIES),
                         "4f95bd3c96fa95d174544fed59b92ca7df0b6a7677dc7e3d6a561bf5b71b5b79")
        self.assertEqual(empreintes.portes(),
                         "574ac94323f6bee6a2ffaf26901949baa36b5d24eea528bde937859400fe0d0d")

    def test_le_fichier_est_a_jour(self):
        self.assertEqual((RACINE / "EMPREINTES.md").read_text(encoding="utf-8"), empreintes.markdown())


class RegleDeTransition(unittest.TestCase):
    def test_un_pas(self):
        self.assertEqual(etat_suivant({Porte.de("א", "ב")}), {Porte.de("ב", "ג")})

    def test_trajectoire(self):
        t = trajectoire({porte("א", "ב")}, 3)
        self.assertEqual(len(t), 4)
        self.assertEqual(t[3], {porte("ד", "ה")})

    def test_toutes_les_portes_actives_est_un_point_fixe(self):
        self.assertEqual(periode(set(PORTES)), 1)

    def test_periodes(self):
        self.assertEqual(periode({Porte.de("א", "ב")}), 22)
        # Deux lettres diamétralement opposées : la porte revient après 11 pas,
        # l'opérateur orienté après 22.
        self.assertEqual(periode({Porte.de("א", "ל")}), 11)
        self.assertEqual(periode({porte("א", "ל")}), 22)
        self.assertEqual(periode({porte("א", "ב")}, crans=2), 11)

    def test_periode_minimale_de_chaque_porte(self):
        # 11 portes antipodales (distance 11) reviennent en 11 pas, les 220
        # autres en 22 ; chaque opérateur orienté revient en 22.
        from collections import Counter

        from portes_231 import OPERATEURS, distance
        periodes = Counter(periode({p}) for p in PORTES)
        self.assertEqual(periodes, {11: 11, 22: 220})
        for p in PORTES:
            self.assertEqual(periode({p}), 11 if distance(p) == 11 else 22)
        self.assertEqual({periode({op}) for op in OPERATEURS}, {22})
        for ordre in (Ordre.ALPHABETIQUE, Ordre.CATEGORIES):
            self.assertEqual(Counter(periode({p}, ordre=ordre) for p in PORTES), {11: 11, 22: 220})

    def test_avant_et_arriere(self):
        s = {porte("ג", "ש")}
        self.assertEqual(etat_suivant(etat_suivant(s, 1), -1), s)


class TableEtendue(unittest.TestCase):
    def test_231_rangees_et_colonnes(self):
        lecture = list(csv.DictReader(io.StringIO(csv_texte())))
        self.assertEqual(len(lecture), 231)
        self.assertEqual(tuple(lecture[0]), COLONNES)
        self.assertEqual(set(STATUTS), set(COLONNES))

    def test_poids(self):
        r = rangees()[0]  # א–ב
        self.assertEqual((r["poids_somme"], r["poids_produit"], r["guematria_somme"]), (5, 6, 3))
        produits = Counter(r["poids_produit"] for r in rangees())
        # mère·mère 9 (3), mère·double 6 (21), mère·simple 3 (36),
        # double·double 4 (21), double·simple 2 (84), simple·simple 1 (66)
        self.assertEqual(produits, {9: 3, 6: 21, 3: 36, 4: 21, 2: 84, 1: 66})

    def test_le_fichier_est_a_jour(self):
        self.assertEqual((RACINE / "TABLE_231_ETENDUE.csv").read_text(encoding="utf-8"), csv_texte())


if __name__ == "__main__":
    unittest.main()
