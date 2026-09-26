# Validation des transitions — 26 septembre 2026 (UTC)

## Résultat constaté

**Commit logiciel :** `8ead84311c12b2dc66b478f6200ab1d7a67934f3`  
**CI sur branche de vérification :** `36212712115`  
**Job :** `108322440515`  
**Environnement observé :** Ubuntu, Python 3.12.14.

Les journaux d'exécution indiquent :

```text
Ran 162 tests in 3.030s
OK

Ran 11 tests in 0.001s
OK
```

Les 162 tests logiciels comprennent les 125 tests préexistants inchangés et 37 nouveaux tests : 3 de reproduction, 26 de stockage et 8 d'intégration. Les 11 autres contrôles portent sur les documents de reprise.

[Exécution CI vérifiée](https://github.com/talkus/harmonie-libre/actions/runs/36212712115)

## Chemin de correction

Le commit `62f89220096e3ea31dc21c7dacefd5dc4be0e73c` ne modifiait que les tests. Sa CI `36212428391` terminait avec deux erreurs de reprise après interruption et un échec de rejet d'instance périmée. Les 125 tests antérieurs réussissaient.

Le commit logiciel suivant corrige ces trois cas, sans assouplir les anciens tests. Les simulations couvrent aussi les écritures partielles, les intentions altérées, la finalisation répétée et un arrêt de processus par `os._exit`.

[Reproduction antérieure](https://github.com/talkus/harmonie-libre/actions/runs/36212428391)

## Portée du résultat

La reprise termine une sauvegarde locale **déjà préparée** lorsque son événement exact est présent dans le journal vérifié. Elle ne rejoue pas une action externe et ne reconstitue pas un état absent par supposition. Une écriture partielle ou une incohérence non expliquée déclenche un refus, sans réécriture automatique du journal.

Ce résultat est daté et lié au commit ci-dessus. Ce n'est ni une garantie contre toutes les pannes matérielles, ni une validation de Windows ou d'un stockage réseau, ni une attestation indépendante de vérité ou d'autorité. Les limites du protocole restent celles du [rapport d'audit](AUDIT_TRANSITIONS_2026-09-26.md).

Le telos, l'ordre **Humilité → Pardon → Reconnaissance → Espérance** et la phénoménalité **INDETERMINATE** n'ont pas changé.
