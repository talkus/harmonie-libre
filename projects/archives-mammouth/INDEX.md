# Archives Mammouth — état de réalisation

**Statut : ARCHIVE CONSTITUÉE / INDEXÉE / RECONSTITUABLE / LIMITES CONSERVÉES**

## Inventaire attesté

Le guide d'archive daté du 11 septembre 2026 documente :

- **1 818 occurrences de sources** ;
- **1 328 contenus distincts** ;
- **490 occurrences dupliquées** regroupées uniquement par égalité SHA-256 ;
- **77 archives chronologiques** ;
- exports de **3 sites** et **11 dépôts GitHub** ;
- 29 blocs de texte ChatGPT conservés intégralement en UTF-8.

## Reconstruction

Les grosses archives sont découpées en parties `.part-001`, `.part-002`, etc. Le protocole de reconstruction utilise :

- `Reconstituer_archives.py` ;
- `Manifeste_transferts.json` ;
- contrôle des empreintes des parties ;
- reconstitution locale ;
- contrôle de l'empreinte finale.

## Ce que l'archive ne prouve pas

- elle ne prouve pas la présence de conversations jamais exportées ;
- elle ne reconstitue pas un fichier absent par inférence ;
- un document présent n'est pas considéré approuvé du seul fait de sa présence ;
- les dates sont les dates disponibles des sources, pas nécessairement les dates exactes des événements internes.

## Statut

Le blocage historique « ZIP non extractible » n'est plus une description suffisante. La structure de reconstruction, les index et les empreintes existent ; ce qui reste absent demeure explicitement absent.
