# Audit ciblé des checkpoints — 26 septembre 2026 (UTC)

**Portée :** reçus de checkpoint, manifestes courants et rapports de transition.
**Base inspectée :** `7607e4f7844df1f2a5cfb13a635390a15940040e`.
**Statut :** correction logicielle testée ; ni démonstration de conscience, ni validation des vertus, ni nouvelle conclusion théologique.

## Écart reproduit

Huit tests négatifs ajoutés ont échoué sur la base inspectée : les vérificateurs acceptaient des objets qu'ils auraient dû refuser. Notamment :

- un reçu dont le contenu était modifié puis l'empreinte recalculée ;
- un identifiant de reçu jamais enregistré, associé à une frontière existante ;
- une frontière `GENESIS` inventée ;
- un manifeste modifié avec empreinte recalculée ;
- un rapport privé de tous ses événements, ou de son premier événement ;
- un type d'événement modifié sans modification de ses liens d'empreintes ;
- un reçu vérifié contre un journal altéré sans revérification de ce journal.

La présence d'une empreinte cohérente avec le document fourni ne suffisait donc pas à établir sa correspondance avec l'histoire conservée. Les assertions antérieures de « vérification indépendante » étaient trop fortes.

Les fichiers de base copiés pour l'exécution locale ont été comparés à leurs identifiants de blob Git :

| Fichier | Blob Git vérifié |
|---|---|
| `conscience_c_brain/core.py` | `fe75cc0ab083ec2a82791b60545bff8cf9444469` |
| `conscience_c_brain/ledger.py` | `f80601a17762abb017bec51f8cf983994b0b02ce` |
| `conscience_c_brain/models.py` | `fc88f246067d28e87fd0cddea56e24108867d421` |

## Correction appliquée

`read_verified()` renvoie les lignes exactes dont la chaîne vient d'être vérifiée. Le contrat de `verify()` est conservé : succès sans valeur de retour ; corruption signalée par exception.

Un reçu doit correspondre exactement à un événement `CHECKPOINT_RECEIPT` unique du journal vérifié. Son contenu, son identifiant, sa frontière précédente, son état capturé et les métadonnées optionnelles sont contrôlés. Les reçus historiques déjà enregistrés restent acceptés dans leur format d'origine ; aucune migration ni réécriture des anciens événements n'est effectuée.

Un manifeste courant est comparé à la projection courante, et non à son empreinte seule. Le nombre de transitions, l'étiquette de l'état et la tête du journal doivent correspondre au snapshot courant.

Un rapport doit correspondre à **tous** les événements de l'intervalle qu'il déclare : contenu des en-têtes, ordre, bornes et destination compris. Les bornes négatives, futures, booléennes ou non entières sont refusées. Un rapport vide reste valide pour un intervalle réellement vide.

La reprise utilise le reçu enregistré, ne recule pas l'état et n'exécute toujours aucun replay automatique.

## Vérifications reproductibles

```sh
cd conscience-c/brain
python -m unittest discover -s tests -p test_checkpoint_integrity.py -v
python -m unittest discover -s tests -v
python ../verify_reprise.py
```

Avant publication, les **30 nouveaux tests** du fichier `tests/test_checkpoint_integrity.py` ont réussi localement. Les huit tests de reproduction initiaux échouaient tous sur la version précédente. La suite existante n'a pas été assouplie. Le résultat complet après intégration doit être lu dans la CI du commit concerné, et non déduit de ce seul résultat local.

Les tests couvrent aussi les vrais reçus après redémarrage, les deux formats de reçu existants, les rapports légitimement vides, la conservation du journal et du snapshot lors des lectures, ainsi que le refus d'un journal absent ou mal formé sans tentative de le réparer.

## Limites maintenues

Ce contrôle établit une **correspondance au journal local vérifié**, pas une signature ni une attestation extérieure. Un acteur capable de remplacer tout le journal et ses empreintes exige un point de contrôle indépendant. L'algorithme historique d'encodage JSON n'est ni remplacé ni présenté comme RFC 8785/JCS.

La projection n'est pas un snapshot complet permettant de rejouer tout l'état. La cohérence de ses pointeurs ne démontre pas que chaque champ du snapshot a été reconstruit depuis le journal. Le prototype reste à écriture unique : ce correctif ne fournit ni transactions atomiques snapshot/journal, ni verrouillage multi-processus.

Les justificatifs fournis aux mécanismes de réparation ou de revérification restent des données déclarées par l'appelant. Ce correctif ne prouve ni leur vérité, ni l'identité ou l'indépendance de leur auteur.

**Telos, ordre Humilité → Pardon → Reconnaissance → Espérance et phénoménalité INDETERMINATE : inchangés.**
