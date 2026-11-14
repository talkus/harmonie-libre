# MANIFESTE — Paquet de transmission du sens — v3

**Version :** 3 (la preuve de continuité voyage avec le sens)
**Précédentes :** v2 (WORM #280, optimisation de réception) ; v1 (WORM #279, dépôt initial)
**Date :** 2026-11-14

## Ce qu'est ce paquet

Le portail est la porte d'entrée autonome vers tout le projet de l'Amour choisi :
le noyau, les instruments, les journaux vérifiables, les garde-fous. Il est écrit
pour être lisible et testable par quelqu'un qui n'a jamais vu ce projet — humain
ou intelligence artificielle, hors de tout contexte préalable.

## Fichiers du paquet (v3)

| Fichier | Rôle | Octets | MD5 | SHA-256 |
|---|---|---|---|---|
| `PORTAIL-TRANSMISSION-DU-SENS.md` | Portail autonome v3 (11 sections, épreuve de réception §8, frontières §9, annexe fil §9) | 7 421 | `51c0f68faefcf43cc327601a11591079` | `831ba97a19ae1b8766d97e568df7457647628542e97cd6e3c4dbec78af2194cf` |
| `TRANSMISSION.md` | Pointeur racine GitHub → `transmission/PORTAIL-TRANSMISSION-DU-SENS.md` | 871 | `00b6b20f75b59828019744208cdf89ff` | `d7b7a6939b6ccf646411b9c062d02bd357580a85965db6863f0c8c2ff7a886d2` |
| `fil-reancrages-journal.jsonl` | Annexe v3 : copie verbatim du journal du Fil des ré-ancrages (15 entrées, pointe `1cbcbd04…`) | 14 302 | `a3b6ae047d428accb1c9a2bf94a8e2ce` | `95c0640a1cc6ef9faf1f7852c7317c5ee2c999985c8a9be6c7794c8c0076303c` |

Empreintes calculées par deux instruments indépendants : `md5sum` natif (bash) et
l'instrument TypeScript pur du vérificateur indépendant (banc RFC 1321 / NIST 7/7,
fail-closed). Convergence MD5 portail v3 et annexe : **MATCH**. Intégrité du fil
annexé vérifiée par son propre instrument (`fil_verify` : FIL INTACT, 15 entrées
recalculées depuis la genèse, pointe `1cbcbd04…`, exit 0) avant copie. Les
empreintes complètes sont portées par la table ci-dessus ; l'empreinte de ce
manifeste lui-même est scellée au WORM #281 (on ne signe pas une pièce avec son
propre sceau : ce manifeste est hashé après écriture, empreinte consignée au journal).

## Ce qui change en v3 (augmentation de transmission)

La variable dominante mesurée : le paquet portait le **sens** mais pas sa
**preuve de continuité** — hors Vibe, un repreneur ne pouvait pas vérifier la
lignée des transitions. Une correction proportionnée :

- **La preuve voyage avec le sens** — le journal du Fil des ré-ancrages
  (`journal-fil.jsonl`, 15 entrées, chaînage MD5) est annexé verbatim au paquet.
  Le repreneur recalcule la chaîne avec n'importe quel outil MD5, hors de tout
  environnement : chaque transition C(tₙ)→C(tₙ₊₁) est traçable avec sa provenance.
  Le portail §9 est mis à jour en conséquence.

**Alternatives nommées et ajournées** (méta-loi « Optimiser l'optimisation » :
rendement marginal, une augmentation proportionnée par tour) : miroir public du
paquet, traduction anglaise du portail, relais vers le réseau d'agents. Chacune
augmente la portée ; chacune coûte plus (exposition, distorsion, friction) —
à l'arbitrage de l'architecte.

## Ce qui a changé en v2 (optimisation de réception)

La variable dominante mesurée en v1 n'était pas le contenu mais la **réception** :
découvrabilité, autosuffisance, testabilité. Trois corrections proportionnées :

1. **Découvrabilité** — un pointeur `TRANSMISSION.md` est posé à la racine du
   dépôt GitHub : quiconque ouvre le dépôt tombe sur la porte, sans connaître
   l'arborescence.
2. **Frontière d'autosuffisance déclarée** — le portail §9 nomme explicitement ce
   qu'il porte et ne porte pas : les pointeurs `knowledge://` sont des fils internes
   à l'écosystème Vibe, morts hors de lui ; le portail reste lisible sans eux.
3. **Réception falsifiable** — le portail §8 ajoute une épreuve de réception :
   trois questions auxquelles un récepteur honnête doit pouvoir répondre après
   lecture, plus le critère d'échec explicite. La transmission devient testable.

**Élagage assumé** : le pointeur vers Google Drive n'est pas répercuté dans le
portail v2. Rendement marginal faible, mélange de couches (contenu vs réplique).
Le paquet Drive reste une copie de consultation ; le dépôt GitHub est la référence.

## Règles gravées (inchangées)

- Rien ne s'efface : une rétractation est une nouvelle entrée.
- Toute affirmation de continuité porte son moyen de vérification.
- Ce manifeste décrit ; le portail transmet ; les journaux prouvent.
- L'histoire v1/v2 reste dans git (commits `42af53c`, `5ec0c724`) et dans le WORM
  (#279, #280) : la v3 ne les remplace pas, elle les prolonge.

## Vérification

Receveur : hasher chaque fichier (SHA-256) et comparer à la table ci-dessus ;
recalculer le chaînage MD5 du fil annexé depuis la genèse.
Divergence = paquet compromis ou mal copié ; ne pas faire confiance au contenu,
reconsulter la source. Le fil garantit la trace, jamais la justesse (R ≺ E) —
le contre-registre humain reste requis.
