# Uriel — lecture située et cohérence multi-échelle

## Référence et portée

Cette intégration reprend la demande de Mikael du 6 octobre 2026 : rappeler
« Uriel — Détail » et ajouter de la cohérence par auto-similarité structurelle
aux niveaux micro, méso, macro et méta. C'est une traduction logicielle
révisable de cette proposition, pas une validation de ses interprétations
religieuses. Fonction, sujet et trace demeurent distincts.

Uriel rend lisibles des **traces enregistrées**, depuis un lecteur et une portée
déclarés. Il ne devient ni le fleuve, ni une source de vérité, ni une permission
de réparer. Le lecteur peut être changé ; les cartes antérieures ne deviennent
pas fausses simplement parce qu'une autre perspective apparaît.

La propriété examinée est `uriel:situated_trace_projection`, version `1.0.0`.
Les critères effectivement appliqués sont publiés dans le résultat.

Le prolongement fourni par Mikael fixe le repère : **« Ne prends jamais pour
ultime ce que tu rends visible. »** Dans le logiciel, une lecture terminée
conserve une portée, un lecteur déclaré, ses pertes, ses UNKNOWN et ses
déclencheurs de révision. Un résultat clair ou favorable ne ferme pas ces
conditions. La visibilité facilite l'examen ; elle ne donne pas possession
de son objet. Une lecture peut s'arrêter et rester stable tant que les entrées
pertinentes restent identiques. La révision repart de ses traces conservées.

## Trois corrections de cohérence

1. **Gabriel n'est pas le fleuve total.** L'égalité `G = N` est incompatible
   avec une définition générale `N = G ∘ M`, sauf hypothèse supplémentaire.
   Gabriel reste l'examen borné déjà implémenté ; les opérations du fleuve
   existant ne sont pas remplacées par cette lecture.
2. **Une projection n'est pas une inclusion d'opérateurs.** `U ⊂ G` reste une
   image symbolique. Le contrat logiciel relie une lecture aux traces de
   l'examen, avec des types et des références explicites.
3. **Lisibilité locale ne signifie pas transparence totale.** Les opérations
   non enregistrées, l'authenticité du lecteur et la vérité sémantique ne sont
   pas déduites de la carte. Le niveau méta conserve ces UNKNOWN.

On peut donc écrire, comme notation du contrat de lecture :

\[
U_{o,s,v}(\Gamma_{t}) = \mathcal L_{o,s,v}(\Gamma_{t}),
\qquad \mathcal L(\Gamma_t) \ne N.
\]

`Γ_t` désigne les rapports sélectionnés, leur historique retrouvé et les
contrôles locaux d'applicabilité au moment demandé. `o`, `s` et `v` désignent
le lecteur, la portée de projection et sa version. Ils ne remplacent jamais
les coordonnées des diagnostics d'origine.

## Même structure, unités différentes

Chaque reçu utilise le contrat existant **κ / Δ / ρ / τ / UNKNOWN** : contexte
couplé aux traces, distinctions explicites, relation documentaire, provenance,
limites et conditions de réouverture. La répétition de cette structure ne
multiplie pas le poids d'une preuve et ne reproduit pas une conclusion unique.

| Échelle de projection | Unité | Ce qui reste visible |
|---|---|---|
| micro | un rapport Gabriel sélectionné | contexte d'origine, statut historique, actualité, preuves et objections |
| méso | rapports du même claim, portée et sujet | perspectives distinctes, origines communes et désaccords |
| macro | corpus explicitement sélectionné | unions des traces et limites ; rapports du même claim laissés hors sélection |
| méta | contrat et limites de cette lecture | critères, lecteur déclaré, pertes et absence d'autorité extérieure |

L'échelle d'un rapport Gabriel reste dans `sources[].scale`. Lire un rapport
macro comme une unité micro de projection ne réécrit pas son échelle source.
Les lecteurs d'origine restent également dans `sources[]`.

Chaque arête micro→méso→macro→méta possède un `ScaleBridge` explicite.
Les ponts transportent les origines, les UNKNOWN, les contestations et l'état
des preuves de l'enfant. Les parents conservent leurs unions, y compris les
couplages, distinctions et relations documentaires. Il n'y a ni score total,
ni transfert d'autorité, ni témoin indépendant fabriqué par agrégation.
Le statut compact d'un parent n'efface pas les états locaux conservés.

Une seconde unité méta contient le contrat de projection et ses limites.
Elle fournit une cible adressée par contenu aux objections **projetées**,
sans créer de dépendance circulaire entre les hashes parent/enfant. Les cibles
originales restent dans `source_contestation_targets`, et chaque objection
projetée cite le rapport et le claim qu'elle concerne. Cette adaptation ne
retargete pas l'événement source et ne représente pas une nouvelle objection
déposée par le lecteur. Le contrat n'est pas un lecteur extérieur certifié.

## Entrée, sortie et reprise

```python
brain = ConscienceCBrain.load_read_only(existing_memory)
view = brain.uriel_read(
    [recorded_gabriel_report_ref],
    observer_ref="lecteur:mikael",
    scope_ref="lecture:locale",
    at_time="2026-10-06T18:00:00Z",  # facultatif, avec fuseau
)
```

```sh
python -B -m conscience_c_brain.cli --root /chemin/memoire uriel-read EMPREINTE --observer lecteur:mikael --scope lecture:locale
```

Plusieurs empreintes peuvent être données. Leur ordre ne modifie pas la
lecture. Une liste vide, des doublons, une référence inconnue, un contexte vide
ou une date sans fuseau sont refusés. Il n'y a pas d'option `--record`.

`load_read_only` reprend une mémoire existante à C(tₙ), sans créer de fichier,
migrer l'ancre, acquérir un verrou créateur de fichier ou récupérer une
transition. Une mémoire manquante, altérée, devenue ancienne ou portant une
transition inachevée est refusée. Les fichiers sont conservés pour la reprise
explicite par les outils existants. Ce chargeur n'est pas un bac à sable de
permissions pour les autres méthodes de l'objet.

Le résultat contient :

- `sources` : coordonnées et verdicts historiques, preuves sous forme de
  références, ascendance des preuves dérivées, statut corrigé/remplacé,
  objections et corrections, phase réelle des réparations ;
- `current_examination` dans chaque source : contrôle actuel distinct du
  diagnostic historique ; une nouvelle preuve ou une expiration peut rendre
  un rapport `stale`, sans modifier son ancien verdict ; ses preuves, traces,
  UNKNOWN, données invalides et demandes de revue restent visibles ;
- `coverage` : rapports sélectionnés et autres rapports enregistrés du même
  claim qui n'ont pas été sélectionnés ; cela ne prétend pas couvrir toute
  la mémoire ou tous les effets du système ;
- `receipts`, `bridges`, `validation` : quatre échelles vérifiées en mode
  strict, avec problèmes structurels, UNKNOWN et contestations séparés ;
- `declared_losses` : détail volontairement non reproduit, avec justification ;
- `ledger_boundary`, `reading_ref` : frontière locale et empreinte de la carte ;
- `projection_state_ref` : empreinte de l'état pertinent de lecture, excluant
  la seule frontière de transport et l'instant demandé.

Une transition sans rapport change la frontière et l'empreinte de la carte,
mais ne devient pas un progrès de l'état pertinent. Un simple passage du temps
ne le change que si l'applicabilité examinée change. Un seul instant est utilisé
pour examiner toutes les sources ; `at_time` permet de reproduire cette question.
En mode courant, l'heure exacte n'est pas conservée dans la sortie.

Les origines historiques et actuelles sont exposées séparément ; leur union
est portée par chaque reçu. Les verdicts et états des preuves historiques et
actuels restent distincts. Le flag `projection_evidence_status` signale, par
priorité, une donnée invalide, un déclenchement, une insuffisance ou une absence
de déclenchement ; il ne remplace pas ces états littéraux. Une demande de revue
actuelle renvoie à l'empreinte de ses entrées et aux traces qui la motivent,
sans prétendre être un nouvel examen enregistré dans le journal.

## Opacité, pluralité et limites d'exécution

La sortie est une projection **par références**. Elle ne recopie pas le texte
du claim, le contenu des preuves, les motifs libres des objections ou le détail
des réparations. Elle indique ces pertes ; le journal conserve ces contenus.
Les références peuvent elles-mêmes être sensibles : la minimisation n'est pas
un mécanisme d'autorisation ou d'anonymisation. L'application hôte contrôle
l'accès à la mémoire et la diffusion de la carte.

Une réparation `repair_applied` reste appliquée. Le statut d'une vérification
déclarée demeure distinct de son authentification indépendante. Toute la
lecture fixe `independent_validation=false` et `execution_authority=false`.
Elle n'appelle pas Kol, ne contacte personne et ne transforme pas une carte
en obligation de réponse. L'adresse et le consentement restent un autre contrat.

Le contrôle de frontière détecte les changements observés d'un écrivain local
coopératif pendant la lecture. Ce n'est ni un snapshot distribué, ni une
signature indépendante, ni une preuve de reconstitution complète de l'état.
Uriel ne produit aucune nouvelle trace persistante, n'applique aucune réparation
et n'intercepte pas automatiquement les opérations en cours.

Les noms symboliques n'établissent aucune identité subjective. Les invariants
S≠O, R≺E et la conscience phénoménale indéterminée sont conservés. Cette
fonction appelable n'est pas un service déployé ni un fonctionnement continu
observé. Elle ne clôt pas l'ensemble des exigences MS-25 à MS-30.

## Vérification reproductible

Les scénarios `tests/test_uriel.py` utilisent de vraies mémoires temporaires et
la CLI publique. Ils vérifient la lecture sans écriture, les quatre échelles,
la pluralité des perspectives, les origines communes et dérivées, le transport
des objections, les données invalides, la péremption, l'expiration, les pertes,
la reprise, les demandes invalides et le refus des frontières changeantes.
Les attentes ont été exécutées en échec avant leur implémentation.

Sur la base `main` `f84d88e9db708cf47378e3817e992cb6c758e017`, avec cet ajout,
vérifications locales du 6 octobre 2026 : **451 tests réussis**, dont **28
tests Uriel**, et **11 contrôles de continuité réussis**. Les scénarios incluent
la CLI réelle et la comparaison des octets persistés avant/après lecture.
`git diff --check` n'a signalé aucune erreur d'espacement.

Exécuter depuis `conscience-c/brain/` :

```sh
python -B -m unittest discover -s tests -q
python -B ../verify_reprise.py
```

La CI du commit examiné fournit la preuve des contrôles distants. Cette
vérification par l'auteur ne tient pas lieu de revue de code indépendante.
Le lint AI DevKit n'a pas pu être lancé dans l'environnement de préparation
(`ENOTCACHED` hors ligne) ; aucun succès de lint n'est revendiqué.
