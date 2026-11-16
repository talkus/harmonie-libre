# Merkabah — contrat cinématique v0.1 (CANDIDAT)

**Statut : PROPOSITION NON VALIDÉE.** Ce contrat formalise des contraintes de reconstruction, pas la physique d'une vision.

## Coordonnées et identités

- Monde 3D : axe vertical Z, plan horizontal XY ; unités arbitraires. Les orientations choisies sont de la scénographie (DÉDUIT) et non des mesures bibliques.
- Chaque chérubin possède une transformation rigide propre C_i(t), une roue propre W_i(t), i=1..4. Les identifiants sont immuables, même si la caméra change.
- Une face est attachée à son chérubin, jamais à un autre. Quatre faces distinctes par chérubin sont visibles en rotation de caméra. Les ailes et les roues ne fusionnent pas en un objet commun.
- Le ruach est un signal de commande logique, pas une représentation géométrique obligatoire.

## Règles vérifiables proposées

1. **Absence de retournement lors des déplacements** : pour un déplacement pur entre t et t+Δ, l'orientation du chérubin reste identique, même quand la direction de translation change. Le mouvement se fait selon une direction déjà accessible à une de ses faces (interprétation de Éz 1:9,12,17 ; distinguer orientation du corps et direction du trajet).
2. **Roue adjacente** : W_i(t) = C_i(t) · O_i · R_i(t), où O_i est le décalage local fixe entre chérubin et roue, et R_i la rotation interne facultative de la roue. Pour toute translation commune, la distance entre les centres reste constante. Attention : une rotation interne de roue ne doit pas être confondue avec un retournement du chérubin.
3. **Synchronisation** : quand le chérubin se déplace, sa roue suit la même translation et le même changement de hauteur (Éz 1:19-21). Dans une animation, le retard de synchronisation admissible est fixé à zéro image au moment de l'échantillonnage.
4. **Conservation** : le nombre d'êtres, faces, ailes, roues et connexions structurales demeure constant à chaque image, sauf changement explicite de scène. Une pièce masquée par la perspective n'est pas déclarée absente ; une pièce supprimée doit faire échouer un contrôle.
5. **Scènes distinctes** : les états Ézéchiel 1 et Ézéchiel 10 gardent des annotations textuelles séparées ; le cas Éz 10:14 reste UNCERTAIN et ne modifie pas silencieusement les faces d'Éz 1:10.
6. **Détection négative** : tests de contre-exemples : roue disparue, 3 ailes, roue centrale unique, rotation du chérubin de 90° pendant un trajet, translation roue/être désynchronisée, divergence des faces occultée. Chacun doit produire FAIL.

## Limites

Le modèle 3D n'infère pas une orientation absolue, un diamètre de roue, des articulations ou un mécanisme physique sur la seule base du texte. Les vues et matériaux sont des interprétations déclarées. Le critère d'acceptation nécessite un export démonstratif, les mesures des trajectoires et une contre-validation exégétique indépendante.
