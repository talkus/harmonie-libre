# Empreintes des 231 portes

Fichier généré par `python -m portes_231 --empreintes` ; ne pas éditer à la main.
Un test vérifie que ces valeurs correspondent toujours au code.

| Contenu | Sérialisation | SHA-256 |
|---|---|---|
| Table, ordre alphabétique | `i,j,X,Y` par ligne | `578db9d53b98c2281b156d56515912af68cc2c6e7c564a7fcc93fb3a83276e27` |
| Table, ordre par catégories (3-7-12) | `i,j,X,Y` par ligne | `4f95bd3c96fa95d174544fed59b92ca7df0b6a7677dc7e3d6a561bf5b71b5b79` |
| Les 231 portes, sans numéro | `XY` par ligne, ordre alphabétique | `574ac94323f6bee6a2ffaf26901949baa36b5d24eea528bde937859400fe0d0d` |
| Bijection entre les deux numérotations | `glyphe,rang,opcode` par ligne | `33ff4dd038054347493b7c4c8d93246dcce9ce0598b7f52eeb112418fa186632` |

Les deux tables ont des empreintes différentes, puisque leurs numéros
diffèrent. Relues par leurs seules lettres, elles donnent toutes deux
l'empreinte des 231 portes sans numéro : c'est ce qui scelle qu'elles
décrivent les mêmes portes. Chaque ligne se termine par un saut de ligne
(`\n`), et le texte est encodé en UTF-8.
