# SOL — corrections vérifiées, 21 octobre 2026

Ce lot corrige deux défauts reproduits dans les systèmes existants. Il ne clôt pas le mandat général « construis un système qui réussi la ou tu échoues ».

## Deux défauts, deux portées

Le runtime d’héritage local comparait deux objets imbriqués partageant des références après callback. Cinq états altérés étaient admis comme restaurés dans le corpus ciblé. La version corrective fige le digest attendu avant callback. Les 29 tests historiques passent sur les deux versions ; dix contre-épreuves d’une seule famille ne donnent plus de fausse admission sur le correctif. Les callbacks restent de confiance, les alias extérieurs et effets externes ne sont pas restaurés, et état/journal restent non atomiques. La bibliothèque versionnée est disponible par import explicite ; aucun consommateur permanent de rollback n’est affirmé raccordé. L’ancienne installation reste intacte.

Dans l’interface Action/Mission, deux onglets pouvaient lire le même stockage ancien, réserver deux UUID, puis effacer l’intention de l’autre au retour d’une réponse. La version 0.3.1 coordonne les deux emplacements de reprise par Web Locks exclusifs, relit leur état avant réservation/envoi et compare exactement identité et intention avant écriture. Une absence de verrou ou un stockage corrompu conserve les données et bloque la nouvelle mutation ; les lectures possibles restent disponibles. Aucun nouvel appel métier n’est lancé automatiquement.

Recharger tous les onglets déjà ouverts de cette application avant l’usage concurrent : un ancien onglet 0.3.0 ne participe pas aux nouveaux verrous. Cette garde est coopérative entre onglets de même origine et profil navigateur ; elle n’isole pas un propriétaire, une extension hostile, un autre profil ou les effets serveur. Les identifiants de reprise restent secrets et ne doivent pas être publiés.

## Reproduction

Le harnais `tests/shared-browser.test.cjs` est autonome, sans dépendance externe. Fournir un nouveau chemin de reçu ; un ancien reçu n’est pas écrasé :

```js
const {run} = require('./tests/shared-browser.test.cjs');
run({sourceDir: './app', receiptPath: './new-shared-browser-receipt.json'});
```

Il utilise deux contextes JavaScript séparés avec Map de stockage, verrou et transport simulés. Il ne remplace pas une observation dans un vrai navigateur. Les corpus et résultats avant/après sont conservés séparément. Le cas secondaire T08, s’il n’est pas exécuté séparément, reste non vérifié.

Les 23 régressions Python existantes du proxy, du MCP public et du paquet de fonctions sont conservées. Les fichiers CDN sont contrôlés séparément du manifeste Python : le bundle Python Vercel ne contient pas le dossier public. Le commit GitHub relie les deux portées ; le manifeste de runtime ne prétend pas les confondre.

## Gouvernance et retrait

Le suivi Atelier conserve les exigences sémantiques UNKNOWN. Un journal PASS ne valide ni le langage naturel, ni le succès général, ni un effet d’un connecteur. Aucun schéma ni fonction SQL du noyau existant n’est remplacé. Les sources, échecs, anciens reçus et anciennes versions sont conservés. Le déploiement précédent reste disponible pour un retour de l’alias, avec contrôle du déploiement courant avant toute bascule. Un retour de version ne supprime ni ne rejoue les intentions et reçus ajoutés.

Continuum : le dépôt public de l’éditeur a été retrouvé, mais pas les douze fichiers normatifs privés requis pour son amorçage. Son état reste UNKNOWN ; la recherche et les limites sont conservées sous `continuum/`. La présence d’un connecteur ou d’un document ne lui confère aucune autorité actuelle, permission ou validation scientifique.
