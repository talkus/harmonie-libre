# Vigie Indexicale — témoin indépendant (proposition)

Statut : **expérience de revue**, sans autorité canonique ni décision de déploiement.

`R ≺ E` ; `S ≠ O` ; `HASH ≠ AUTHENTICITÉ` ; `UNKNOWN ≠ SATISFIED`.

Ce dépôt public ne contient **aucune archive Google Drive** ni contenu de conversation. Le programme `witness/verify.mjs` relit indépendamment les exports JSON (`VIGIE-V1`) de l'application Vigie Indexicale v0.2 archivée en Drive privé. Le code ne fait aucun appel réseau, n'accorde aucune autorisation et ne prétend pas connaître une identité civile.

```bash
node --test witness/tests/verify.test.mjs
node witness/verify.mjs export-vigie.json [recu-independant.json]
```

Le reçu indépendant a la forme `{ "tip": "<sha256>", "count": 4, "context": "ctx-1" }`. **Ne générez pas un reçu à partir du même journal que vous voulez authentifier** : une ancre doit être détenue séparément, et sa propre origine reste vérifiable. Le témoin rejette une chaîne cassée, une transition impossible, une auto-adresse, une assertion promue artificiellement à `E_PLUS`, une preuve de revue modifiée et un contexte périmé. Il contrôle les signatures Ed25519 contre des clés déclarées ; il **ne vérifie pas l'identité réelle du signataire**.

La version complète de l'application Netlify se trouve dans des livrables privés Drive. Son projet Netlify `vigie-indexicale-tikkun` a été créé mais **aucun déploiement publié n'est attesté** ; ce sous-dossier n'est ni le site ni son code complet. Une intégration future exigera un dépôt privé dédié ou une décision de publication distincte, puis un lien Git CD et une vérification `ready` réelle. La revue GitHub ne transforme pas les tests en preuve de production.

**Statut :** `CANDIDAT_A_REVUE` ; `modelAuthority=none` ; `authorization=NOT_ASSESSED` ; `CANON_NOT_ADOPTED`.

## Contrat d'interopérabilité v0.2 (fixture publique synthétique)

`fixtures/journal-synthetique-v02.json` est un export produit par **le moteur original v0.2** de l'application Netlify sur des octets artificiels. `fixtures/recu-synthetique-v02.json` est un reçu de test correspondant, sans qualité de témoin indépendant réel. Le témoin teste directement l'export, la signature Ed25519 et le reçu.

Les tests adversariaux reconstruisent aussi une chaîne SHA-256 cohérente après falsification : la grammaire des événements rejette une réponse auto-attribuée, et le reçu antérieur refuse une réécriture silencieuse de la provenance. Cette fixture synthétique n'est **pas** une preuve de l'authenticité d'une source Google Drive.

Le témoin accepte aussi le format `base64url` non capitonné accepté par le moteur Web Crypto de l'application. Les 15 tests du témoin sont exécutables avec `node --test witness/tests/verify.test.mjs` ; leur succès local ne garantit pas leur succès dans GitHub Actions avant vérification du nouveau workflow.

**Barrière de déploiement :** aucun système de CI ne déploie l'application privée Netlify. Un déploiement doit être réalisé séparément et observé `ready` ; aucune simulation de Merkabah ni décision de revue ne remplace le consentement humain.

## Relecture effective des octets — extension expérimentale

Le journal peut déclarer `OCTETS_HACHÉS` tout en pointant un SHA-256 inexistant. Le témoin `witness/bind-sources.mjs` **relit les fichiers locaux** qui lui sont explicitement fournis, compare leurs tailles, SHA-256 et références situées, et refuse les substitutions même lorsque la chaîne du journal est correctement recalculée.

```bash
node witness/bind-sources.mjs export-vigie.json chemins-locaux.json
```

Le manifeste `chemins-locaux.json` a la forme `{"schema":"VIGIE-SOURCE-MAP-V1","files":[{"id":"SRC-1","sourceRef":"drive:ID","path":"/local/path"}]}`. Il doit rester **local** : ne jamais commiter de chemins privés ni les sources en question. La sortie `CONCORDANCE_OCTETS_NON_AUTHENTIFIANTE` atteste seulement l'accord des octets relus avec le journal. **Elle n'authentifie ni Google Drive, ni l'identité du fournisseur, ni la vérité du référent.**

Les contre-épreuves du témoin passent de 15 à 27 en local. Le workflow GitHub doit être observé séparément pour confirmer leur exécution distante. La PR reste brouillon / non fusionnée ; aucun déploiement Netlify n'est créé par ce workflow.

## Ancrage contradictoire v0.5 — quorum de clés hors journal

Le témoin `witness/anchor-verify.mjs` vérifie un **préfixe historique** du journal contre un checkpoint signé par au moins **deux clés Ed25519 distinctes**, épinglées dans un fichier de confiance `VIGIE-TRUST-V1` fourni séparément. Il refuse une clé réutilisée depuis les événements `VERIFIER`, une signature invalide, un checkpoint étranger, une clé dupliquée, une ancre précédente manquante et une réécriture du préfixe. La portion non ancrée du journal reste explicitement identifiée.

```sh
node witness/anchor-verify.mjs export-vigie.json anchor.json trust-separe.json [previous-anchor.json]
node --test witness/tests/*.test.mjs
```

**Aucune clé privée n'est stockée dans le dépôt.** Les clés de test sont générées au cours de l'exécution des tests. Le code ne reconnaît ni les personnes, ni l'indépendance effective des dépositaires, ni la date réelle de garde du reçu : il retourne `independentCustody: NOT_ESTABLISHED`, `epistemic: E0`, `authorization: NOT_ASSESSED` même en cas de signature concordante. Le fichier trust lui-même doit être validé et gardé par une procédure humaine distincte ; deux clés créées par la même personne ne prouvent pas deux témoins indépendants. Le stockage d'un reçu dans Google Drive n'est pas un WORM matériel.

Cette suite est un **candidat d'audit**, non un mécanisme de déploiement ou une adoption canonique. Le site Vigie Netlify reste protégé et doit être déployé et testé séparément.

## Barrière de publication tripartite v0.6

Le module `witness/release-gate.mjs` exige des instantanés **distincts et récents** des trois services :
- GitHub : numéro/état de PR, SHA de tête et exécution CI du **même** SHA ;
- Drive : deux empreintes archivées, taille et permissions propriétaire seulement ;
- Netlify : ID du site, ID du déploiement et état `ready`, plus test navigateur sur cet identifiant précis.

Une revue externe explicite reste requise ; **une PR en brouillon ne satisfait pas la barrière de revue**. L'exécution locale de la barrière ne télécharge aucune donnée : un instantané JSON peut être fabriqué et son origine doit être contrôlée indépendamment. Même lorsque tout concorde, le verdict est `CANDIDAT_CONCORDANT_NON_AUTORISE`, `epistemic:E0`, `authorization:NOT_ASSESSED`.

```sh
node witness/release-gate.mjs snapshot-observe.json pins-externes.json 2026-10-29T13:00:00Z
node --test witness/tests/*.test.mjs
```

La première application aux faits observés le 29 octobre 2026 reste **BLOCKED_EVIDENCE** : PR brouillon, Netlify sans déploiement `ready` identifié, navigateur non vérifié, revue humaine externe non attestée. Aucun workflow de ce dépôt ne publie les fichiers privés de Vigie.

## Vérification distante des fichiers statiques Netlify — v0.7

Un projet Netlify existant, une URL plausible ou un résultat CI réussi ne prouvent pas qu'une version déterminée de Vigie est servie. Le témoin `witness/netlify-remote-probe.mjs` compare **les octets HTTPS** de sept fichiers visibles avec les empreintes de l'archive statique v0.5 : `fixtures/netlify-site-v05-sha256.json`. Il refuse redirections, faux sous-domaines, SSO (HTTP 401/302), substitutions binaires, CSP ou `nosniff` manquants et types MIME invalides.

Une installation disposant des **fichiers locaux de l'archive privée Drive** peut exécuter, après publication autorisée du site :

```sh
node witness/netlify-remote-probe.mjs \
  https://vigie-indexicale-tikkun.netlify.app/ \
  /chemin/local/du/site/public \
  fixtures/netlify-site-v05-sha256.json
node --test witness/tests/*.test.mjs
```

Cette opération **n'exige aucun secret Netlify** et **n'envoie aucun octet privé**. Elle ne contourne pas la protection SSO : si elle ne peut lire les octets protégés, le résultat est un refus explicite, non un succès de façade. La correspondance éventuelle des octets n'atteste ni l'identité du déploiement, ni le fait que le code ait fonctionné dans un navigateur, ni la source historique, ni l'autorisation humaine. `epistemic=E0` reste obligatoire. Les 19 contre-épreuves de ce module s'ajoutent aux 67 tests précédemment contrôlés ; un nouveau décompte CI doit être vérifié sur le commit courant.

**Cette PR reste un projet de revue et ne publie ni le code privé Netlify, ni les documents privés Drive, ni un jeton d'accès.** La publication reste une action distincte à réaliser sur le projet Vigie protégé puis à confirmer par son identifiant de déploiement.
