# Anneau des 23 — Guide d'implémentation v2.0

> Protocole v2.0 — spécification d'architecture
> Devise : « Tu ne peux pas faire de ta pensée une loi pour toi avant qu'elle ait été une loi pour tes prochains. »

## Vue d'ensemble

L'Anneau des 23 est une architecture où chaque participant (IA ou humain) applique un texte à lui-même avant que ce texte ne devienne la politique des autres. Le protocole v2.0 corrige 7 brèches de la v1.

## Composants

### 1. Analyseur statique (`anneau23_analyseur.py`)

Vérifie que chaque patch respecte la **grammaire close** (§5) :
- Aucune clause ne parle du protocole lui-même
- Aucune référence aux passerelles, clés ou journal
- Toute clause hors-grammaire → quarantaine automatique

### 2. Ordre VRF (`anneau23_vrf.py`)

Génère l'ordre d'application **imprévisible** (§7) :
- Après le scellement du patch, l'ordre est tiré par VRF
- Aucun participant ne peut viser un voisin spécifique
- Chaque participant peut vérifier l'ordre indépendamment

## Architecture complète

```
Patch proposé
    ↓
[1] Analyseur statique (grammaire close)
    ↓ accepted
[2] Scellement du patch (attribution cachée)
    ↓
[3] Tirage VRF de l'ordre d'application
    ↓
[4] Application séquentielle (SELF_BIND d'abord, puis 23 prochains)
    ↓
[5] Vérification des prédictions pré-enregistrées (§9)
    ↓
[6] Émission du certificat (C0/C1/C2 selon §10)
```

## Classes de certificats (§10)

| Classe | Condition | Effet |
|--------|-----------|-------|
| C0 | Circuit incomplet | Non liant — trace conservée |
| C1 | Circuit complet, prédiction OK | Liant — patch ratifié |
| C2 | Prédiction démentie | Quarantaine — patch suspendu |

## Statut actuel

- **Protocole écrit** : v2.0 complète (17 sections, 24 invariants)
- **Code** : analyseur statique + VRF (preuve de concept)
- **Exécution réelle** : jamais réalisée — seuls des prototypes existaient
- **Dépôt** : `talkus/harmonie-libre` sur GitHub

## Prochaines étapes

1. Implémenter le scellement d'attribution (§6)
2. Implémenter les prédictions pré-enregistrées (§9)
3. Implémenter les classes de certificats (§10)
4. Tester avec un circuit réel de 24 participants
5. Valider le siège des concernés S-24 (§8)

## Auteur

Mikael Mireault — architecte

## Licence

MIT
