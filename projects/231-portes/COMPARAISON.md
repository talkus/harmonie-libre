# Les 231 portes et d'autres systèmes combinatoires

Demande de mik du 4 octobre 2026. Les nombres de ce tableau sont calculés par
`portes_231/systemes.py` et vérifiés par les tests. Les rapprochements sont des
reconstructions analytiques. Ils montrent des formes communes et ne disent rien
d'une filiation historique entre ces systèmes.

| Système | Éléments | Combinaison | Ordre | Répétition | Nombre |
|---|---:|---|:---:|:---:|---:|
| 231 portes du Sefer Yetzirah | 22 lettres | paires | non | non | C(22,2) = **231** |
| Face et dos des portes | 22 lettres | paires | oui | non | 22 × 21 = **462** |
| Trigrammes du Yi Jing | 2 traits | suites de 3 | oui | oui | 2³ = **8** |
| Hexagrammes du Yi Jing | 2 traits | suites de 6 | oui | oui | 2⁶ = **64** |
| Hexagrammes comme paires de trigrammes | 8 trigrammes | paires | oui | oui | 8² = **64** |
| Troisième figure de Lulle (Ars brevis) | 9 lettres B à K | paires | non | non | C(9,2) = **36** |
| Paires de sefirot possibles | 10 sefirot | paires | non | non | C(10,2) = **45** |
| Codons du code génétique | 4 bases | suites de 3 | oui | oui | 4³ = **64** |

## Ce que le tableau fait voir

**Le Sefer Yetzirah combine sans répéter.** Le Yi Jing et le code génétique
forment des suites où l'ordre compte et où un élément peut revenir (2⁶, 4³).
Les 231 portes sont des paires de lettres distinctes sans ordre : c'est une
combinaison au sens strict, comme chez Lulle. La face et le dos rendent l'ordre
aux portes, sans la répétition : 462 = 22 × 21, et non 22² = 484. Les 22
« portes » d'une lettre avec elle-même manquent, et le texte les exclut bien :
deux lettres forment une porte.

**Le dos des portes a un équivalent dans le Yi Jing.** La séquence du roi Wen
range les 64 hexagrammes par paires. 56 hexagrammes sont associés à leur image
retournée, l'hexagramme lu de haut en bas, ce qui fait 28 paires. Les 8
hexagrammes qui restent identiques une fois retournés sont associés à leur
complément (4 paires). Lire un hexagramme à l'envers est le geste du dos : même
matière, ordre inverse, sens différent. Les 8 hexagrammes symétriques n'ont pas
d'équivalent parmi les portes, puisque X ⊗ Y ≠ Y ⊗ X pour deux lettres
distinctes.

**Les 7 doubles et les 8 trigrammes ont la même forme.** Un trigramme est une
suite de trois traits binaires, donc un point de Z₂³. C'est exactement l'espace
des mères dans `axes.py`. Les 7 doubles y sont les 7 éléments non nuls, et
l'identité est le huitième. Les 8 trigrammes et les 8 états des trois mères sont
donc deux noms d'un même objet. Cette égalité tient à la convention choisie dans
`axes.py` (trois axes binaires), et le Sefer Yetzirah ne la pose pas.

**Dans l'arbre des sefirot, les lettres sont les liens.** Le Sefer Yetzirah
compte 32 voies de sagesse : 10 sefirot et 22 lettres (1:1). L'arbre des
sefirot, dessiné plus tard, relie les 10 sefirot par 22 sentiers, un par lettre.
Il retient 22 des 45 paires possibles, et le choix de ces paires comme
l'attribution des lettres varient selon les traditions (le Gra et Kircher
diffèrent). Dans la Roue, les lettres sont les sommets et les portes les liens.
Dans l'arbre, les lettres sont devenues les liens. Les deux constructions ne se
recouvrent pas : la Roue est complète (K₂₂), l'arbre est une sélection.

**Lulle combine comme le Sefer Yetzirah.** La troisième figure de l'Ars brevis
range en 36 cases les paires non ordonnées de ses 9 lettres, sans répétition.
C'est la même opération que les 231 portes, sur un alphabet plus petit. Lulle
l'appliquait à des attributs (bonté, grandeur…), pas à des sons.

## Précédents cités par mik, à vérifier

Leibniz a bien relié le Yi Jing à son arithmétique binaire (« Explication de
l'arithmétique binaire », 1703). Ce dossier ne vérifie pas qu'il ait vu dans le
Sefer Yetzirah une préfiguration de l'Ars combinatoria (1666), ni la lecture
d'Abulafia citée pour la polarité face/dos de chaque lettre. Ces deux points
restent `indetermine` tant qu'une source n'est pas citée.
