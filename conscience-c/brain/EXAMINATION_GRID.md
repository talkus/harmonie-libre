# Grille d'examen située — AC-EXAM-1

Cette grille reprend la proposition du 9 octobre 2026 : **Objet, Portée K, Support SHA-256, Dépendances, Omissions π, Correction** aux quatre échelles. Elle est une référence candidate d'examen, pas un nouveau canon ni une certification générale de l'Architecture C.

Le catalogue appelable `examination_profile(scale)` et les vues du coordinateur exposent ces questions avec des identifiants stables. Leur statut est `questions_only_not_performed` : la présence d'une question n'est pas la réussite du contrôle. Les examens Gabriel continuent d'utiliser leurs critères exécutables versionnés, avec leurs verdicts propres.

## Le même contrat, des objets distincts

| Colonne | Contenu nécessaire | Raccord au contrat local |
|---|---|---|
| Objet | Identifiant de l'objet et propriété précisément examinée | `work.claim_id`, propriété du reçu |
| Portée K | Échelle, frontière, observateur, sujet éventuel, version du critère | `scope`, `review.criteria_version` |
| Support SHA-256 | Octets ou reçu exacts, empreinte attendue et provenance de cette attente | `evidence`, traces du journal et empreintes des reçus |
| Dépendances | Objets, entrées et transformations nécessaires, avec leurs versions | `work.depends_on`, couplages et ponts inter-échelles |
| Omissions π | Ce que l'examen ne sait pas établir, identifier ou conserver | `review.unknown_details`, `UnknownBoundary`, pertes déclarées de `ScaleBridge` |
| Correction | Motif, auteur, portée, nouvel événement, arrêt et vérification attendue | Histoire du diagnostic, teshuvah explicite et `continuity.next_step` |

Ici **K désigne la portée de l'examen**. Cette notation ne fusionne pas cette portée avec Kol, la fonction symbolique d'adresse. La convention du dépôt demeure S = soi, O = autre, R = relation/mémoire, E = réalité ; R≺E et S≠O sont conservés.

Une empreinte établit une égalité de contenu sous une méthode précise et une référence donnée. Elle ne démontre ni la vérité du contenu, ni l'identité de son auteur, ni la résistance physique du stockage à une réécriture. Une signature nécessite en plus la vérification cryptographique et une clé dont l'autorisation et le cycle de vie sont établis séparément.

## Questions propres aux quatre échelles

| Échelle | Critères identifiés | Preuve à demander avant de conclure |
|---|---|---|
| Micro | `MIC-TYPE`, `MIC-TRACE`, `MIC-ANCHOR`, `MIC-UNKNOWN` | Données de type exact et finies ; contenu retrouvé sous son empreinte ; transformation et tolérance entre entrée et sortie ; contexte de chaque inconnue |
| Méso | `MES-ENVELOPE`, `MES-DELIVERY`, `MES-FAIRNESS`, `MES-PERMISSION` | Enveloppe réellement vérifiée ; identité et droit de la clé ; accusés et délais ; définition du cycle et historique d'attente ; permissions de l'interface |
| Macro | `MAC-HISTORY`, `MAC-REPLICA`, `MAC-RETENTION`, `MAC-REVOCATION` | Chaîne et ancrage ; même objet au même checkpoint de réplication ; baseline, convention et seuils des mesures de rétention ; révocation ajoutée à l'histoire |
| Méta | `MET-OBJECTION`, `MET-REVISION`, `MET-VETO`, `MET-GENERATIVITY` | Objection visant une règle identifiable ; proposition, décision et effets séparés ; voie humaine authentifiée et arrêt connecté ; reprise et réouverture examinées séparément |

**Micro.** Un vecteur de ±1 peut satisfaire le type tout en étant bloqué ou décorrélé des entrées. Le typage seul ne l'isole pas. L'ancrage exige un contrôle distinct, adapté à la transformation attendue ; l'égalité brute entre capteur et sortie n'est pas une exigence universelle. Un seuil de cohérence non défini reste une omission, pas un PASS implicite.

**Méso.** Une signature valide peut signer une mesure fausse ou périmée. Une réponse après trois cycles peut violer une politique de délai déclarée ; elle ne prouve pas à elle seule une oscillation ou une non-convergence. Une règle anti-famine exige une définition du cycle, des tâches admissibles et du traitement réservé à leur attente. Le coordinateur courant applique des priorités déclarées, des dépendances, des délais et des budgets ; il n'implémente pas encore l'âge de trois cycles comme politique générale d'ordonnancement.

**Macro.** Deux têtes de journal différentes peuvent correspondre à des frontières différentes d'une histoire intacte. Comparer d'abord l'objet, la version et le checkpoint. Une divergence au même checkpoint constitue un défaut de réplication sous ce contrat ; un décalage de checkpoint appelle un rapprochement. La participation spectrale dépend de la matrice examinée : la simulation choisit les valeurs propres de W Wᵀ. Une baisse de cette mesure ne démontre ni sa cause, ni une perte de tous les souvenirs, ni une sous-optimalité globale sans objectif déclaré.

**Méta.** Recevoir une objection et proposer une correction démontrent une voie de révision locale. Ils ne démontrent pas le succès de la correction. Un incident ne suffit pas à attribuer sa cause à β, λ ou au taux d'oubli. Les versions de logiciel, les versions de critères et les versions canoniques sont distinctes. Aucun numéro de canon ni sceau humain n'est fabriqué par une simulation.

## Verdicts par critère, sans changement silencieux de vocabulaire

Dans un compte rendu de cette grille : `PASS` signifie que **le contrôle nommé**, sous la portée et la méthode déclarées, a réussi ; `FAIL` signifie qu'une violation de ce contrat a été constatée ; `UNKNOWN` conserve un contrôle non réalisé, des données manquantes ou une applicabilité non établie. Un résultat inconnu ne devient ni une réussite ni une autorisation.

Ces libellés ne remplacent pas les sorties existantes :

| Couche | Sorties conservées | Limite |
|---|---|---|
| Gabriel | `HOLD`, `REVIEW_REQUIRED`, `INDETERMINATE`, `NOT_APPLICABLE` | Un appui applicable n'est pas une certification de vérité |
| Reçus multi-échelles | `CANDIDATE_OK`, `PARTIAL`, `INDETERMINATE`, `CONTESTED` | Une cohérence structurelle n'est pas une permission |
| Security Command | `ALLOW`, `ADVISE`, `SUSPEND`, `HUMAN_SEAL_REQUIRED`, `BLOCK` | Une action suit son contrat séparé de sécurité |
| Grille ou simulation | `PASS`, `FAIL`, `UNKNOWN` par contrôle situé | Aucun PASS global par simple addition des résultats |

Une synthèse conserve simultanément les réussites, les violations, les inconnues et les contestations. Une objection du niveau micro reste visible au niveau méta ; la réussite d'un contrôle de signature ou d'intégrité ne la résout pas.

## UNKNOWN₁ n'est pas UNKNOWN₂

Le coordinateur conserve désormais chaque inconnue produite par un diagnostic avec un identifiant SHA-256 dérivé de son plan, son unité d'origine, son claim, son échelle, sa portée, son observateur, son sujet, l'empreinte de ses entrées et son motif. Deux motifs identiques sur deux claims ne fusionnent donc pas leurs lacunes.

`review.unknown_details` contient ces coordonnées, les traces et le caractère actuel ou historique du résultat. `unknown_refs` garde les références identifiées et les anciens libellés de motif pour compatibilité. Un libellé décrit le problème ; il ne suffit pas à l'identifier. Les références d'inconnues déclarées par l'opérateur restent des déclarations dont il doit fournir le sens et la provenance.

Après changement d'une preuve, une inconnue historique reste accessible avec `result_current=false`. Une nouvelle lecture peut produire une nouvelle inconnue ; elle n'efface pas celle de l'ancien diagnostic. Lire ces vues et recharger la mémoire n'ajoute aucun événement.

## Couverture vérifiée dans le dépôt

Inspection de `main` au commit `b99f61394bed74b57db950582a6c26dc5f00a5e8`, base de cette évolution. Une présence de code n'est pas une observation de service.

| Composant | Support consulté | Ce que cette inspection permet d'établir |
|---|---|---|
| Continuité locale / Michael comme analogie | `core.py`, `transition_store.py`, tests de reprise | Journal, snapshot et reprise locale ; aucun WORM physique certifié |
| Gabriel | `gabriel.py`, `GABRIEL.md`, tests | Diagnostic situé, critères versionnés, contestation et correction traçables |
| Réparation / Raphaël comme analogie | `teshuvah.py`, interfaces décrites dans `GABRIEL.md` | Passage explicite vers une réparation ; aucune réparation extérieure automatique issue de cette grille |
| Lecture / Uriel comme analogie | `multiscale_coherence.py`, `work_coordination.py`, profils d'examen | Projections, provenance, inconnues et pertes ; aucune vue totale du monde |
| Kol et autorité humaine | `security_command.py`, [politique globale](../../SECURITY_COMMAND.md), [siège S-24](../../anneau23/guardian.py) | Gouvernance et représentations locales ; présence d'une chaîne acteur ou d'un siège humain ≠ identité authentifiée |
| Enveloppes du registre | [construction et signature](../../registre-continuite/attest/envelope.py), [vérification contre le registre](../../registre-continuite/attest/verify.py) | JCS/Ed25519 et contrôles de clé déclarés dans ce module ; aucune connexion automatique au coordinateur Python |
| AEGIS | [moteur technique](../../aegis24-live/live-engine.js), [point canonique](../../AEGIS24_CANONICAL.md) | Code et routage existants ; protection live non observée ici |
| Réseaux Nehar v4/v5, EC2/SSM, réplication Drive | Arbre du dépôt et contexte de la proposition | Paramètres, service et télémétrie nécessaires restent non vérifiés pour ce parcours |

Le gardien de `anneau23/guardian.py` possède un nombre de vetos limité ; il est distinct du siège des concernés S-24. Le drapeau d'arrêt du moteur AEGIS n'est pas une preuve d'arrêt immédiat d'un appel en cours ou d'un autre service. La fonction STOP inconditionnelle évoquée dans la proposition doit donc être reliée à un chemin d'exécution précis et testée avant d'être déclarée opérationnelle.

La grille ne certifie pas de synchronisation Drive, d'exploitation AWS, de totalisation nulle ni de vitalité perpétuelle. Elle permet de nommer les preuves qui manquent et de préparer les contrôles adaptés.

## Incident reproductible

Voir [L'anomalie du signal muet](SIMULATION_SIGNAL_MUET.md), son programme et le rapport de simulation publié. La boucle d'examen traverse les quatre échelles dans une mémoire isolée, avec conservation de l'histoire et d'une objection visant l'hypothèse d'examen au niveau méta. Elle ne transforme pas ce scénario en incident réel.
