# Merkabah : graphe candidat, contrôles et esquisse Blender

Ce travail prolonge le [plan Merkabah](PLAN_COLLABORATIF.md) et les tâches
[#39](https://github.com/talkus/harmonie-libre/issues/39),
[#40](https://github.com/talkus/harmonie-libre/issues/40) et
[#41](https://github.com/talkus/harmonie-libre/issues/41). Il ne valide pas une représentation biblique.

## Deux scènes, avec leurs sources

`schema/merkabah_candidate_v0.3.json` contient deux scènes distinctes. Pour la
première, les faces sont humain, lion, taureau et aigle ; pour la seconde, elles
sont chérubin, humain, lion et aigle. Ézéchiel 10:15,20 identifie les êtres aux
vivants vus auparavant, mais la correspondance entre chaque numéro d'une scène
et l'autre reste un choix du modèle. L'identité éventuelle de la face de
chérubin et du taureau n'est pas établie par ce modèle.

Les références par nœud et relation renvoient à l'édition AELF consultée ; pour
les yeux aux jantes la référence est explicitement NABRE/USCCB, car les
traductions ne formulent pas toutes Éz 1:18 de la même manière. La géométrie,
les orientations non indiquées et le nombre de mains demeurent indéterminés.
Les étiquettes d'ailes par numéro sont une manière de représenter les fonctions
décrites, pas des identités individuelles données par le texte.

Sources : [AELF Éz 1](https://www.aelf.org/bible/Ez/1),
[AELF Éz 10](https://www.aelf.org/bible/Ez/10),
[NABRE Éz 1](https://bible.usccb.org/bible/ezekiel/1) et
[NABRE Éz 10](https://bible.usccb.org/bible/ezekiel/10).
Le texte appartient à ses éditeurs : ces fichiers ne le reproduisent pas.

Le JSON est généré par `python merkabah/schema/build_candidate_v03.py`. Le schéma
formel est `schema/merkabah_v03.schema.json`. La v0.1 reste disponible inchangée ;
la v0.3 est une proposition expérimentale, pas une substitution au canon ni une décision.
Une autre proposition v0.2 existe dans la [PR #47](https://github.com/talkus/harmonie-libre/pull/47) ;
ces approches doivent être comparées avant toute fusion. Le schéma v0.3 est
expérimental et n'est pas compatible directement avec le schéma candidat
`merkabah.schema.json` : les noms des champs et les identifiants de scène diffèrent.
Il faut définir une conversion et la tester avant de les réunir.

## Contrôles

Depuis la racine du dépôt :

```sh
python merkabah/validate_graph_v03.py
python -m unittest discover -s merkabah/tests -v
```

Le validateur contrôle la séparation des scènes, les références, les identifiants,
les propriétaires des ailes, faces et roues, et les relations représentées. Les
tests introduisent des suppressions, doublons et échanges entre scènes. Le schéma
est également vérifié si `jsonschema` est installé. L'adaptateur `to_networkx`
conserve les relations multiples si `networkx` est installé ; les dépendances
optionnelles figurent dans `requirements-test.txt`.

`validate_motion_samples.py` examine des positions et orientations **échantillonnées**.
Il compare la translation de chaque roue à celle de son être et vérifie que
l'être ne tourne pas entre deux échantillons. L'écart fixe entre eux est une
simplification choisie pour ce scénario. Cela ne vérifie ni le rendu, ni les
intervalles entre échantillons, ni l'origine du souffle, ni la physique réelle.

## Blender

La scène `blender/generer_v03.py` lit le graphe **v0.3**. Avec Blender installé :

```sh
blender -b --factory-startup --python-exit-code 1 --python merkabah/blender/generer_v03.py
blender -b --factory-startup --python-exit-code 1 --python merkabah/blender/generer_v03.py -- --scene ez10
```

Elle produit dans `merkabah/blender/generated/` une scène `.blend`, un export
`.glb`, une image et un rapport par scène. C'est une esquisse statique :
quatre corps, seize étiquettes de faces, seize ailes et quatre roues. Les
couleurs, positions, angle des roues et nombre de marqueurs d'yeux sont des
choix graphiques. Elle ne comporte pas encore mains, jambes explicites, charbons
ou animation ; ses compteurs ne prouvent ni fidélité visuelle ni contact des
ailes. `sources/AUDIT_CONTRADICTOIRE_LOVABLE.md` décrit les limites d'un autre
prototype, qui n'est pas relié dynamiquement au graphe GitHub.

Godot, les tests NetworkX dans un environnement
équipé, l'inventaire complet des archives et une revue biblique humaine restent
à réaliser. Aucun agent n'est présenté comme humainement indépendant.
