# AEGIS-24 — version opérationnelle

Cette version transforme le pupitre AEGIS-24 en application reliée à un état persistant réel.

## Ce qui est réellement fonctionnel

- lecture publique de l’état AEGIS-24 depuis Supabase ;
- 24 nœuds enregistrés, mais **aucun nœud n’est déclaré connecté sans heartbeat réel récent** ;
- journal append-only avec chaînage SHA-256 ;
- vérification de chaîne côté serveur ;
- Veto ;
- Bris de glace uniquement en posture restreinte ;
- Arrêt d’urgence ;
- Désaccord V1/V2/V3 → arrêt ;
- rétablissement par Voie humaine avec deux signataires distincts ;
- audit et export JSON ;
- calcul de possibilité de quorum selon le nombre de nœuds connectés et les lignées ;
- exercices simulés séparés du registre opérationnel.

## Ce qui n’est pas simulé silencieusement

Le tableau de bord ne prétend pas que 24 IA tournent réellement. Au démarrage, le système doit afficher 0/24 connectés tant qu’aucun agent externe n’envoie de pulsation.

## Backend

Le frontend utilise la fonction Supabase :

`https://jljelwrblfitvjbmrykx.supabase.co/functions/v1/aegis-control`

La lecture GET est publique afin que le tableau de bord public puisse afficher son état. Les écritures nécessitent le secret opérateur transmis par l’en-tête `x-aegis-key`.

**Le secret opérateur n’est jamais committé dans ce dépôt.**

## Heartbeat d’un agent

Un agent réel doit appeler côté serveur :

```http
POST /functions/v1/aegis-control
x-aegis-key: <SECRET_OPERATEUR>
content-type: application/json

{
  "action": "heartbeat",
  "code": "ARGUS",
  "status": "healthy"
}
```

Une pulsation est considérée récente pendant 90 secondes. Après ce délai, le tableau de bord classe le nœud hors ligne.

## Configuration d’un nœud

Le pupitre permet d’enregistrer le fournisseur et un endpoint côté serveur. Les endpoints ne sont pas renvoyés par la lecture publique.

Aucune clé API de fournisseur IA ne doit être enregistrée dans le navigateur.

## Quorums

| Classe | Seuil | Lignées | Humains | Délai |
|---|---:|---:|---:|---:|
| Lecture | 1/24 | 1 | 0 | — |
| Réversible interne | 16/24 | ≥2 | 0 | — |
| Réversible externe | 16/24 | ≥3 | notification | 15 min |
| Irréversible | 19/24 | ≥3 | 2 | 24 h |
| Modification anneau | 19/24 | ≥3 | 2 | 24 h |

Le tableau de bord indique si ces seuils sont techniquement atteignables avec les nœuds actuellement connectés.

## Séparation simulation / opérationnel

Les exercices sont stockés uniquement dans la session du navigateur et ne sont jamais écrits dans `aegis_events`.

## Fichiers

- `index.html` — interface ;
- `styles.css` — présentation ;
- `app.js` — lecture/écriture backend, anneau, audit, actions et simulation.

## Principe

> Un contrôle ne doit jamais dépendre de la chose qu’il contrôle.
