# L'anomalie du signal muet — simulation locale

Ce parcours rend le scénario du 9 octobre 2026 reproductible. Les calculs, les signatures de test, le journal local, les examens Gabriel et les rechargements de mémoire sont réellement exécutés. Le capteur, le canal, les répliques et la matrice sont des objets de simulation ; aucune connexion AWS, Drive ou AEGIS n'est effectuée.

## Résultat de la traversée

| Échelle | Observation dans la simulation | Résultat et limite |
|---|---|---|
| Micro | Entrées `[-1, +1, -1, +1]`, sortie figée `[+1, +1, +1, +1]` ; les valeurs sont des flottants binaires finis | Type PASS ; alerte de saturation ; ancrage de terrain UNKNOWN. La trace brute est conservée et la sortie n'est pas admise comme observation empirique |
| Méso | Une signature Ed25519 de test est valide ; le canal défectueux attend quatre cycles selon la convention du scénario | Signature cryptographique PASS ; autorisation de la clé UNKNOWN ; délai FAIL. Le triage et la quarantaine sont simulés, pas installés dans un répartiteur réel |
| Macro | Deux répliques au même checkpoint ont des racines de contenu différentes ; la participation spectrale de la matrice jouet passe de 2 à 1 | Comparaison des répliques FAIL ; seuil spectral de la fixture FAIL ; journal local intact. Une réplique à un autre checkpoint reste UNKNOWN, sans corruption déduite automatiquement |
| Méta | Une objection questionnant l'hypothèse d'examen est enregistrée et retrouvée après rechargement | Réception et conservation de l'objection PASS ; correction, causalité de β, sceau humain et effets sur le terrain restent UNKNOWN |

Les contrôles portent chacun sur un objet et une méthode précis. Ils ne produisent pas de PASS global. Chaque étape expose les six colonnes de [la grille AC-EXAM-1](EXAMINATION_GRID.md).

Le parcours utilise cinq unités : deux lectures micro, puis méso, macro et méta. La seconde lecture micro est indépendante du canal mis en quarantaine. Elle termine dans le coordinateur malgré l'anomalie ; cela démontre une lecture indépendante disponible, pas la disponibilité permanente d'un service externe.

Le programme recharge réellement la mémoire après chaque lecture. Les inconnues des cinq unités, même lorsqu'elles ont le même motif, conservent leurs claims et leurs identifiants distincts jusque dans la vue méta. L'objection reste ouverte et l'histoire antérieure est conservée.

## Ce que le scénario ne peut pas conclure

Le typage ne suffit pas à arrêter une dérive sémantique : ±1 est précisément le type accepté dans ce cas. Il faut un contrôle distinct de l'ancrage et une politique d'admission. La fixture conserve la trace suspecte, sans la présenter comme un fait de terrain.

Le dépassement de délai viole ici une politique illustrative de trois cycles. Il ne démontre pas un cycle limite ou une non-convergence. La règle de triage des paquets âgés de trois cycles est exécutée dans la fixture ; le coordinateur publié conserve son ordonnancement par intentions et dépendances, sans vieillissement général des priorités.

La participation spectrale est définie ici par `(tr G)² / tr(G²)`, avec `G = W Wᵀ`. La baseline est une identité 2×2 ; la matrice dérivée possède deux lignes identiques. Le seuil 1,5 appartient à ce test, pas à un réseau Nehar réel. Une projection orthogonale ne peut pas à elle seule recréer les dimensions déjà perdues : les données et la baseline utiles à une récupération doivent être conservées et réexaminées.

Le programme ne choisit pas β ou λ et n'applique pas de remédiation automatique. L'incident ne démontre pas leur causalité. La proposition finale est : **séparer contrôle de type et ancrage empirique, et comparer les répliques au même checkpoint**. Elle reste `ASSISTANT_PROPOSAL_REVISABLE`, sans sceau humain, sans effet externe et sans nouvelle version canonique.

## Reproduire

Depuis `conscience-c/brain/`, dans un environnement Python de travail :

```sh
python3 -m pip install -e ".[simulation]"
python3 -m conscience_c_brain.signal_muet_simulation
```

Pour conserver un nouveau rapport :

```sh
python3 -m conscience_c_brain.signal_muet_simulation --output signal-muet-nouveau-rapport.json
```

Le programme crée puis détruit une mémoire temporaire réservée au scénario. Son API refuse un dossier déjà rempli : elle ne réinitialise pas une mémoire réelle. Le bootstrap de cette fixture est distinct de la reprise à C(tₙ) du projet.

Le [rapport publié](examples/signal-muet-report.json) est une capture d'un essai local, avec `simulation=true`, `source_class=reconstruction_analytique`, `execution_authority=false` et `continuous_service_observed=false`. Ses empreintes d'événement permettent de reconnaître cette capture ; elles ne constituent pas un accès à un journal permanent ou un témoignage indépendant. Relancer le programme renouvelle les dates, les clés éphémères et les empreintes, tout en reproduisant les mêmes observations numériques et limites.

## Contrats techniques de la fixture

- La clé Ed25519 est éphémère et sa partie privée n'est jamais écrite. Le paquet `CC-SIM-SIGNED-1` utilise un JSON trié UTF-8. Il n'est ni une enveloppe RFC8785-JCS du registre ni une identité d'acteur autorisé. Une signature valide ne valide pas son contenu empirique.
- L'arbre de test `CC-SIM-MERKLE-1` sépare les feuilles des nœuds internes, duplique la dernière feuille d'un niveau impair et engage le nombre de feuilles dans la racine finale. Ce n'est pas une preuve de cohérence RFC9162 ni un stockage WORM physique.
- Le cerveau conserve son journal local par chaîne SHA-256. Toutes les preuves du scénario y sont classées comme reconstructions analytiques ; les cinq diagnostics Gabriel restent donc `INDETERMINATE`. Les PASS et FAIL de la fixture sont des résultats de contrôles du scénario, avec leur portée explicite.
- Les questions du profil d'examen ne s'auto-certifient pas. Une objection, une proposition et une réparation démontrée restent trois événements distincts.

## Vérification

La CI installe l'option `simulation` et exécute les tests de signature altérée, de type ambigu ou non fini, de comparaison de répliques, de calcul spectral, de parcours complet et de refus d'une mémoire existante. Les tests des inconnues situées vérifient également leur séparation, leur stabilité après rechargement et leur conservation lorsqu'un seul claim change.

```sh
python3 -m unittest discover -s tests -v
```

Ces essais soutiennent la robustesse et la révisabilité **locales du parcours testé**. Un service distant, une correction d'un réseau réel et un scellement humain exigent leurs propres preuves et décisions.
