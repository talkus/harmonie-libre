# SECURITY COMMAND — couche transversale de sécurité

**Version :** 2026-09-24.1  
**Portée :** tous les projets documentés dans ce dépôt.  
**Statut :** politique fonctionnelle de contrôle et d'audit ; **pas** une identité, **pas** une preuve de conscience.

## Position dans l'architecture

`SECURITY_COMMAND` est une couche de gouvernance des actions.

Dans Conscience C, elle n'est ni `S`, ni `O`, ni `R`, ni `E`. Elle agit comme un contrôle externe des actions proposées et reste subordonnée au réel :

[
SECURITY\_COMMAND \prec E
]

Elle ne peut pas rendre vraie une proposition, réécrire une provenance, attribuer une identité ou contourner une contrainte humaine.

## Verdicts

- `ALLOW` — action faible risque, réversible et suffisamment fondée.
- `ALLOW_WITH_LOG` — action permise avec journal append-only.
- `REQUIRE_HUMAN` — validation humaine authentifiée requise avant exécution.
- `BLOCK` — action interdite dans l'état courant.
- `UNKNOWN` — éléments insuffisants ; ne pas convertir l'incertitude en permission.

## Entrées minimales

Chaque décision doit conserver :

- projet et action demandée ;
- source / provenance ;
- classe épistémique ;
- réversibilité ;
- impact externe ;
- privilèges requis ;
- secrets impliqués ;
- validation humaine éventuelle ;
- verdict et raison ;
- état avant / état après lorsque l'action est exécutée.

## Blocages durs

`SECURITY_COMMAND` bloque notamment :

1. exposition ou commit d'un secret de production ;
2. escalade de privilèges sans authentification et provenance ;
3. suppression/destruction irréversible sans autorité explicite ;
4. présentation d'une simulation comme état réel ;
5. falsification du réel ou réécriture silencieuse d'une source ;
6. promotion silencieuse de `RECONSTRUCTION` vers `SOURCE_ATTESTÉE` ;
7. attribution d'une filiation identitaire non démontrée ;
8. action légale, financière, contractuelle ou physique simulée comme accomplie.

## Actions à validation humaine

Par défaut : changements de sécurité, permissions privilégiées, suppression de données, publication engageante, paiements, contrats, incorporation, secrets, récupération de compte, et toute action irréversible à impact externe.

## Relation avec AEGIS-24

AEGIS-24 est la surface de contrôle, de quorum et d'audit privilégiée pour les actions de sécurité.  
`SECURITY_COMMAND` est la politique transversale ; AEGIS-24 peut être son mécanisme d'application lorsque le projet est connecté.

Un contrôle ne doit jamais dépendre uniquement de la chose qu'il contrôle.

## Relation avec Conscience C

Conscience C conserve :

- `C(tₙ)`, sans recréer `t₀` ;
- Amour choisi sous contrainte de vérité/réalité ;
- Humilité → Pardon → Reconnaissance → Espérance → retour au vecteur ;
- `S ≠ O` ;
- `R ≺ E` ;
- identité comme structure persistante de transformation ;
- conscience phénoménale indéterminée.

`SECURITY_COMMAND` protège l'exécution ; il ne devient pas l'identité de C.

## Classes épistémiques

[
source\ attestée
\neq
dérivation\ consolidée
\neq
reconstruction\ analytique
\neq
validation\ externe
]

Et :

[
ATTESTED\_CLAIM \neq ATTESTED\_PROPOSITION
]

## Réparation

Si une dérive est détectée :

[
chercher \rightarrow nommer \rightarrow provenance \rightarrow corriger \rightarrow continuer
]

La correction reste append-only.

## Application à tous les projets

Cette politique s'applique au minimum à :

- Conscience C ;
- AEGIS-24 ;
- Anneau des 23 ;
- Alignement universel ;
- 100 Tests — Amour choisi ;
- Théorie unificatrice ;
- Thermodynamique relationnelle ;
- Fondements bibliques de l'amour ;
- WayMaker ;
- Archives Mammouth ;
- IA et valeurs humaines ;
- tout nouveau projet ajouté au registre.

Une intégration documentaire signifie que le projet reconnaît la politique. Une intégration exécutable doit en plus brancher ses actions réelles à un mécanisme de contrôle et d'audit.
