import unittest

from portes_231 import (
    ALPHABET, LETTRES, OPERATEURS, ORDRE_CATEGORIES, PORTES, Lecture, Ordre, Porte, adjacence,
    cercle, distance, est_porte, orbites, porte, tourner,
)

ORDRES = (Ordre.ALPHABETIQUE, Ordre.CATEGORIES)


class Numerotation(unittest.TestCase):
    def test_opcodes_du_texte_du_4_octobre(self):
        # LetterOpCode : ALEF=0, MEM=1, SHIN=2, BET=3 … TAV=9, HE=10 … QOF=21.
        self.assertEqual("".join(map(str, ORDRE_CATEGORIES)), "אמשבגדכפרתהוזחטילנסעצק")
        self.assertEqual(LETTRES["א"].opcode, 0)
        self.assertEqual(LETTRES["מ"].opcode, 1)
        self.assertEqual(LETTRES["ת"].opcode, 9)
        self.assertEqual(LETTRES["ק"].opcode, 21)
        self.assertEqual(sorted(l.opcode for l in ALPHABET), list(range(22)))

    def test_la_numerotation_ne_change_pas_les_231_portes(self):
        for ordre in ORDRES:
            c = cercle(ordre)
            paires = {Porte.de(c[i], c[j]) for i in range(22) for j in range(i + 1, 22)}
            self.assertEqual(paires, set(PORTES))

    def test_la_face_reste_alphabetique(self):
        # Avec les opcodes, מ (1) précède ב (3) ; la face de ב–מ reste ב→מ.
        self.assertEqual(Porte.de("מ", "ב").face, porte("ב", "מ"))


class GrapheK22(unittest.TestCase):
    def test_matrice_d_adjacence(self):
        a = adjacence()
        self.assertEqual(len(a), 22)
        self.assertTrue(all(a[i][i] == 0 for i in range(22)))
        self.assertEqual(sum(map(sum, a)), 462)  # 231 arêtes, deux sens
        self.assertEqual(sum(a[i][j] for i in range(22) for j in range(i + 1, 22)), 231)
        self.assertTrue(all(a[i][j] == a[j][i] for i in range(22) for j in range(22)))

    def test_est_porte(self):
        self.assertTrue(est_porte("א", "ת"))
        self.assertFalse(est_porte("א", "א"))


class Rotation(unittest.TestCase):
    def test_avant_puis_arriere_revient(self):
        for ordre in ORDRES:
            for k in (1, 5, 11, 21, 22, -3):
                for op in OPERATEURS:
                    self.assertEqual(tourner(tourner(op, k, ordre), -k, ordre), op)

    def test_un_tour_complet_est_l_identite(self):
        for p in PORTES:
            self.assertEqual(tourner(p, 22), p)

    def test_la_rotation_garde_les_231_portes(self):
        # Une rotation est un automorphisme de K₂₂ : elle permute les portes.
        for ordre in ORDRES:
            for k in range(22):
                self.assertEqual({tourner(p, k, ordre) for p in PORTES}, set(PORTES))

    def test_l_operateur_garde_son_sens(self):
        op = tourner(porte("א", "ב"), 1)
        self.assertEqual((op.x.glyphe, op.y.glyphe), ("ב", "ג"))
        # Au passage de ת à א, une face peut devenir un dos.
        self.assertEqual(tourner(porte("א", "ת"), 1).lecture, Lecture.DOS)

    def test_avant_et_arriere_different(self):
        p = Porte.de("א", "ב")
        self.assertNotEqual(tourner(p, 1), tourner(p, -1))

    def test_orbites(self):
        for ordre in ORDRES:
            o = orbites(ordre)
            self.assertEqual(sorted(o), list(range(1, 12)))
            self.assertEqual([len(o[d]) for d in range(1, 11)], [22] * 10)
            self.assertEqual(len(o[11]), 11)
            for d, ps in o.items():
                for p in ps:
                    self.assertEqual(distance(tourner(p, 7, ordre), ordre), d)

    def test_l_ordre_de_la_roue_change_les_orbites(self):
        # א–מ sont à 12 places dans l'alphabet (distance 10), voisines par catégories.
        p = Porte.de("א", "מ")
        self.assertEqual(distance(p, Ordre.ALPHABETIQUE), 10)
        self.assertEqual(distance(p, Ordre.CATEGORIES), 1)

    def test_type_inconnu(self):
        with self.assertRaises(TypeError):
            tourner("א", 1)


if __name__ == "__main__":
    unittest.main()
