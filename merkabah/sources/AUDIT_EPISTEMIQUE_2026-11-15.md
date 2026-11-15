# MERKABAH — Audit contradictoire du 15 novembre 2026

**CANDIDAT, NON VALIDÉ.** Sans altérer le graphe initial ni le noyau original.

## Mesures établies sur le graphe GitHub v0.1

- 45 nœuds : 4 êtres, 4 roues, 16 visages, 16 ailes et 5 éléments complémentaires.
- 50 relations : 4 appariements êtres/roues, 4 déplacements liés, 16 appartenances de faces, 16 d'ailes, etc.
- Identifiants de nœuds distincts, aucune relation vers un nœud absent sur la version examinée.
- **45/45 nœuds et 50/50 relations sans référence de verset précise individuelle** ; la provenance est seulement `ez1`.
- **0/45 nœud et 0/50 relation avec portée de scène** ; la présence globale d'une liste `Ezekiel_1/Ezekiel_10` ne suffit pas.
- Les tests d'origine sont structurels, pas une revue philologique indépendante.

## Invariants et preuves manquantes

| Catégorie | Ce qui est contrôlable | Ce qui n'est pas prouvé |
|---|---|---|
| Texte | Quatre êtres, chacun quatre faces et ailes | L'orientation anatomique de chaque face |
| Roues | Une roue associée à chaque être, yeux mentionnés | Tori orthogonaux, nombre d'yeux, emplacement métrique |
| Mouvement | Éz 1:9,12,17,19-21 et 10:11,16-17 : mouvement lié sans retournement | Trajectoire carrée, vitesse, moteur physique |
| Scènes | Éz 1:10 : **bœuf** ; Éz 10:14 : **chérubin** | Leur équivalence géométrique ; cf. Éz 10:22 |
| Archives | Les identifiants de fichiers et passations ont été rapportés | Comparaison des octets du `merkabah_core.py` originel |

Les manuscrits et les traductions divergent sur Éz 10:14 ; conserver les deux libellés. Dans le prototype Lovable, la position arrière de la face de l'aigle et le caractère carré du trajet sont **des choix de modélisation**, non des obligations textuelles. La réussite d'un test de comptage ne valide pas la géométrie.

## Sources publiques de lecture

- Ézéchiel 1, Louis Segond : https://cours.bethyeshoua.org/bibles/louis-segond?book=Ezek&chapter=1
- Comparaison Ézéchiel 10 : https://www.bible.com/fr/bible/compare/EZK.10.10%2C14%2C21-22
- Notes de traduction sur la différence bœuf/chérubin : https://tips.translation.bible/es/story/translation-commentary-on-ezekiel-1014/

## Ordre de la suite

1. **#37** : inventaire verset → affirmation, avec variantes de traduction.
2. **#38** : archives Drive, empreintes et distinction RETROUVÉ/RECONSTRUIT. `CANON_NOT_VERIFIED` tant que l'original n'est pas prouvé.
3. **#39–40** : étendre le graphe aux sources, scènes, hypothèses puis réexécuter les tests.
4. **#41–42** : évaluer le prototype Lovable et les vues individuelles ; ne pas prétendre que Blender/Godot ont été produits.
5. **#43** : audit par une personne distincte du producteur, avant décision humaine finale.

`python merkabah/tools/audit_candidate.py --json` retourne **BLOCKER** (erreur structurelle) ou **GAP** (preuve manquante) ; `--strict` refuse de conclure en présence de GAP. Ne pas interpréter une sortie non bloquante comme « fidèle à Ézéchiel ».
