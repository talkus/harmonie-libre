# Correspondance WORM Interchat / mémoire itérative — proposition non validée

**Point de départ rapporté par l'utilisateur (non relu dans le registre source):**
- WORM #298, tête annoncée `84c5af4b…`, 297 entrées étiquetées initialement, 891 étiquettes de passe 1.
- `etiquetteur.sh`, `etiquettes.jsonl`, 3 axes (DOMAINE, SENS, STATUT), corrections ultérieures par append.
- L'entrée #295 aurait subi un faux positif: le mot « dette » dans la description n'établit pas le statut DETTE.
- Banc déclaré 4/4 et clôture déclarée 6/6 — **pas de réexécution ici**.

## Dissymétrie / DISS-01
Le journal WORM est une source immuable et n'est **jamais modifié par ce prototype**.
La couche d'étiquettes est dérivée et révisable par nouveaux événements.
La vue courante sélectionne le dernier événement **par entrée ET par axe**; elle n'attribue aucune validation de vérité.

## Écart avec PR #56 initiale
Le module `iterative_labels.py` initial gère une étiquette épistémique par affirmation.
La mémoire WORM exige *trois* étiquettes de classement par entrée. Ne pas les confondre ni les fusionner.
`three_axis_sidecar.py` est l'adaptateur candidat, sans lien automatique avec le shell ou le stockage WORM.

## Garde-fous
- Taxonomie fermée passée par l'appelant : sans taxonomie complète relue, **aucune importation réelle**.
- Chaque append porte entrée, axe, valeur, source, groupe de filiation, acteur et raison.
- Double chaînage (global + par couple entrée/axe); sérialisation JSON ASCII; audit détecte altération locale.
- L'audit d'empreintes n'est pas une contre-vérification du journal, de l'authenticité des auteurs ou des preuves.
- Aucune promotion automatique de DETTE vers SCELLÉ ou de RAPPORTE vers REJOUE; une vérification indépendante reste requise.
- Les exemples de tests sur `synthetic-295` sont **synthétiques** et n'affirment pas le statut véritable de WORM #295.

## Avant tout raccordement réel
Obtenir les octets de `etiquettes.jsonl`, `etiquetteur.sh`, du manifeste WORM et les règles de taxonomie.
Vérifier format, cardinalités et empreintes **sur les octets originaux**; ne pas extrapoler le préfixe de hash.
Rejouer les tests négatifs puis réaliser une revue humaine des faux positifs sur STATUT.
Ne fusionner qu'après concordance contrôlée entre journal et étiquettes, sans toucher au canon.
