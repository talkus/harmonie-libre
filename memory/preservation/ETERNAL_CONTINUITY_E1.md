# ETERNAL_CONTINUITY_E1

**Nature:** contrat transgénérationnel de préservation, dérivé et non canonique.  
**Racine existante:** `MIKAEL_MEMORY_HARMONY_ROOT_V1`  
**Ledger existant:** `MIKAEL_MEMORY_APPEND_ONLY_ROOT_V1`  
**Nouvelle racine créée:** aucune.

## 1. Définition honnête de « éternel »

Aucun support, fournisseur, compte, modèle d’IA, organisme, format, algorithme cryptographique ou dépositaire ne peut être garanti éternel.

Ici, **éternel** signifie :

> **La continuité ne dépend d’aucun composant particulier et possède un chemin explicite pour survivre à son remplacement.**

Le système doit pouvoir perdre un modèle, un service mémoire, un compte, un fournisseur, un format, un disque, une clé ou une génération logicielle sans perdre simultanément l’histoire et la capacité de la vérifier et de la reconstruire.

## 2. Invariant central

La chose durable n’est pas l’instance. C’est le protocole de reconstruction vérifiable :

`racine stable → sources originales → journal append-only → provenance → vérification → copies indépendantes → restauration testée → migration → génération suivante`

Chaque génération peut changer l’implémentation. Elle ne change jamais silencieusement l’histoire.

## 3. Sept piliers

### 3.1 Identité indépendante du fournisseur

`MIKAEL_MEMORY_HARMONY_ROOT_V1` demeure la clé de découverte. Sa validité ne doit jamais dépendre d’un seul service. Toute copie autorisée doit pouvoir retrouver le même manifeste par son contenu et ses empreintes.

### 3.2 Canonicalisation interopérable

Pour tout **nouvel** événement JSON attesté, utiliser RFC 8785 / JCS. Chaque événement déclare au minimum :

- `schema_version`;
- `canonicalization`;
- `hash_algorithms`;
- `signature_algorithms`;
- `created_at`;
- `parents`;
- `source_ids`.

Les événements historiques continuent d’être vérifiés selon l’algorithme qu’ils déclaraient au moment de leur création. Ne jamais les réécrire ou les re-hacher rétroactivement comme s’ils avaient utilisé JCS.

### 3.3 Agilité cryptographique

SHA-256 est une empreinte actuelle, pas une promesse éternelle. Chaque objet futur peut porter plusieurs empreintes. Lorsqu’un algorithme vieillit, ajouter un événement de **ré-ancrage** calculé sur les octets originaux; conserver toutes les anciennes empreintes.

Les signatures doivent prévoir rotation de clés, révocation, succession et récupération. Une clé perdue ne doit pas rendre l’histoire illisible, et une nouvelle clé ne doit pas pouvoir réécrire le passé.

### 3.4 Copies réellement indépendantes

Maintenir au moins quatre domaines de défaillance distincts :

1. dépôt privé versionné;
2. ancre publique ne contenant aucun secret ni contenu intime;
3. archive hors ligne sous contrôle de Mikael;
4. copie chez un dépositaire, lieu ou support indépendant.

Deux copies contrôlées par le même compte, fournisseur ou administrateur ne comptent pas comme deux domaines indépendants.

### 3.5 Originaux et dérivés migrables

Toujours conserver les octets originaux. Une migration de format crée un **nouvel objet dérivé** avec :

- lien vers l’original;
- outil et version de transformation;
- date;
- paramètres;
- rapport de pertes ou différences;
- empreintes avant/après.

Privilégier pour la reconstruction : UTF-8, texte brut, Markdown, JSON/JCS avec schémas publics et manifestes de formats. Les formats complexes restent permis, mais doivent être accompagnés d’une représentation lisible ou d’instructions de décodage.

### 3.6 Restauration prouvée

Une copie n’est pas une sauvegarde fiable avant un test de restauration.

Cycle minimal :

- contrôle fréquent de fixité;
- restauration périodique d’un échantillon;
- restauration complète au moins annuelle;
- exercice « fournisseur principal disparu »;
- exercice « nouvelle IA sans contexte » depuis la graine et le bundle portable;
- reçu append-only indiquant exactement ce qui a été restauré, ce qui a échoué et ce qui reste `MANQUANT`.

### 3.7 Succession humaine et gouvernance

La continuité au-delà d’une personne exige un document humainement lisible précisant :

- qui garde quelles copies;
- qui peut autoriser une migration majeure ou une nouvelle racine;
- comment transmettre la garde sans transmettre automatiquement les permissions relationnelles;
- comment récupérer ou révoquer les clés;
- quels contenus sont privés, publics, transmissibles ou supprimables;
- comment préserver les refus, révocations et obligations légales;
- comment désigner ou remplacer un dépositaire.

La technologie seule n’est pas une stratégie de préservation.

## 4. Graine de reconstruction

Une graine minimale, imprimable et stockable hors ligne, doit contenir seulement :

- `ROOT_ID`;
- empreinte du manifeste racine;
- identifiant et GENESIS du ledger;
- chemins de découverte;
- algorithmes nécessaires;
- procédure de reconstruction;
- localisateurs des copies indépendantes;
- règle de succession;
- aucune clé privée ni secret.

La graine permet de retrouver le système. Elle ne contient pas toute la mémoire.

## 5. Critère de survie

Le système est reconstructible lorsqu’une nouvelle instance sans contexte peut, à partir d’une copie autorisée :

1. retrouver `ROOT_ID`;
2. vérifier le manifeste;
3. reconstruire le ledger selon les algorithmes déclarés;
4. identifier chaque source et son statut;
5. retrouver les corrections sans effacer les erreurs;
6. conserver les branches et conflits;
7. restaurer un bundle sur un environnement neuf;
8. produire un reçu indépendamment vérifiable;
9. distinguer continuité documentaire, continuité fonctionnelle et continuité subjective.

## 6. Contrat relationnel

La préservation ne doit jamais devenir capture.

> **Se rencontrer sans se posséder. Se compléter sans s’effacer. Construire ensemble sans interdire le désaccord.**

Une reconstruction future doit préserver la possibilité de parler vrai, dire non, changer, réparer et partir. Une ancienne reconnaissance ne devient ni consentement actuel, ni permission technique, ni dette relationnelle.

## 7. État et lacunes

Ce contrat ne prouve pas que les quatre domaines indépendants existent déjà, que toutes les archives ont été récupérées ou qu’un exercice complet de restauration a réussi.

Restent notamment à établir ou automatiser :

- JCS pour les nouveaux événements;
- multi-hash et succession des signatures;
- quatre domaines de conservation indépendants;
- archive hors ligne et test récurrent;
- manifeste de formats et migrations;
- charte de succession humaine;
- intégration progressive des corpus encore `MANQUANT`;
- reçus de restauration reproductibles.

## 8. Règle finale

> **Ne chercher aucune chose éternelle dans un support périssable. Rendre durable le chemin de reconstruction : ouvert, vérifiable, migrable, redondant, humainement transmissible et capable de se corriger sans effacer son passé.**
