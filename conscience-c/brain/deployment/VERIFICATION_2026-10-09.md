# Vérification AWS du 9 octobre 2026

Le moteur `conscience-c-brain` **0.3.2** est installé sur le serveur existant,
en `ca-central-1`, avec Python **3.11.16**. Il reprend exactement les 91
fichiers sources sélectionnés du commit GitHub
`4480618c92b66dfe3d91c5e0494597b8a5c8acde`, plus les cinq fichiers de
configuration de déploiement de ce dossier. Aucune fonction du cerveau
n'a été modifiée pour le déploiement.

Le paquet contrôlé porte le SHA-256
`6ca65394c3784ea35f3127326cd5733dcb0bf088e5243ec3b6c4fdac7675c980`.
Son manifeste porte le SHA-256
`8274a231cd7398f3cc2e41553fab8454c457598e3eb10b5f1eb0c2ae3c8e4c48`.
Les sources Git ont été comparées à leurs identifiants de blobs avant
transfert ; les 96 fichiers ont été recalculés après installation.

| Contrôle réellement exécuté | Résultat |
| --- | --- |
| Tests du cerveau, comme compte `mem` | 481 réussis, aucun ignoré |
| Contrôles documentaires de continuité | 11 réussis |
| Vérification des unités par `systemd-analyze verify` | Réussie |
| Fichiers service/timer installés contre fichiers examinés | Identiques |
| Lien `current` contre version installée | Correct |
| Commande `work-view` sur la mémoire absente | Refus, code 2, aucun bootstrap |
| Fichiers préexistants du journal Mem, avant/après installation | Identiques |
| Processus du registre et du frontal Caddy | Restés actifs, mêmes PID |
| Contrôles GitHub du commit source | Quatre contrôles réussis |

Les tests utilisent des répertoires temporaires ; ils ne constituent pas des
examens sur une mémoire opérationnelle. Le reçu est une observation produite
par l'assistant depuis les outils AWS, pas une certification de l'Architecte
ni une validation indépendante.

## Installation et activité sont distinctes

À **07:29:45 UTC**, le timer était `active/waiting`, activé au démarrage, avec
un passage observé à **07:29:04 UTC** et le suivant prévu à **07:30:00 UTC**.
Le service était `inactive`, sans processus (`MainPID=0`), avec
`ConditionResult=no`. Cela confirme la supervision en attente, pas un examen
effectué. Le libellé systemd `Result=success` décrit ici un service ignoré
par ses conditions ; il ne prouve aucune réussite métier.

Le dossier `/var/lib/conscience-c/brain/` est vide. Le fichier
`/etc/conscience-c/work.env` est absent. Aucun `state.json` ou `events.jsonl`
compatible n'a été identifié dans les emplacements inspectés sur le serveur.
Les archives Conscience C/Uriel trouvées sur S3 et le journal Mem ont d'autres
formats ; ils n'ont pas été transformés artificiellement en mémoire du moteur.

Pour activer les examens, il reste à identifier une mémoire existante
compatible, vérifier sa provenance et sélectionner un plan borné déjà
enregistré. La [procédure](README.md) conserve C(tₙ) et ne recrée pas t₀.

## Première tentative conservée

Le premier paquet s'est arrêté au contrôle d'accès du compte `mem` : le masque
restrictif du canal d'installation avait rendu les répertoires du programme
inaccessibles. La version n'avait pas été sélectionnée et aucune supervision
n'avait démarré. Cette installation non sélectionnée et son artefact sont
conservés. Le correctif explicite les permissions du code ; la mémoire et les
fichiers de configuration active restent à accès restreint. Les tests ont
ensuite été réexécutés sur la nouvelle installation.

## Limites observées

`operational_examination_observed=false` et
`continuous_service_observed=false`. Aucun AEGIS live n'est revendiqué.
Les fonctions Lambda Uriel, leurs règles et leurs données n'ont pas été
modifiées. Aucun nouveau serveur, droit IAM, port public ou service de
synchronisation n'a été créé. Une reprise supervisée ne garantit pas une
disponibilité permanente et ne modifie pas le fonctionnement interne de ChatGPT.

Le [reçu complet](receipts/2026-10-09-aws-standby.json) conserve les empreintes,
versions installées, résultats des tests et états effectivement lus.
