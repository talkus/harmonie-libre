# Écorces / Étincelles — intégration effective de la matrice R33 aux vues Merkabah

**Statut : candidat non fusionné, couche SYMBOLIQUE optionnelle.**

Le document Drive [MATRICE INTÉGRALE DÉDUITE 288 (72×4)](https://docs.google.com/document/d/1nGJMjHhe1xVl0Z3-pMGDJRlWk-BL0DR68Sr1FXdVghA/edit) a été relu. Ses lignes ont été intégrées sous leur **texte et identifiant d'origine** : E001…E288, groupés en 72 portes N01…N72. Aucun intitulé n'a été inventé ou remplacé. Les références aux portes K22, miroirs Rudd et chaînes intra-porte sont préservées comme **archives de l'interprétation R33**, pas entités bibliques.

## Cardinalités réelles

- D1 : 72 **Origines** — Humilité.
- D2 : 72 **Écorces / kelipot** — Pardon.
- D3 : 72 **Actes / chemins inverses** — Reconnaissance.
- D4 : 72 **Étincelles relevées** — Espérance.
- Total **288 entrées de matrice**, et NON 288 étincelles explicitement observées dans Ézéchiel.

Chaque porte suit E[4k−3] → E[4k−2] → E[4k−1] → E[4k] → R'. Cela provient de l'archive R33, pas des versets bibliques. Les 14 ancrages historiques revendiqués dans l'index R33 demeurent des références documentaires, pas quatorze preuves validées dans cette étape.

## Connexion avec les scintillements d’Ézéchiel

Le graphe biblique **reste identique** (102 nœuds, 115 relations sur deux scènes Ez1 et Ez10). Le nouveau programme `model_integrer_ecorces_etincelles.py` reproduit la totalité du graphe, les nouvelles notes exégétiques et la matrice symbolique, **dans trois compartiments identifiables**.

La relation de sens possible est : scintillement/yeux selon les traductions → image de lumière perceptible → étincelles évoquant une possibilité de réparation. Elle reçoit le statut `SYMBOLIC_VIEW_OF_SCINTILLATIONS_NOT_GRAPH_EDGE`, **jamais** un statut TEXTUEL. Il n'est pas affirmé qu'une roue = une vertu, qu'une étincelle E002 serait réellement sur une jante, ni que la Kabbale lourianique et le prophète aient formulé la même doctrine.

L'exploration visuelle pourra proposer le mode **« Analogies R33 »**, désactivé par défaut, qui révèle les 72 cycles de réparation sans confondre une porte, une écorce ou un chiffre avec un objet de la scène.

## Comment générer la vue complète

```sh
git fetch --depth=1 origin merkabah/experimental-v03-two-scenes
git show FETCH_HEAD:merkabah/schema/merkabah_candidate_v0.3.json > /tmp/merka-v03.json
python docs/sens/model_integrer_ecorces_etincelles.py /tmp/merka-v03.json --out /tmp/merka-avec-288.json
MERKABAH_EXPERIMENTAL_GRAPH=/tmp/merka-v03.json python -m unittest discover -s docs/sens -p 'test_*.py' -v
```

L'artefact de CI inclura le modèle et les 288 descriptions intégrales. Source de départ : [matrice intégrale R33](https://docs.google.com/document/d/1nGJMjHhe1xVl0Z3-pMGDJRlWk-BL0DR68Sr1FXdVghA/edit). Le graphe à 78/152 rapporté par ailleurs reste distinct et non fusionné.
