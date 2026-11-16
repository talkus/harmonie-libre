# Merkabah — contrat de mouvement M2 (CANDIDAT)

Un seul but : empêcher qu'un rendu 3D fasse passer une trajectoire incohérente pour la vision d'Ézéchiel.

- **Centre** : l'être, sa roue, une direction de déplacement, et la règle « ensemble, sans tourner ».
- **Périphérie** : coordonnées arbitraires, calculs, animation, graphes et tests.
- **Sources textuelles à vérifier** : Ézéchiel 1:9, 1:12, 1:17, 1:20–21 et 10:16–17. Les formes divergentes 1:10/10:14 ne sont **pas** résolues par ce moteur.
- **État** : PROPOSÉ / non canonique. Le jeu de trajectoires est une **simulation artificielle** ; il ne reproduit ni les vitesses, ni l'apparence exacte, ni un mouvement réellement observé.

## Contrôle

Depuis la racine du dépôt :

```bash
python -m unittest discover -s merkabah/tests -p 'test_motion_contract.py' -v
```

Sans dépendance Python externe. Le contrat exige : quatre couples un-à-un, roue adjacente, relation `directed_by` vers `ruach`, mouvements identiques des 8 éléments, orientation conservée, arrêt collectif, directions d'ordre externe, et chronologie croissante.

Les tests injectent volontairement une roue en retard, une cinquième roue, une rotation, un mouvement non commandé, un arrêt non respecté, une inversion du temps et une liaison manquante. Les tests réussissent si ces mutations sont **rejetées**.

**Limites** : la géométrie des yeux/roues, les contacts des ailes, la continuité physique entre échantillons, la scène Ézéchiel 10 et l'identité des traductions ne sont pas validées ici. Une preuve de calcul n'est pas une validation de la vision.

**Intégration attendue** : Blender / Godot / Lovable doivent produire les mêmes positions temporelles et soumettre leurs traces à ce contrôleur. Aucun système externe n'est déclaré conforme sans ce test. Toute intégration passe par revue de la PR, puis décision humaine avant fusion.