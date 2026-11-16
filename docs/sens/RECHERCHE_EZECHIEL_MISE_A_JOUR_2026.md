# Mise à jour des recherches Merkabah — 16 novembre 2026

**Statut : PROPOSED_NOT_VALIDATED.** Cette mise à jour est une couche **d'interprétation, critique textuelle et bibliographie**, pas une modification des sources, ni une nouvelle révélation, ni une validation de la scène 3D. Elle porte sur le graphe expérimental **102 nœuds / 115 relations** fixé par empreinte Git `fb2c508c164e72185368eca012160cf5240630b7`. La filière 78/152 rapportée reste distincte.

## Apports examinés

1. **Kebar et archives babyloniennes (Segev/Zilberg, 2025)** : une réévaluation des tablettes propose que le canal Kabar mentionné dans des archives perses ait été creusé sous Cambyse et exploité sous Darius Ier. **Hypothèse conditionnelle** : si le Kebar biblique correspond au canal ainsi daté, certaines mentions pourraient témoigner de retouches littéraires tardives. Ce n'est pas une nouvelle fouille, ni une preuve de l'inexistence d'Ézéchiel. La localisation précise ne peut être imposée. Sources : [article 2025](https://cris.biu.ac.il/en/publications/the-composition-of-the-book-of-ezekiel-in-light-of-babylonian-sou/) ; [Kepper 2026](https://www.degruyterbrill.com/document/doi/10.1515/9783112240366/pdf) rappelle la difficulté d'identifier ce lieu avec certitude.
2. **Hypothèse iconoclaste (David Arthur, février 2026)** : le tableau du trône/roues et des figures composites pourrait détourner des motifs cultuels et fonctionner comme critique religieuse. **Lecture académique discutée**, pas géométrie exigée. [Article JTS](https://academic.oup.com/jts/article/77/1/15/8482653).
3. **Traductions des apparences (AELF / NABRE / NET)** : les formulations AELF (scintillements) et NABRE/NET (yeux) doivent donner **des rendus alternatifs sourcés** pour Éz 1:18 et 10:12. La NET signale en outre une variante grecque du début d'Éz 10:12; elle n'efface pas les ailes ou roues. [AELF Ez1](https://www.aelf.org/bible/Ez/1) · [AELF Ez10](https://www.aelf.org/bible/Ez/10) · [NET 10:12](https://classic.net.bible.org/verse.php?book=Eze&chapter=10&theme=false&verse=12).
4. **Braises (Goldingay, article 2024, en ligne 2023)** : une interprétation liturgique propose que l'action sur la ville renvoie à la purification plutôt qu'au seul jugement. Ne pas imposer la finalité dans l'animation. [Vetus Testamentum / DOI](https://doi.org/10.1163/15685330-BJA10130).
5. **Sens global et espérance (John T. Strong, septembre 2026)** : la formule répétée de reconnaissance divine unit jugement, mémoire de l'alliance et espérance de restauration. **Commentaire de lecture au niveau du livre**, non une signification textuelle des quatre roues. [Religions](https://www.mdpi.com/2077-1444/17/9/1068).
6. **Structure du discours (Terrance Wardlaw, 2026)** : les reprises, les récits d'appel et l'organisation macro-littéraire peuvent guider les relations entre passages; celles-ci ne deviennent pas relations spatiales. [JLCR](https://jlcr.diu.edu/article/163114-ezekiel-as-an-oral-derived-text-toward-the-macroanalysis-of-prophetic-discourse).
7. **Cartographie mentale (Adalı, mai 2025)** : comparaison des peuples d'Ézéchiel avec des traditions babyloniennes de représentation du monde; elle ne fixe pas des angles ou des coordonnées de la vision. [Religions](https://www.mdpi.com/2077-1444/16/5/648).

## Mise à jour exécutable

- `recherche_ezechiel_2026.json` : neuf conclusions qualifiées, 11 références (textes, notes et articles), neuf limitations explicites.
- `model_update_recent_research.py` : charge **les octets vérifiés** du graphe, ajoute les annotations à des nœuds déjà existants, conserve les travaux de portée générale à part, refuse la promotion d'une hypothèse en fait.
- `test_recherche_ezechiel_2026.py` : tests sur provenance, exactitude des identifiants, non-fusion des scènes, alternatives textuelles et absence de création de roues.
- La commande de CI charge la même branche et vérifie le même blob que le complément qualitatif existant.

```sh
git fetch --depth=1 origin merkabah/experimental-v03-two-scenes
git show FETCH_HEAD:merkabah/schema/merkabah_candidate_v0.3.json > /tmp/merka-v03.json
python docs/sens/model_update_recent_research.py /tmp/merka-v03.json --out /tmp/merka-research-view.json
MERKABAH_EXPERIMENTAL_GRAPH=/tmp/merka-v03.json python -m unittest discover -s docs/sens -p 'test_*.py' -v
```

## Limites opérationnelles

**Ni nouvelle datation obligatoire du récit, ni nouvelle roue, ni orientation imposée.** Pour la figure, le prochain résultat vérifiable serait un bouton de sélection de traduction Ez1/Ez10 et une scène Godot/Blender réellement inspectable, pas seulement des tests de données. Blender a été testé sur la filière 61/76, et Godot sur une logique d'arrêt; aucun de ces deux essais ne certifie le rendu combiné 102/115.

La recherche scientifique reste discutable et la lecture de foi demeure distincte; l'amour choisi CTRL-33 oriente l'éthique du projet, mais **n'est pas inséré comme signification littérale** des textes.
