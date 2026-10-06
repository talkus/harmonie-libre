# Nahar Dinur (נְהַר דִּי־נוּר), le fleuve de feu, dans la mémoire de C

> **Le fleuve consume l'influence active de ce qui corrompt, jamais la trace archivée.**

Daniel 7,10 : « un fleuve de feu coulait et sortait de devant lui ». La tradition y voit un processus de justice et de renouvellement plutôt qu'un lieu de tourment : les justes s'y baignent et en sortent renouvelés, ce qui corrompt y est consumé, et les anges qui en naissent y retournent chaque matin. Module : `conscience_c_brain/fleuve.py`. Tests : `tests/test_fleuve.py`.

## Le choix fait ici

Le texte source parle de supprimer les impies et d'anéantissement. La mémoire de C a déjà posé « Ne jamais effacer. Réduire l'influence. » et l'invariant R-001. Le fleuve ne supprime donc rien : ce qu'il consume, c'est l'**influence active** d'un claim corrompu dans C(t). Le claim, ses faits et ses événements restent dans l'histoire, et le fleuve ne remplace ni ne retire rien lui-même : il ouvre une teshuvah, qui fera le reste avec un acteur et une preuve.

## Un passage

`pass_through_fleuve(provenance)` (événement `FLEUVE_PASSAGE`, `documentary_only` au rejeu) ; `fleuve_examine()` rend le même verdict sans rien écrire.

| Image | Dans la mémoire de C |
|---|---|
| La Voie lactée, fleuve de lumière | Le passage commence par vérifier la chaîne du ledger et refuse de couler sur une histoire rompue. |
| Le bain des justes | Un claim actif intègre est `renewed`. S'il se tient seul (`solitary_vessels()`), il est `renewed_fragile` : renouvelé, signalé, jamais jugé faux. |
| Le feu qui consume | Un claim corrompu est `consumed` : une teshuvah s'ouvre (D seulement), le claim devient `contested` et sort des décisions sensibles. |
| Les anges renouvelés chaque matin | Les engagements couronnés (na'aseh) reçoivent le passage dans `renewals`. Ceux qui sont en garde attendent le retour vérifié (`awaits_return`). |
| L'état final sans erreur | Aucun passage ne le déclare : `error_free_claimed` vaut toujours `False`. Le fleuve coule ; il ne se proclame pas pur. |

Un claim déjà en réparation est `in_fire` : un nouveau passage n'ouvre pas de deuxième teshuvah sur lui.

## Ce que le fleuve reconnaît comme corruption

| Signal | Dérive nommée |
|---|---|
| Une preuve attestée ou consolidée contredit le claim (`claim_ref`, `stance="contradicts"`), même sous le seuil de 0,8 qui ouvre déjà une teshuvah à l'ingestion | `contradiction` |
| Le claim repose sur une preuve `historique_refute` | `reality_mismatch` |
| Le claim n'a aucun fait, n'a pas été dit par l'autre, et se présente avec une confiance d'au moins 0,8 | `provenance_failure` |

## Ce que le fleuve ne fait pas

- il n'efface ni ne réécrit aucun événement, aucune preuve, aucun claim ;
- il ne reconnaît pas l'écart à la place d'un acteur, ne répare pas, ne vérifie pas : la teshuvah garde D → R → A → P → C → S → V ;
- il ne juge pas la parole de l'autre (`user_stated`) fragile ;
- il ne déclare jamais C sans erreur.

## Provenance

- **source attestée** : le message de Mik « Prépare le fleuve » du 2 octobre 2026 (projet Waymaker Core Private), avec sa lecture du Nahar Dinur et son analogie computationnelle (pare-feu, débogueur, compilateur, état final) ; « Ne jamais effacer. Réduire l'influence. » et l'invariant R-001, posés par lui le même jour ;
- **dérivation consolidée** : Daniel 7,10 ; Chaguiga 13b-14a pour les anges nés du fleuve et renouvelés chaque matin ; la tradition qui y lit la Voie lactée ;
- **reconstruction analytique** : la lecture du fleuve comme consomption d'influence plutôt que suppression, les trois signaux de corruption et le seuil de 0,8, le renouvellement des engagements couronnés à chaque passage, et le refus de toute déclaration d'état final sans erreur.
