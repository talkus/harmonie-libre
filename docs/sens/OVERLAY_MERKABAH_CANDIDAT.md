# Deux enrichissements bornés du graphe Merkabah, sans dupliquer les entités

**Statut : PROPOSED_NOT_VALIDATED.** Vise la branche GitHub `merkabah/experimental-v03-two-scenes` (`0.3.0-experimental`, 102 nœuds, 115 relations), et **non** le modèle local 78/152 rapporté mais non accessible.

Le script `merkabah_qualitative_overlay.py` construit **à la lecture** un complément qualitatif par nœud :
1. Force de la preuve : références, statut source, incertitude et particularités de traduction, sans confiance numérique arbitraire.
2. Mouvements autorisés : translation/élévation/arrêt des êtres et des roues associées; propriétés héritées des parties; mouvements non spécifiés laissés indéterminés.

**Aucun nœud ou arc ajouté au graphe source.** La roue dans la roue reste le booléen `wheel_inside_wheel` des quatre roues par scène. Les deux scènes sont strictement distinctes. `Ez 1:18` conserve le conflit de formulation NABRE « eyes » / AELF « scintillements » comme réserve de traduction. `Ez 1:10` et `10:14` restent distincts.

## Exactitude des preuves
Le test CI récupère le graphe existant depuis sa branche et vérifie son blob Git SHA-1 exact : `fb2c508c164e72185368eca012160cf5240630b7`. Si la branche change, il **échoue explicitement** au lieu de fabriquer un état réputé identique.

### Test
```sh
git fetch --depth=1 origin merkabah/experimental-v03-two-scenes
git show FETCH_HEAD:merkabah/schema/merkabah_candidate_v0.3.json > /tmp/merkabah-experimental-v03.json
MERKABAH_EXPERIMENTAL_GRAPH=/tmp/merkabah-experimental-v03.json python -m unittest discover -s docs/sens -p 'test_*.py' -v
python docs/sens/merkabah_qualitative_overlay.py /tmp/merkabah-experimental-v03.json --out /tmp/merkabah-overlay.json
```

**Règle de lecture :** `allowed_in_candidate` signifie « mouvement autorisé par ce contrat de simulation », **pas** « déplacement physiquement ou théologiquement démontré ». `NOT_MODELED` ne signifie pas « interdit par Dieu » ou « interdit par le texte ».

Ce travail **ne change pas** la provenance : utilisateur v0.3 78/152 (129 texte, 18 glose, 5 ressemblance) et 16/16 tests rapportés, GitHub candidat PR #55 61/76, Drive v0.2 rapporté 85/221, GitHub expérimental 102/115. Les quatre versions ne sont pas fusionnées. Aucun test ici ne valide la géométrie, les yeux de la scène 10, la synchronisation de tous les objets 3D ou une animation complète.
