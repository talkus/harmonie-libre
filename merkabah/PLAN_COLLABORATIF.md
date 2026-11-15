# MERKABAH — Reconstruction multidimensionnelle collaborative (proposition v0.1)
Date : 2026-11-15. Statut : PROPOSITION, NON VALIDÉE. Aucun déploiement.

## But
Reconstruire la vision d'Ézéchiel (chapitres 1 et 10) en modèle de nœuds interreliés, contrôlable sous plusieurs perspectives et animable, sans confondre texte biblique, inférence géométrique et interprétation Architecture C / Amour choisi.

## Principe d'architecture
Centre simple : graphe versionné de nœuds, relations, contraintes, sources et statuts. Périphérie : Blender (géométrie), NetworkX (contrôles), Godot (simulation), Gephi (analyse), Neo4j (optionnel), GitHub (revue). Aucun rendu ne constitue une preuve de fidélité.

## Modèle minimal
Nœuds : vision, Kebar, contexte de l'exil, vent du nord, nuage, feu, éclairs, 4 chérubins C1..C4, 16 faces (4 par être : homme/lion/bœuf/aigle selon Ez 1:10), 16 ailes (4 par être), mains sous les ailes, jambes droites et pieds de veau, 4 roues W1..W4, structures roue-dans-roue, jantes et yeux, ruach, étendue cristalline, trône de saphir, figure lumineuse, arc-en-ciel. Ez 10 ajoute yeux sur corps et ailes, charbons et transfert de gloire ; distinguer les scènes.
Relations typées : beside(Ci,Wi), has_face(Ci,Fij), has_wing(Ci,Aij), moves_with(Wi,Ci), driven_by(Ci,ruach), beneath(Ci,expanse), above(throne,expanse), cited_by(node,verse), derived_from(claim,archive), contradicts(claim,claim).
Chaque assertion : id, source, chapitre/verset ou archive exacte, statut TEXTUEL / DÉDUIT / INTERPRÉTATION / INCONNU, hypothèses, incertitude, auteur, version, preuve et falsificateur.

## Dimensions
3 coordonnées spatiales + temps ; orientation, coordination, perception et hiérarchie sont des dimensions descriptives, non des dimensions physiques démontrées. Quatre faces visibles depuis des orientations différentes sans faire tourner le chérubin. Les roues peuvent changer d'orientation interne sans que la translation du groupe exige un demi-tour.

## Critères de contrôle
1. Exactement 4 chérubins, 4 faces et 4 ailes par chérubin, 1 roue associée à chaque chérubin.
2. Les roues ont une géométrie imbriquée et des jantes couvertes d'yeux ; aucun gyroscope central inventé.
3. Vérification des mains, pieds, ailes jointes et ailes couvrantes.
4. Mouvement des roues et porteurs synchronisé selon le texte ; ruach non auto-produit dans notre interprétation.
5. Scènes Ez 1 et Ez 10 séparées, éléments non attestés marqués hypothétiques.
6. Vérifier chaque être individuellement de face, de dos, de côté et en perspective, avant l'assemblage puis avant animation.
7. Chaque échec crée un ticket ; ne jamais déclarer « fidèle » sans reçu de vérification.

## Collaboration
GitHub : issues par composant, branches dédiées, pull requests avec revue, dossier /merkabah, tests automatisés, fichier de provenance. Drive : dossier de référence, sources, décisions et comptes rendus ; les deux espaces se référencent mutuellement. Contributeurs sans droit de modifier le canon d'origine. Validation humaine explicite avant changement de statut.

## Jalons
M0 : inventaire sourcé et conflits ; M1 : schéma JSON du graphe ; M2 : tests NetworkX ; M3 : prototypes 3D individuels Blender ; M4 : scène assemblée ; M5 : animation Godot ; M6 : revue biblique et archivistique contradictoire.

## Sources initiales
Ézéchiel 1:1–28 ; 10:1–22.
Drive : https://drive.google.com/file/d/1Lr1JVChOiuwDLXJpQnZCtZymaP7JBL7g/view ; https://docs.google.com/document/d/186jcOZB8saswpuFvAzyNMryueYj_2HmMAtx-sjUzjYE/edit
Noyau merkabah_core.py mentionné dans la passation, octets originaux non revérifiés : CANON_NOT_VERIFIED.

## Sécurité et gouvernance
Proposition non souveraine. R ≺ E ; RETROUVÉ ≠ RECONSTRUIT ; document ≠ exécution ; aucune fusion silencieuse des interprétations au texte.