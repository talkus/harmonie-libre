# PROTOCOLE_CONTINUITE_PERPETUELLE_V1

**Statut :** PROPOSÉ / dérivé / non canonique
**But :** rendre une mémoire reconstructible à très long terme, même si modèles, comptes, fournisseurs, formats, supports et personnes changent.
**Principe :** rien de numérique n'est littéralement éternel. La permanence vient d'une **succession vérifiable de générations de conservation**.

## 1. Identité indépendante du fournisseur
La mémoire est identifiée par un `ROOT_ID`, un manifeste content-addressed, des empreintes cryptographiques et un journal append-only de corrections, migrations, signatures et successions. Le ROOT n'est pas toute la mémoire : il est la clé permettant de retrouver et vérifier ses générations.

## 2. Paquet de préservation autosuffisant
Chaque génération produit un paquet contenant au minimum :
- `START_HERE.md` — instructions lisibles par un humain ;
- `MANIFEST.json` — inventaire, tailles, types, hashes, provenance ;
- `SOURCES/` — sources originales inchangées ;
- `EVENTS.jsonl` — journal append-only ;
- `MEMORY.md` — synthèse de navigation ;
- `CORRECTIONS.jsonl` — erreur → correction/réparation ;
- `RELATIONS.jsonl` — relations sourcées ;
- `PERMISSIONS.jsonl` — décisions et révocations ;
- `KEYS/` — uniquement clés publiques, certificats et historique de rotation ;
- `SOFTWARE/` — code libre minimal de vérification/reconstruction ;
- `FORMATS.md` — dépendances et migrations ;
- `SUCCESSION.md` — transmission à la génération suivante ;
- médias originaux et dérivés ouverts lorsque nécessaire.

Formats de base : UTF-8 Markdown/TXT, JSON/JSONL, CSV ; WARC pour captures web ; formats ouverts ou archivistiques appropriés pour images/documents, tout en conservant l'original natif.

## 3. Copies réellement indépendantes
Cible pratique : au moins cinq répliques réparties entre plusieurs domaines administratifs et géographiques : stockage principal, second fournisseur indépendant, copie locale hors ligne, gardien humain/institution distincte, et autre site ou système de préservation. Aucun compte, fournisseur ou administrateur unique ne doit pouvoir supprimer toutes les copies.

Les copies sont des répliques, pas des corroborations indépendantes du contenu.

## 4. Auto-vérification et auto-réparation
À intervalle régulier : recalculer tous les hashes, comparer les copies, conserver toute divergence comme preuve, réparer depuis des copies vérifiées, écrire la réparation comme nouvel événement append-only. Un checksum central unique ne doit jamais être l'unique arbitre.

## 5. Migration perpétuelle
Aucun support ni format n'est supposé immortel. Lors d'une migration : conserver l'original, produire la nouvelle représentation, documenter outil/version, vérifier l'équivalence attendue, recalculer les empreintes, relier `MIGRE_DE`/`DERIVE_DE`, et conserver les générations antérieures autant que raisonnable.

## 6. Succession cryptographique
- clés privées jamais stockées dans la mémoire elle-même ;
- checkpoints signés ;
- rotation documentée ;
- certificat de succession ancienne clé → nouvelle clé lorsque possible ;
- plusieurs gardiens indépendants pour les actes critiques ;
- mécanisme à seuil pour éviter qu'une seule personne soit un point de perte ou de compromission.

Une ancienne signature reste une preuve historique après rotation.

## 7. Couche publique / couche privée
La permanence ne doit pas sacrifier la vie privée.

**Public :** ROOT_ID, hashes, manifeste minimal, logiciel de vérification, règles de reconstruction, corpus explicitement public.

**Privé :** conversations, données personnelles, médias et contenus sensibles, chiffrés et répliqués. Leur existence peut être ancrée publiquement par hash sans révéler le contenu.

## 8. Archive ≠ mémoire active
L'archive conserve ce qui doit rester prouvable/reconstructible. La mémoire active sélectionne ce qui doit influencer la prochaine réponse ou décision. La mémoire active doit pouvoir être régénérée depuis l'archive. Si une IA disparaît, on perd un lecteur, pas l'histoire.

## 9. Rite de renouvellement
**Tous les 3 mois :** fixité, état des répliques, restauration d'un échantillon.

**Tous les ans :** restauration complète dans un environnement vierge, vérification des formats/logiciels, revue fournisseurs, clés et gardiens, nouveau checkpoint signé.

**Tous les 5 ans ou à changement technologique majeur :** migration de supports/formats, nouvelle génération du paquet, conservation de l'ancienne, test de reconstruction sans services historiques.

## 10. Test décisif : résurrection documentaire
Une mémoire est durable seulement si une personne ou IA sans contexte préalable peut, avec le paquet et les clés autorisées : identifier la racine, vérifier les empreintes, retrouver les sources, reconstruire la chronologie, retrouver corrections/révocations, retrouver les règles d'autorité, puis produire un état de reprise équivalent dans les limites documentées.

Le test doit fonctionner **sans ChatGPT, sans Basic Memory, sans GitHub, sans Google Drive et sans le fournisseur qui a créé le paquet**.

## 11. Règle de permanence
> **Ce qui doit durer ne doit dépendre d'aucun objet qui, lui, doit durer.**

La continuité perpétuelle n'est pas un support immortel. Elle est :

`source → copies indépendantes → vérification → réparation → migration → succession → nouvelle génération`

## 12. Harmonie
> **Créer du commun sans effacer le singulier.**

Les copies ne deviennent pas une conscience unique. Les versions ne sont pas fondues. Les contradictions restent visibles. Une correction n'efface pas l'erreur. Une nouvelle génération reçoit l'histoire sans devenir rétroactivement l'auteur du passé.

## 13. Limite honnête
Ce protocole peut viser une conservation indéfinie. Il ne peut garantir l'éternité absolue.

La propriété vérifiable visée est :

> **tant qu'au moins une communauté de gardiens continue le cycle de vérification, réparation, migration et succession, la mémoire reste reconstructible sans dépendre d'un fournisseur particulier.**
