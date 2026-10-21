# SOL-Action Bridge 0.1.0 — extension additive, candidate corrigée v2

Ancien contrat conservé : `public.sol_action_api(text,jsonb)`, schéma `sol_action`, worker `SOL-ACTION-PY/0.1.0` et oracle SQL inchangés. Le fichier `backend.sql` crée exclusivement `sol_action_bridge` et `public.sol_action_bridge_api(p_action text,p_input jsonb default '{}') returns jsonb`. Ne pas rejouer une installation ambiguë : CREATE SCHEMA échoue si elle existe déjà.

## Récupérer le reçu d'un rapprochement dont la réponse s'est perdue

HTTP `POST /api/job`, corps exact :

```json
{"action":"receipt","input":{"job_id":"UUID_DU_JOB","capability":"CAPACITE_PRIVEE_64_HEX","target_request_id":"UUID_DE_LA_REQUETE_RECONCILE_ORIGINALE"}}
```

La fonction Python traduit cette lecture en RPC bridge `lookup_receipt`, avec les trois champs exacts. Aucun nouvel UUID de mutation n'est créé. Aucun begin, worker, oracle, rapprochement ou écriture de table n'est exécuté. La lecture vérifie le job et sa capacité avec l'autorisation existante, puis lit seulement `sol_action.intents` et `sol_action.outcomes`.

Si l'issue existe :

```json
{"ok":true,"action":"lookup_receipt","status":"HISTORICAL_NOT_CURRENT","job_id":"UUID_DU_JOB","target_request_id":"UUID_CIBLE","found":true,"intent_found":true,"target_action":"reconcile","receipt":{"action":"reconcile","request_id":"UUID_CIBLE","status":"HISTORICAL_NOT_CURRENT","current_reuse_authorized":false,"begin_granted":false},"current_reuse_authorized":false,"automatic_retry":false}
```

Le reçu réel peut aussi contenir `production_request_id`, `result`, `pending`, `verification`, `completion` et `reconciled_outcome`. Un ancien begin imbriqué peut garder `pending:true` alors que le reçu externe du rapprochement porte `pending:false` avec le résultat effectivement conservé. L'interface doit vérifier le job, l'UUID cible, l'action du reçu et la corrélation avec l'intention en attente ; ne pas confondre le pending historique imbriqué et l'état externe rapproché.

Si aucune issue n'est trouvée : `ok:true,status:UNKNOWN,found:false,intent_found:boolean,receipt:null`, identifiants corrélés, sans autorité actuelle. Le pending doit rester conservé. UUID appartenant à un autre job, capacité erronée ou entrée invalide : refus générique `ok:false,status:REJECTED,error:NOT_AUTHORIZED_OR_INVALID_REFERENCE`, sans contenu privé. La lecture peut être renouvelée : elle n'a aucun effet métier et ne rejoue jamais l'intention recherchée.

Le CSV brut et les clés `capability`, `parent_capability`, `bridge_token`, `token` sont supprimés récursivement. La capacité fournie est aussi remplacée lorsqu'elle apparaît dans une chaîne. Les marqueurs `current_reuse_authorized`, `begin_granted`, `binding_granted` sont forcés à false partout où ils existent. Une ancienne observation PASS peut rester visible comme donnée historique ; aucune fraîcheur n'est créée.

## Version réservée avant begin

Deux tables privées append-only : `releases` et `bindings`. Elles sont sous RLS sans policy, sans droits directs pour public/anon/authenticated/service_role. UPDATE, DELETE et TRUNCATE sont refusés par triggers. Seul l'opérateur SQL propriétaire peut admettre une release par INSERT. Le répartiteur SECURITY DEFINER a `search_path=''` ; son wrapper public est SECURITY INVOKER. Les clients anon/authenticated n'ont accès qu'à `health`, `lookup_receipt` et `bind` contrôlés.

`releases` contient : `release_hash`, `manifest_hash`, `source_commit`, `source_files` (objet chemin→SHA256), `deployment_id`, `deployment_url`, `token_sha256`, empreintes courantes des runtimes SQL core et bridge et date/acteur d'admission. `token_sha256` est SHA256 du token **texte UTF-8**, jamais le token brut. Les empreintes SQL ont des valeurs par défaut calculées lors de l'admission. Le registre reste de confiance opérateur ; un INSERT ne constitue ni promotion ni preuve fournisseur.

Fichier `app/release-source.json`, produit après gel des quatre fichiers serveur effectivement attendus dans le bundle Python :

```json
{"schema":"SOL_ACTION_RELEASE_SOURCE/v1","files":{"api/job.py":"SHA256_REEL","api/mcp.py":"SHA256_REEL","bridge_runtime.py":"SHA256_REEL","vercel.json":"SHA256_REEL"}}
```

Pour cette candidate v2, la liste est exactement : `api/job.py`, `api/mcp.py`, `bridge_runtime.py` et `vercel.json`, chacun associé au SHA256 de ses octets. Le contrôle annonce `file_scope:BUNDLED_SERVER_FILES_ONLY`. Il exclut les fichiers `public/*`, le manifeste lui-même et `build-info.json`. Les chemins restent relatifs et confinés à l'application ; les empreintes sont hexadécimales minuscules. L'absence d'un fichier attendu doit refuser le contrôle, sans miroir ni substitution par une copie CDN.

Les fichiers publics de l'interface restent reliés au commit GitHub. Leur livraison est contrôlée séparément par des lectures HTTP du CDN, avec URL, déploiement ou alias observé, date UTC, code HTTP et SHA256 des octets reçus, comparés aux fichiers du commit. Cette observation externe datée ne prouve pas leur présence dans le processus Python, ni leur état futur après déplacement d'un alias.

Après le commit GitHub, produire `app/build-info.json` :

```json
{"schema":"SOL_ACTION_BUILD_INFO/v1","source_commit":"SHA_GIT_40_HEX"}
```

Calculs exacts : `manifest_hash = SHA256(octets exacts de release-source.json)` ; `release_hash = SHA256(manifest_hash + ':' + source_commit)` en ASCII. Le commit ne contient pas son propre SHA ; le build-info est un raccord généré après le commit, sans preuve d'origine par sa seule présence.

Dans le runtime Vercel, `SOL_BRIDGE_TOKEN` doit être une variable privée de 64 caractères hexadécimaux minuscules indépendants. Ne jamais l'écrire dans le code, le manifeste, `vercel.json`, les fichiers publics, GitHub ou les reçus. Le détenteur de ce secret peut se présenter comme le wrapper ; ce mécanisme n'est pas une attestation matérielle d'identité.

Avant toute nouvelle production, `bridge_runtime.py` relit le manifeste, le build-info et les octets réels des quatre fichiers serveur, vérifie chaque empreinte, puis calcule l'empreinte réelle `self_hash` de `api/job.py`. Il refuse les fichiers absents, chemins sortants, schémas inconnus et doublons de clés JSON. Ce contrôle local ne télécharge pas les fichiers publics du CDN.

Le diagnostic du 21 octobre 2026 a relu le [builder Python Vercel](https://github.com/vercel/vercel/blob/main/packages/python/src/index.ts), blob Git observé `abc51249f9c454d6f046a18e43e80dad328d35df` : `public/**` figure dans ses exclusions prédéfinies et ce code ne lit pas `includeFiles`. L'ancienne configuration `includeFiles` n'établissait donc pas la présence des assets publics dans la fonction. La candidate v2 la retire et réduit le manifeste aux quatre fichiers serveur ; leur inclusion réelle reste à vérifier dans le nouveau déploiement. La lecture de cette source du builder ne prouve pas à elle seule la version exacte utilisée par Vercel pour un déploiement donné.

Le wrapper appelle ensuite `bind` avec exactement : `job_id,capability,production_request_id,release_hash,manifest_hash,source_commit,self_hash,bridge_token`. `production_request_id` est l'UUID déjà préparé du futur begin. L'admission, le token, le job et les empreintes sont contrôlés avant toute insertion.

Le bind prend le verrou job du noyau existant. Il refuse un ancien begin ou résultat sans binding préalable, un UUID déjà utilisé, une release périmée, un hash différent, une capacité ou un secret incorrect. Une seule binding est autorisée par job ; elle fixe aussi l'UUID exact de production. Seule la première insertion retourne `status:BOUND_RELEASE,binding_granted:true`. Une répétition identique retourne un reçu historique avec `binding_granted:false` ; une variante est refusée. Aucun token brut ne figure dans les tables ou réponses.

Le bridge appelle l'ancien `sol_action.dispatch('begin', ...)` avec ce même UUID dans **la même transaction** que la binding. Il exige un begin nouveau et corrélé avant l'insertion finale ; un refus contrôlé du noyau est converti en exception afin d'annuler le bloc entier. Une erreur d'insertion de la binding annule aussi le begin. Aucun ancien corps n'est modifié. La réponse nouvelle ajoute `binding_and_begin_atomic:true,begin_receipt:{...}` avec le reçu réel du begin. Le wrapper utilise exclusivement ce reçu : il n'envoie jamais de second appel begin. Une binding passée ne rappelle ni le noyau ni le worker. Une réponse perdue laisse donc soit aucune des deux lignes, soit les deux ; lookup_receipt peut retrouver le begin historique. L'absence de résultat après begin garde le pending original, sans relance automatique. La fenêtre ancienne begin-avant-worker reste explicitement possible ; aucune nouvelle fenêtre binding-sans-intention n'est revendiquée comme résolue par une répétition.

## Portée des preuves

La preview `dpl_bcBJNStnWYpRbYdjy77zwtKwDZAo` a rendu une erreur de métadonnées ou d'intégrité lors de `release_manifest` ; le service antérieur a été rétabli et aucun job métier n'y a été lancé. Cette erreur reste conservée. La correction v2 constitue une nouvelle candidate à contrôler : elle ne reprend aucun succès de déploiement, de calcul ou de contrôle externe de la candidate précédente. Un manifeste localement correct ne vaut pas validation du nouveau runtime ; les réponses serveur actuelles et les observations CDN datées restent des preuves distinctes.

Le token et le selfhash attestent au plus une réservation faite par le détenteur du secret et la comparaison locale des octets annoncés. Ils ne prouvent ni une machine hostile isolée, ni une signature Vercel, ni le lien matériel entre un processus et un résultat. L'ancienne RPC demeure accessible avec ses anciens droits ; elle ne reçoit aucune nouvelle attestation de version. Une binding n'ajoute aucun verdict favorable à ses reçus. L'oracle SQL indépendant et son périmètre CSV restent séparés.

La mutation du noyau, le remplacement de ses fonctions, la suppression des anciens reçus, une promotion épistémique ou la publication des capacités ne font pas partie de ce module. Un retrait conservatoire révoque les deux droits EXECUTE bridge et retire le wrapper web correspondant, en conservant tables et historique pour examen. Aucun retrait distant n'a été exécuté par la préparation locale.
