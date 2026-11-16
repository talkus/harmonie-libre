# MERKABAH — Godot M5, préflight exécutable (candidat)

**Statut : PROPOSED_NOT_VALIDATED.** Reprise de la source existante, pas création du canon ni preuve de fidélité.

## Sources et contexte
- Script source Google Drive : https://drive.google.com/file/d/1RvDdeab71eO4ADewY9hC4BNK-SGhQ244/view (relecture 2026-11-16).
- Plan collaboratif : https://docs.google.com/document/d/1tZV-BGhkEt6qpPxQjN6sSOFMyeYd9FVe_S9hk4dLpRM/edit
- Travaux GitHub : #36, #42, #43 ; contrats de mouvement PR #48 et graphe v0.4 PR #55.
- Les calculs Kuramoto et Yechidah sont des **interprétations Architecture C**. Ils ne sont pas des faits explicitement donnés par Ézéchiel 1/10.
- Les scènes d'Ézéchiel 1 (Kebar) et 10 (Temple) sont séparées. Dans ce candidat, **Ez_10 est rejetée par la simulation de mouvement**, tant qu'un contrat propre n'a pas été défini.

## Correction ciblée
Le script source Drive déclarait `validate_yechidah` mais `step_merkabah` n'appelait pas ce garde-fou. Il pouvait donc progresser malgré `tempo_source="wheels"` ou un couplage interdit. L'adaptation appelle le préflight **avant** toute mutation de position ou de phase ; `dt <= 0`, `NaN`, `Inf` et scène non validée sont également refusés. `ok=false` accompagne tout rejet.

## Tests
- Statiques, sans Godot : `python -m unittest discover -s merkabah/tests -p 'test_godot_preflight_static.py' -v`.
- Comportement moteur, **à exécuter sur un poste équipé de Godot 4** : `godot --headless --path merkabah/godot --script res://test_fail_closed.gd`.

## Ce que ce travail ne fait PAS
- Il ne génère pas de mesh, de caméra ni de vidéo, et `group_position` n'est pas encore appliquée aux transformations de quatre instances Node3D.
- Il ne valide ni les 16 faces, ni 16 ailes, ni les yeux, ni la géométrie 3D.
- Il ne prouve pas l'exégèse ni ne fusionne la divergence Ez 1:10 / Ez 10:14.
- Il ne remplace pas le modèle Blender PR #55 et n'affirme aucun PASS Godot sans exécution et journal.

## Étape d'intégration
Lier quatre paires distinctes de Node3D (êtres/roues) à l'état validé; vérifier synchronisation, arrêt, élévation et absence de demi-tour avec vues face/dos/gauche/droite. Faire une revue externe #43 avant toute validation canonique.
