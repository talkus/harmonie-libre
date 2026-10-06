# Empreintes des 231 portes

Fichier généré par `python -m portes_231 --empreintes` ; ne pas éditer à la main.
Un test vérifie que ces valeurs correspondent toujours au code.

| Sorte | Contenu | Dépend de l'ordre ? | Sérialisation | SHA-256 |
|---|---|:---:|---|---|
| structurelle | Les 231 portes, sans numéro | non | `XY` par ligne, ordre alphabétique | `sha256:virgule:574ac94323f6bee6a2ffaf26901949baa36b5d24eea528bde937859400fe0d0d` |
| sérialisation | Table, ordre alphabétique | oui | `i,j,X,Y` par ligne | `sha256:virgule:578db9d53b98c2281b156d56515912af68cc2c6e7c564a7fcc93fb3a83276e27` |
| sérialisation | Table, ordre par catégories (3-7-12) | oui | `i,j,X,Y` par ligne | `sha256:virgule:4f95bd3c96fa95d174544fed59b92ca7df0b6a7677dc7e3d6a561bf5b71b5b79` |
| sérialisation | Bijection entre les deux numérotations | — | `glyphe,rang,opcode` par ligne | `sha256:virgule:33ff4dd038054347493b7c4c8d93246dcce9ce0598b7f52eeb112418fa186632` |

Il n'existe qu'une empreinte structurelle. Les deux tables, relues par
leurs seules lettres, la redonnent toutes deux : c'est ce qui scelle
qu'elles décrivent les mêmes portes. Les empreintes de sérialisation, une
par ordre, figent cet ordre pour un outil qui lit les portes en séquence.

Convention `virgule`, inscrite dans chaque empreinte : champs séparés par `,` ; chaque ligne terminée par `\n`, y
compris la dernière ; UTF-8 sans BOM ; pas d'en-tête. Dans une ligne de
table, l'extrémité de plus petit rang dans l'ordre choisi vient d'abord.
