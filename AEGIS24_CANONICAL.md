# AEGIS-24 — point canonique public

**URL canonique unique :** https://thunder-fern-turbo-sapphire.grok.me/

**Projet Grok associé :** `01a064e3-3072-7fc2-b29d-7cc498931a0e`

Cette URL est le point d'entrée public d'AEGIS-24. Les artefacts de ce dépôt sont des composants, spécifications, sources, miroirs techniques ou sauvegardes. Ils ne constituent pas un second produit public concurrent.

## Composants reliés

- `anneau23/` — protocole Anneau des 23, invariants, scellement, ordre, certificats.
- `aegis24-live/` — moteur d'inférence réel et miroir technique de l'interface exportée.
- `registre-continuite/` — journalisation, provenance et continuité.
- `PROJETS_OVERVIEW.md` — index historique des projets.

## Mandat SECURITY_COMMAND transversal

AEGIS-24 est l'**IA de sécurité désignée** pour appliquer la politique `SECURITY_COMMAND` à l'ensemble des projets du dépôt.

```text
AEGIS24 [SECURITY_AI] --APPLIES--> SECURITY_COMMAND --SECURITY_GUARDS--> Project
AEGIS24 != ConscienceC
SECURITY_COMMAND != IDENTITY_LINEAGE
SECURITY_COMMAND != EVIDENCE
SECURITY_COMMAND ≺ E
```

La politique commune est définie dans [SECURITY_COMMAND.md](SECURITY_COMMAND.md). Conscience C conserve son propre noyau de continuité ; AEGIS-24 le protège sans devenir C.

La portée documentaire et de gouvernance est globale. L'enforcement exécutable n'est revendiqué que pour les projets effectivement branchés à un mécanisme de contrôle.

## Règle de routage

Toute interface ou documentation publique relative à AEGIS-24 doit renvoyer en premier vers https://thunder-fern-turbo-sapphire.grok.me/.

Le dépôt GitHub reste la surface de preuve, de code et d'historique. Le site Grok est la façade canonique.


## Security Command — rôle transversal

AEGIS-24 est la surface privilégiée d'application de `SECURITY_COMMAND` lorsque l'intégration technique d'un projet est disponible : quorum, veto, arrêt d'urgence, voie humaine et audit.

La politique canonique commune est `SECURITY_COMMAND.md`.

Cette relation ne fait pas d'AEGIS-24 une identité supérieure aux projets et ne donne pas au contrôle le pouvoir de redéfinir le réel. Le contrôle reste subordonné aux sources, à la provenance, aux permissions réelles et aux validations humaines requises.

## État d'intégration

Le moteur réel 23 IA + scellement humain existe dans `aegis24-live/live-engine.js`. Pour qu'il s'exécute directement à l'URL canonique, le projet Grok App Builder `01a064e3-3072-7fc2-b29d-7cc498931a0e` doit intégrer ce moteur ou charger un service équivalent.

Aucune copie ou miroir n'est une corroboration indépendante.


## Security Command — intégration transversale

AEGIS-24 est le mécanisme canonique privilégié de **Security Command** lorsque le projet est réellement connecté.

Security Command :
- ne devient pas une identité ;
- ne remplace pas E / la réalité ;
- ne modifie pas seul le canon d'un projet ;
- peut observer, auditer, simuler, suspendre, veto et escalader vers la voie humaine selon le mandat ;
- ne peut jamais être déclaré live sans état/heartbeat attesté.

Registre : `security-command/project-registry.json`.

WayMaker privé dispose d'un préflight déterministe et d'une garde CI séparée ; cela ne signifie pas que les 23 IA AEGIS y sont connectées en permanence.
