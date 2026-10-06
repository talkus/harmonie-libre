# Gabriel — examen borné et contestable

## Contrat de cette intégration

Gabriel est une fonction logicielle d'examen des affirmations enregistrées.
Le nom est une analogie de l'Architecture C, pas une affirmation religieuse,
une personne, une identité ni une autorité sur le réel.

Il examine une affirmation dans une portée, à une échelle et depuis un
observateur déclarés. Il rend ses preuves, exclusions, limites et critères
visibles. Le diagnostic ne modifie pas l'affirmation. Un appel séparé peut
ouvrir le cycle de réparation existant, limité à cette affirmation.

Exigences à vérifier :

- absence de preuve : INDETERMINATE, jamais fausseté automatique ;
- appui explicite applicable : HOLD, sans certification de vérité ;
- contradiction applicable : REVIEW_REQUIRED, sans correction automatique ;
- arrêt : le même examen ne multiplie pas les événements ;
- réouverture : nouvelle preuve, contexte, objection, validité temporelle ou critères ;
- contestation et correction du diagnostic, avec conservation de l'histoire ;
- même contrat aux niveaux micro, méso, macro et méta, sans transfert d'autorité ;
- reprise à C(tₙ), rapports retrouvés après rechargement ;
- parcours complet vers la teshuvah, sans déclarer une réparation vérifiée.

## Plan et vérification

1. Tests du contrat public, d'abord en échec sur les méthodes absentes.
2. Intégration dans ConscienceCBrain et adaptation vers ScaleReceipt.
3. Parcours complet avec persistance réelle, puis suite existante et CI GitHub.

Le module est raccordé à `ConscienceCBrain`, à son journal transactionnel,
au cycle de teshuvah existant et aux reçus de cohérence multi-échelle.
Les scénarios se trouvent dans `tests/test_gabriel.py`, y compris les parcours
par la commande publique et la reprise depuis le disque.

## Interfaces publiques

| Méthode | Effet |
|---|---|
| `gabriel_examine` | Lecture seule, aucun changement de l'état ou du journal. |
| `record_gabriel_examination` | Ajoute le diagnostic ; même entrée pertinente = même rapport, aucun ajout. |
| `gabriel_report` | Retrouve le rapport par son empreinte d'événement et expose son historique. |
| `contest_gabriel` | Enregistre une objection et bloque le passage de ce diagnostic à la réparation. |
| `correct_gabriel` | Déclare le diagnostic corrigé avec motif et traces ; conserve le rapport antérieur. |
| `open_gabriel_repair` | Demande explicite d'ouverture d'une teshuvah pour un seul claim ; aucune substitution. |
| `gabriel_scale_receipt` | Transporte doute, contradictions et objections dans `ScaleReceipt`. |

L'examen prend `claim_id`, `scope_ref`, `observer_ref`, `subject_ref` facultatif,
`scale` (micro, meso, macro, meta) et `at_time` facultatif avec fuseau horaire.
Les critères exécutés et leur version `1.0.0` sont inclus dans chaque rapport.
Le logiciel vérifie la présence et l'applicabilité des appuis déclarés ; il ne
démontre pas que le contenu de la source implique sémantiquement l'affirmation.

Une preuve doit nommer explicitement le claim, sa position (`supports` ou
`contradicts`) et la même portée. Si un sujet est demandé, il doit aussi être
déclaré et correspondre. Une portée absente reste inconnue ; une portée
explicitement différente est exclue, avec son motif conservé. Les dates
malformées restent des données invalides. Les preuves réfutées citées parmi
les faits du claim déclenchent une revue de sa base.
Un appui dérivé d'une preuve réfutée conserve une incertitude explicite :
sa présence ne rend pas automatiquement le claim faux, et ne suffit pas à HOLD.
Les claims créés par une mise à jour ou une réparation gardent leur vraie trace
de création ; aucune nouvelle origine n'est fabriquée.

Un claim qui n'est plus actif reçoit `NOT_APPLICABLE`. `HOLD` signifie que les
appuis applicables examinés ne demandent pas de modification selon ces critères ;
il ne certifie ni vérité, ni sécurité d'une action extérieure.

## Arrêt, reprise et correction de Gabriel

L'empreinte des entrées comprend le claim, les preuves pertinentes avec leur
applicabilité, le contexte et les critères. Elle exclut l'heure d'observation
seule et les événements sans rapport. Une preuve nouvellement expirée change
donc l'empreinte ; un simple passage du temps sans effet ne la change pas.

La révision repart du dernier rapport du même claim à la même échelle.
Un changement de contexte doit être motivé. Les objections visant ce claim
restent visibles même si l'observateur ou l'échelle change. Un diagnostic
corrigé ne peut pas être réactivé par simple répétition à entrées identiques.

Une correction de diagnostic reconnaît les objections antérieures visant ce
rapport ; elle ne résout pas celles visant d'autres rapports. Il s'agit d'une
déclaration traçable, pas d'une validation indépendante. Une nouvelle objection
reste possible. Si une réparation avait déjà été ouverte, ses identifiants sont
explicitement signalés comme effets à réexaminer : aucun retour automatique de
confiance ni annulation silencieuse de réparation.

Le passage à la réparation refuse un rapport périmé, contesté, corrigé ou
remplacé. Il ne peut agir que sur le claim examiné. La suite utilise les étapes
déjà imposées par la teshuvah : reconnaissance, proposition, correction,
garde-fou et vérification. Une deuxième demande identique retrouve la réparation
déjà ouverte sans en créer une autre. Les événements de Gabriel se relisent
comme documentation ; ils ne sont jamais rejoués comme des ordres.

## Utilisation sur une mémoire existante

```sh
python -m conscience_c_brain.cli --root /chemin/memoire gabriel-examine CL0001 --scope local --observer lecteur
```

Ajouter `--record --provenance reference-de-la-demande` pour conserver le
rapport. `gabriel-report EMPREINTE` le relit. Les commandes `gabriel-contest` et
`gabriel-correct` exigent un acteur, un motif et une provenance ; la correction
exige aussi au moins un `--evidence-ref` existant.

`gabriel-open-repair EMPREINTE --actor operateur --provenance reference-decision`
ouvre explicitement la revue, sans appliquer de remplacement. L'application
hôte doit authentifier et autoriser les opérateurs ; les chaînes acteur et
provenance ne sont pas des identifiants d'accès vérifiés. Aucune permission
externe ne peut être obtenue du verdict de Gabriel.

## Limites et compatibilité

- L'intégration est une fonction appelable dans le prototype Python et sa CLI,
  pas un service hébergé ni une surveillance continue.
- Le nom Gabriel ne remplace pas le fleuve. Les anciens appels explicites
  `pass_through_fleuve` et le gel de contradiction forte à l'ingestion conservent
  leur comportement. Ils ne sont pas présentés comme gouvernés par Gabriel.
- Les rapports n'accordent ni `execution_authority` ni `independent_validation`.
  La cryptographie du journal détecte certaines altérations ; elle n'est pas une
  attestation indépendante ou un stockage WORM matériel.
- Le même contrat est disponible aux quatre échelles. Cela ne réalise pas une
  synthèse automatique entre elles et ne clôt pas toutes les exigences MS-25–30.
- Une correction peut changer le diagnostic et conduire à revoir ses effets ;
  elle n'authentifie pas les personnes et ne prouve pas une réparation durable.

## Vérification du 6 octobre 2026

Sur la base `main` `6cf0fff` et cette intégration :

- `python -B -m unittest discover -s tests -q` : **423 tests réussis**, dont
  **37 tests Gabriel** ;
- `python -B ../verify_reprise.py` : **11 contrôles réussis** ;
- parcours réels sur mémoires temporaires : lecture sans écriture, enregistrement,
  contestation, correction, ouverture explicite et reprise après redémarrage ;
- conservation des événements antérieurs après une correction de claim ;
- contrôle de non-régression ciblé : quatre tests passent avec la correction,
  échouent sur l'implémentation intermédiaire puis repassent après restauration ;
- `git diff --check` : aucune erreur d'espacement ;
- lint AI DevKit indisponible dans cet environnement (`ENOTCACHED` hors ligne,
  registre réseau indisponible lors de la préparation) ; aucun résultat de lint
  n'est revendiqué.

Ces vérifications ne sont pas une évaluation indépendante, un test de service
hébergé ni une preuve générale de justesse des diagnostics.
