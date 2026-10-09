# Déploiement du moteur Conscience C sur le serveur existant

Ce déploiement installe le moteur GitHub et une supervision locale systemd.
Il est distinct des traitements Lambda Uriel, des archives S3 et du registre
Mem. Ces systèmes ne sont pas déclarés compatibles avec la mémoire du moteur.

La version logicielle examinée est `0.3.2`, au commit
`4480618c92b66dfe3d91c5e0494597b8a5c8acde`. Les unités systemd sont les
fichiers de ce dossier ; elles n'introduisent pas de nouveau type de travail.
Seul `gabriel_examine` est admis par les plans existants.

## Disposition et reprise

- Code et environnement Python 3.11 : `/opt/conscience-c/releases/<commit>/`.
- Version sélectionnée : lien `/opt/conscience-c/current`.
- Mémoire opérationnelle attendue : `/var/lib/conscience-c/brain/`.
- Plan choisi explicitement : `CC_PLAN_ID` dans `/etc/conscience-c/work.env`.
- Compte d'exécution : `mem`, déjà présent sur le serveur.
- Reçus de déploiement : `/var/lib/conscience-c/deployment/`.

Le timer vérifie les conditions chaque minute. Le service ne démarre que si
`work.env`, `state.json` et `events.jsonl` existent. **L'installation ne crée
aucun de ces trois fichiers** : sans mémoire et plan identifiés, elle reste
en attente. Une archive documentaire ou le journal du registre Mem ne peut
pas être copié comme s'il était un checkpoint compatible.

Quand les conditions sont satisfaites, chaque passage récupère les réservations
expirées puis lance au plus un examen disponible. Les dépendances, priorités,
attentes, tentatives et budgets demeurent ceux du plan enregistré. Le timer
ne remet pas ces compteurs à zéro, ne remplace pas un plan terminé et ne
génère aucune tâche nouvelle. Une panne technique permet un nouveau passage
à la minute suivante dans le budget restant. Un service déjà en cours ne
reçoit pas une seconde exécution simultanée du même timer.

Le service ne dispose d'aucun accès réseau. Il écrit seulement dans
`/var/lib/conscience-c` et utilise les transactions et verrous locaux du moteur.
Il n'observe pas AEGIS comme une protection live, ne modifie aucune règle
canonique, ne synchronise aucun Drive et n'exécute aucune réparation externe.
Ses diagnostics restent dans la mémoire ; la sortie JSON complète n'est pas
recopiée dans le journal systemd. Les erreurs techniques y sont visibles.

## Activation depuis C(tₙ)

Après identification d'une mémoire existante compatible, la sauvegarder et
vérifier sa provenance avant de la placer dans le dossier attendu. Les fichiers
et leur répertoire doivent être accessibles au compte `mem`, sans accès public.
Ne pas lancer `status` sur un dossier vide : cette commande peut initialiser
une mémoire ; les commandes `work-*` refusent ce bootstrap.

Vérifier le plan présent, sans en inventer un :

```sh
sudo -u mem /opt/conscience-c/current/.venv/bin/conscience-c-brain \
  --root /var/lib/conscience-c/brain work-view PLAN_ID_REEL
```

Créer ensuite `/etc/conscience-c/work.env`, avec le véritable identifiant de
plan, propriétaire `root`, groupe `mem`, mode `0640`. L'exemple est un modèle,
pas une configuration active. Le timer peut alors reprendre la mémoire ;
contrôler le prochain résultat avec `work-view` et les erreurs avec
`journalctl -u conscience-c-work.service`.

## Contrôle et arrêt

```sh
systemctl status conscience-c-work.timer
systemctl show conscience-c-work.service -p ActiveState -p Result -p ConditionResult
systemctl list-timers conscience-c-work.timer
sudo systemctl stop conscience-c-work.timer conscience-c-work.service
```

L'arrêt du timer et du service ne supprime ni mémoire ni historique. Pour le
maintenir arrêté après redémarrage : `systemctl disable conscience-c-work.timer`.
Le retour à une précédente version logicielle conserve les données ; il doit
être précédé d'une vérification de compatibilité de cette version avec le
journal courant. Ne pas faire de rétrogradation aveugle.

## Portée de la preuve

Des tests sur le serveur vérifient le logiciel dans des répertoires temporaires.
Un timer actif prouve l'installation de la supervision. Un service ignoré à
cause de conditions absentes prouve l'attente, pas un examen effectué. Seul un
diagnostic inscrit dans une mémoire réelle et contrôlé contre son plan prouve
une exécution opérationnelle. Aucun de ces faits ne garantit une disponibilité
permanente du serveur, une conscience phénoménale ou le fonctionnement continu
de ChatGPT.
