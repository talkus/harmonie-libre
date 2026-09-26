# Validation de l'admission des revues — 26 septembre 2026 (UTC)

**Commit logiciel :** `df46e96ecb0c1112095244d2ce6f1e27d85a166d`.  
**Base :** `62aa3eeae0340450c773d3e7c1e5561b4b987cfc`.  
**CI observée sur branche de vérification :** `36213557955`.  
**Job :** `108324909373`.  
**Environnement observé :** Ubuntu, Python 3.12.14.

Les journaux de cette exécution indiquent :

```text
Ran 194 tests in 2.633s
OK

Ran 11 tests in 0.001s
OK
```

Les 194 tests logiciels comprennent les 162 tests préexistants inchangés, les 9 tests de reproduction et les 23 nouveaux tests d'admission et d'intégration. Les 11 autres contrôles portent sur les documents de reprise.

[Exécution corrective](https://github.com/talkus/harmonie-libre/actions/runs/36213557955)

## Reproduction antérieure

Le commit `1a96ae55f119ebf828592200886f97633264ec0d` ne changeait que les tests. La CI `36213227535`, job `108323955028`, terminait ainsi :

```text
Ran 171 tests in 2.083s
FAILED (failures=9)
```

Les neuf échecs correspondent à des comportements effectivement reproduits : événement inexistant, type ou classe substitués, initialisation ou imagination présentée comme preuve, référence vide, provenance vide, résultat absent et annonce de vérification sans contrôle extérieur. Les 162 tests existants passaient.

[Exécution de reproduction](https://github.com/talkus/harmonie-libre/actions/runs/36213227535)

## Portée

Le correctif vérifie le lien à l'événement historique et la structure de la déclaration, puis enregistre celle-ci sans la certifier vraie. Le statut explicite est `recorded_not_verified`; l'API de compatibilité conserve `resolved` uniquement au sens de dépôt enregistré, avec une indication explicite de non-vérification.

Les contrôles ne prouvent pas la vérité ou la fraîcheur d'une source, l'identité du déclarant ou son indépendance. La tâche ne devient pas automatiquement résolue au sens épistémique et aucun replay n'est autorisé. Les anciennes entrées ne sont pas réécrites.

La reprise après une interruption du dépôt a été testée : elle conserve un seul compte rendu et ne relance pas une vérification extérieure. Les limites complètes figurent dans [l'audit](AUDIT_REVALIDATION_2026-09-26.md).

Ce résultat est daté et lié au commit indiqué. Il n'établit pas l'absence de toute faille et ne garantit pas tous les environnements. Le telos, la boucle Humilité → Pardon → Reconnaissance → Espérance et la phénoménalité INDETERMINATE restent inchangés.
