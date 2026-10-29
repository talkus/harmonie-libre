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
