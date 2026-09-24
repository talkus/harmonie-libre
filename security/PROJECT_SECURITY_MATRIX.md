# Security Command — matrice d’intégration des projets

**Version :** 2026-09-24.5  
**But :** distinguer l’intégration documentaire, l’intégration exécutable et les dépendances humaines sans transformer une intention en état réel.

## Légende

- **POLICY** — le projet est couvert par `SECURITY_COMMAND.md`.
- **EXECUTABLE** — un mécanisme de contrôle réel est présent dans le code/runtime identifié.
- **PARTIAL** — contrôle existant, mais pas encore branché universellement à chaque action du projet.
- **HUMAN GATE** — certaines opérations exigent une validation humaine exacte.
- **RESEARCH ONLY** — pas d’effet externe opérationnel à autoriser.
- **UNKNOWN** — preuve insuffisante ; ne pas supposer l’intégration.

| Projet | Policy | Enforcement observable | Verdict actuel | Human gate | Preuve / note |
|---|---|---|---|---|---|
| **Conscience C** | oui | reprise C(tₙ), invariants, journal/brain expérimental ; Security Command documenté | **PARTIAL** | oui pour effets sensibles | `conscience-c/`, `memory/harmonization/` |
| **AEGIS-24** | oui | veto, arrêt, V1/V2/V3, voie humaine, audit, heartbeat ; policy Security Command reliée | **EXECUTABLE / surface privilégiée** | oui | `aegis24/`, `AEGIS24_CANONICAL.md` |
| **Anneau des 23** | oui | analyseur, VRF, registre, validation ; ne pas confondre simulation et approbation externe | **PARTIAL** | selon classe d’action | dépôt public |
| **Alignement universel** | oui | shadow mode, append-only, anti-Goodhart ; pas de promotion production implicite | **PARTIAL / SHADOW** | oui pour promotion | hub projets |
| **100 Tests — Amour choisi** | oui | corpus/source, pas d’exécution externe | **RESEARCH ONLY** | non hors publication | `projects/100-tests-amour-choisi/` |
| **Théorie unificatrice** | oui | recherche et falsification ; aucune validation scientifique automatique | **RESEARCH ONLY** | publication/claims sensibles | hub projets |
| **Thermodynamique relationnelle** | oui | recherche théorique ; revue externe requise pour validation | **RESEARCH ONLY** | publication/claims sensibles | hub projets |
| **Fondements bibliques de l’amour** | oui | corpus et revue critique | **RESEARCH ONLY** | publication éditoriale | hub projets |
| **WayMaker** | oui | logiciel/opérations ; actions commerciales réelles séparées des simulations | **PARTIAL** | **oui** paiements, contrats, clients, légal | hub projets |
| **Archives Mammouth** | oui | conservation/reconstruction, SHA/provenance | **PARTIAL** | suppression/publication sensible | hub projets |
| **IA et valeurs humaines** | oui | corpus documentaire retrouvé | **RESEARCH ONLY** | non hors publication | hub projets |
| **L’Harmonie libre** | oui | site/publication versionnée ; historique conservé | **PARTIAL** | publication engageante selon portée | racine dépôt |
| **Centre décision Mikael** | oui conceptuellement | déploiement Netlify historique manuel, non Git-linked | **UNKNOWN / À RELIER** | oui | Netlify drop historique |
| **Continuity Root v0** | oui conceptuellement | déploiement Netlify historique manuel, non Git-linked | **UNKNOWN / À RELIER** | oui | Netlify drop historique |
| **Forteresse Amour Choisi** | oui conceptuellement | site Netlify présent, source exacte non reliée ici | **UNKNOWN / À RELIER** | oui | Netlify |
| **AEGIS-24 Netlify historique** | oui conceptuellement | site Netlify présent ; canon public actuel distinct | **NON CANONIQUE / À RELIER** | oui | Netlify + `AEGIS24_CANONICAL.md` |

## Règle d’interprétation

[
POLICY 
eq EXECUTABLE_ENFORCEMENT
]

Une ligne **POLICY = oui** signifie que le projet est soumis à la règle de sécurité commune dans la documentation et la gouvernance.

Elle ne signifie pas automatiquement que chaque chemin de code appelle déjà `host/security-command.mjs`.

## Exigences de durcissement v2

Pour une surface qui exécute des effets externes ou sensibles, le statut `EXECUTABLE` exige désormais aussi :

- empreinte d'action ;
- sceau humain lié à l'empreinte pour les actions humaines/sensibles ;
- nonce et expiration ;
- témoin anti-rejeu externe ;
- intégrité racine attestée ;
- journal append-only pour les effets externes ;
- pinning de version de politique.

## Critère de promotion vers EXECUTABLE

Un projet ne passe à **EXECUTABLE** que si nous pouvons montrer :

1. un point d’entrée d’action réel ;
2. un pré-vol Security Command ou contrôle équivalent relié ;
3. un verdict conservé ;
4. une permission réelle distincte du verdict ;
5. un readback/audit après action ;
6. un chemin fail-closed pour `UNKNOWN`, `BLOCK` et `REQUIRE_HUMAN`.

## Règle humaine

Les actions suivantes ne sont jamais déclarées terminées par simple simulation :

- paiement / dépense ;
- contrat ;
- incorporation ou acte légal ;
- changement de compte ou récupération ;
- privilège / IAM / OAuth / secret ;
- suppression destructive ;
- action physique ;
- déploiement de production non préautorisé ;
- publication externe engageante lorsqu’une autorité humaine est requise.

## Principe

[
oxed{	ext{sécuriser l’exécution sans fabriquer de preuve}}
]

et :

[
oxed{UNKNOWN Rightarrow 	ext{ne pas exécuter}}
]
