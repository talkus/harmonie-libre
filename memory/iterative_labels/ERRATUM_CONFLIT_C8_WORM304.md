# Correction de lecture C8 / réception WORM #304 — sans effacement

Statut : **CORRECTION_DOCUMENTAIRE**, non-ratification du canon. Date de vérification : 2026-11-15 (Québec), nuit du 15 au 16 UTC.

## Divergence signalée

Une réception WORM #304 rapporte que le rapport de rapprochement GitHub « déclare toujours les octets non retrouvés » et que la branche semble inchangée. Cette lecture est **exacte pour le document ancien** `CTRL36_R33_V22_RECONCILIATION.md`, mais ne couvre pas le rapport ajouté ultérieurement.

## Deux pièces, deux points de connaissance K

- Pièce initiale, conservée intacte : `CTRL36_R33_V22_RECONCILIATION.md` ; `SOURCE_DOCUMENTAIRE_RETROUVEE, EXECUTION_NON_REJOUEE` **au moment de sa rédaction**.
- Pièce ultérieure, relue directement sur la même branche :
  `CTRL36_GOVERNANCE_CANDIDATE_AND_REPLAY.md` ; blob GitHub `402dee3e55effbdc9c5fc37c8f43a9a92e7191a5`.
  Elle consigne les mesures du ZIP 530217 octets, du script 85918 octets, de SQLite 1921024 octets, 8/8 tests spécifiques PASS, 18 passes sur quatre unités, `label-iteratif` exit 0 et racine Merkle reproduite avec le code livré.
- La PR correspondante est #56 : https://github.com/talkus/harmonie-libre/pull/56

## Effet du rapprochement

Le signalement « aucune contre-validation plus récente trouvée sur GitHub » est **à corriger** après consultation du second fichier. L'ancienne pièce n'est pas supprimée; son statut est historicisé, et le second rapport est le dernier état documentaire consulté.

Les scellures WORM #303/#304 et leurs têtes restent des **déclarations de la réception externe**, non vérifiées directement ici; ce correctif GitHub ne les modifie pas.

## Limites non levées

La suite 58/58 a été annoncée, mais l'essai isolé consigné dans le second rapport a donné 30 PASS / 1 FAIL / 27 ERROR en raison de dépendances historiques absentes ou différentes. Le sceau `O_S24_EXTERNE` n'est pas authentifié par la seule présence d'une valeur ou d'un hash dans les fichiers; il exige une preuve externe. Aucune fusion ni promotion de statut automatique.

**Règle : correction ≠ effacement ; temps de l'événement T stable, connaissance K augmentée ; R < E.**
