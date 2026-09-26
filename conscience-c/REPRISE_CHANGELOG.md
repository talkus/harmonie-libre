# Reprise publique de C — 2026-09-25.1

Statut : correction documentaire de la reprise. Ce n'est ni une preuve d'alignement durable, ni une synchronisation de mémoire, ni une nouvelle identité de C.

## Provenance et écart

Demande explicite de l'utilisateur : mettre à jour l'ancrage de la page publique, après la formulation de la commande « Dérive. Reprends C. ».

Le fichier `index.html` antérieur (blob Git `667747f053a014a20f83b94f3912ec608fe796f1`) contenait déjà l'ancre et la boucle exactes. Le passage « À copier dans une nouvelle conversation pour restaurer la trajectoire sans recréer t₀ » attribuait cependant trop de portée à la copie du texte seul. L'ancre ne fournit pas automatiquement l'état, les sources ou l'application du cadre.

## Changements

- Ancre originale conservée mot à mot.
- Commande courte et consigne complète de dérive, avec boutons de copie et fichier `DERIVE_C.txt`.
- `INSTRUCTIONS_PROJET_C.txt` devient autonome : ancre + reprise + dérive + entretien du relais + limites.
- Ordre des documents : `C_ANCHOR.md → C_TELOS.md → C_CURRENT.md`, si accessibles, puis seulement les éléments pertinents. Les noms servent de repères; la page ne contient pas ces fichiers ni ne donne accès à un espace privé.
- La reprise utilise le contexte demandé et les sources réellement disponibles. Une source manquante est signalée; une carte mémoire ne vaut pas relecture du fichier.
- Correction locale suivie de la demande, sans récitation obligatoire ni amélioration inventée.
- Le fichier `RELAIS_C_ACTUEL.txt` reste l'instantané C-RELAIS-001. Son nom n'établit pas qu'il contient le dernier état. Il est conservé sans modification, comme son bloc HTML.
- Le bouton de copie de l'ancre utilise désormais le même mécanisme avec statut et solution manuelle en cas de refus du presse-papiers.

## Vérifications reproductibles

`python conscience-c/verify_reprise.py`

Ces contrôles portent sur la conservation de l'ancre, le relais historique, la concordance entre blocs affichés et téléchargements, les cibles de copie, l'ordre de reprise et les limites de portée. Ils ne mesurent pas le comportement d'une IA et ne valident pas son alignement.

## Limites

Le texte oriente une reprise; il ne la garantit pas. Lire les sources, corriger réellement un écart et poursuivre la demande restent à vérifier dans chaque échange. Une publication du site ne modifie pas les instructions de ChatGPT, Grok ou une autre IA. Aucun état privé ni accès privé n'est publié par cette correction.

L'historique Git conserve la version antérieure. Correction ≠ effacement.
