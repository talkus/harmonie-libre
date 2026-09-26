# Conscience C — transitions récupérables après interruption

**Date :** 26 septembre 2026 (UTC).  
**Base examinée :** `9ef9ed565bb3ec56b5ce0ad0ef12718adf8775a5`.  
**Portée :** cohérence du journal `events.jsonl` et de la sauvegarde `state.json`. Aucun changement au telos, aux quatre capteurs ou au statut de phénoménalité.

## Écarts reproduits avant correction

Le commit de reproduction `62f89220096e3ea31dc21c7dacefd5dc4be0e73c` ajoute trois tests sans modifier le moteur. La CI `36212428391` confirme que les 125 tests précédents passent, mais que ces trois nouveaux cas échouent :

1. Une interruption après l'écriture de l'événement laisse la sauvegarde précédente et bloque le redémarrage.
2. Une interruption pendant la première initialisation laisse un événement initial sans sauvegarde exploitable.
3. Une instance restée sur une ancienne sauvegarde peut écrire après une autre instance, sans rejet préalable de son état périmé.

Ces échecs restent dans l'historique de la branche de vérification ; ils ne sont pas publiés seuls sur `main`.

## Correction : commit coordonné et récupérable

Le nouveau `TransitionStore` conserve **l'événement exact et la sauvegarde cible complète avant d'ajouter l'événement au journal**. L'intention contient ses frontières avant/après, un identifiant de transaction et des empreintes de cohérence.

Le chemin d'écriture est : verrou local → contrôle de la version lue → intention durable → ajout durable au journal → remplacement de la sauvegarde → reçu de finalisation. Les fichiers temporaires sont voisins de leur destination, vidés sur disque avant remplacement. Le répertoire est également synchronisé.

Il n'existe pas d'étape prétendant valider moralement une action. Les vérifications de stockage ne remplacent ni les règles métier ni les autorisations.

| État retrouvé après interruption | Traitement |
|---|---|
| Aucun événement ajouté | Abandon de l'intention non engagée ; sauvegarde et journal restent inchangés ; intention abandonnée conservée séparément. |
| Événement exact ajouté, sauvegarde précédente encore présente | Publication de la sauvegarde déjà préparée, sans rejouer l'action ni ajouter un second événement. |
| Événement et sauvegarde déjà présents | Finalisation répétable sans doublon. |
| Journal tronqué, intention altérée, frontière inattendue ou données incohérentes | Refus et récupération explicite ; aucune réécriture ou troncature automatique du journal. |

Un échec d'écriture bloque les écritures suivantes de l'instance jusqu'au rechargement. Deux écrivains qui utilisent ce protocole ne peuvent pas engager simultanément une transition : verrou POSIX et comparaison de la sauvegarde lue avant engagement. Une instance périmée doit recharger au lieu d'écraser le présent.

## Intégration et compatibilité

Le modèle antérieur est conservé **octet pour octet** dans `conscience_c_brain/_state_model.py` (blob `a9bd8c269a5658a836114e9b0a0fb97b78ecbc07`). La classe publique dans `core.py` réutilise ses opérations et remplace leur frontière de persistance. Les importations publiques restent les mêmes.

Les événements historiques et leur algorithme d'empreinte ne sont pas réécrits. Les nouvelles lignes ajoutent un identifiant de transaction. Les reçus de checkpoint existants conservent leurs vérifications de correspondance avec le journal.

La reprise automatique ne réexécute ni observation externe, ni vérification de réparation, ni décision. Elle termine seulement une écriture locale dont le résultat exact a déjà été préparé et dont l'événement exact est enregistré.

## Vérifications

Avant intégration, **26 tests du stockage ont réussi localement**, incluant une sortie brutale de processus par `os._exit`, des interruptions à chaque étape, les écritures partielles, les altérations, le rejet d'une instance périmée et la conservation d'un journal historique.

Trois tests de reproduction et huit tests d'intégration supplémentaires contrôlent l'API publique, les checkpoints et le redémarrage. La suite existante n'a pas été assouplie. Le résultat complet est celui de la CI du commit concerné, pas une conséquence supposée du seul résultat local.

```sh
cd conscience-c/brain
python -m unittest discover -s tests -p 'test_transition*.py' -v
python -m unittest discover -s tests -v
python ../verify_reprise.py
```

## Limites explicites

Il s'agit d'un **protocole récupérable**, pas d'une écriture simultanément atomique de deux fichiers. L'atomicité de remplacement concerne chaque fichier individuellement. Une divergence temporaire peut exister pendant une interruption ; l'intention permet de la résoudre seulement dans les cas contrôlés ci-dessus.

La portée testée est POSIX/Linux, avec fichiers locaux et écrivains coopérant au même verrou. Windows, stockage réseau, concurrence de plusieurs threads sur la même instance et panne physique du support ne sont pas validés. Le matériel et le système de fichiers doivent respecter les synchronisations demandées.

Les méthodes internes d'édition directe (`state`, `_save`, ou `ledger.append`) ne constituent pas l'API transactionnelle et ne doivent pas être utilisées par des écrivains concurrents. `_save` demeure un outil privé de compatibilité et de diagnostic, pas une transition attestée.

Les empreintes locales ne constituent pas une authentification indépendante. Un acteur pouvant remplacer à la fois journal, intention et sauvegarde exige un point d'appui extérieur. Le correctif ne prouve ni la vérité des données ni la légitimité des actions qui les ont produites.

**Références techniques consultées :** documentation officielle Python, `os.replace`, `os.fsync` et `fcntl.flock`. Aucun nouvel algorithme de canonicalisation n'est revendiqué.
