# SOL · Coordination — console locale

Ouvrir `index.html` avec ses deux fichiers voisins `styles.css` et `app.js`, ou les servir depuis un hébergement statique. Aucune bibliothèque, police distante, clé ou connexion de compte n’est nécessaire. La politique du navigateur interdit les connexions et les envois de formulaire.

La console accepte une réponse complète `bundle_status` de `public.sol_coordination_api` : objet direct, ligne SQL unique nommée `result`, enveloppe MCP texte Supabase connue, ou son propre export local explicitement non authentifié. Les frontières Supabase doivent être uniques et sur leur propre ligne. Aucune extraction heuristique d’un bloc choisi parmi plusieurs résultats n’est faite.

Importer le JSON par fichier, ou le coller puis choisir « Lire le texte collé ». Le mandat, les versions, chaque exigence et son contrat, la prochaine étape déclarée, les tentatives et les blocages sont disponibles sans troncature. La matrice reçue est comparée structurellement aux exigences intégrales des tâches terminales : omission, doublon ou filiation incohérente refusent l’import. Cette comparaison de données n’authentifie ni la source, ni ses empreintes déclarées, ni la vérité du mandat.

Le reçu reste historique, y compris pendant sa fenêtre de navigation de 60 secondes. L’échéance retenue est le minimum des échéances déclarées et de l’import local + 60 secondes. Importer un ancien export local ne renouvelle pas l’échéance du service. Les dates locales ne sont pas des attestations du fournisseur.

« Copier la lecture Supabase » et « Copier la lecture API » copient uniquement `bundle_status`. Aucun appel n’est envoyé ; aucune mutation ni intention mutante n’est préparée. L’exécution et les autorisations restent hors de cette console. L’export est un téléchargement local marqué `source_authenticated:false`, `current_reuse_authorized:false`, `semantic_truth:UNKNOWN`.

L’import est limité à 32 Mio. Un fichier plus grand est refusé explicitement ; aucun fragment de mandat ou d’exigence n’est présenté comme l’ensemble. Les données ne sont pas automatiquement stockées par le code. « Fermer l’observation » vide son état en mémoire ; ce bouton ne promet pas l’effacement des fichiers source ou des données conservées par le navigateur lui-même.

Le catalogue embarqué provient de `../connectors.json`. Il distingue outils exposés, absence d’outil et skill seul ; il ne revendique aucun compte connecté ni connexion runtime.

Les tests sont dans `tests/dom-tests.cjs`. Ils s’exécutent dans Node en appelant la fonction exportée avec un répertoire de preuves facultatif. Les reçus `../evidence/ui-dom-tests*.json` distinguent la première attente erronée corrigée et la reproduction finale. Le DOM est synthétique : ces tests ne vérifient pas le rendu d’un navigateur, l’authentification, Supabase distant ou un déploiement.
