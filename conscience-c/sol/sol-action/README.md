# SOL-Action — reprise et provenance 0.2, candidate corrigée v2

Cette extension du service SOL-Action corrige la perte d’une réponse de rapprochement : un reçu peut être consulté par son UUID exact et la capacité de sa tâche, sans créer une nouvelle intention ni relancer le producteur. Les identifiants absents ou non corrélés laissent l’issue UNKNOWN.

Le producteur Python et le vérificateur SQL de totaux CSV restent séparés. Une nouvelle liaison de version conserve le commit GitHub, le manifeste des fichiers serveur et le déploiement déclaré par l’opérateur. Les quatre fichiers serveur sont contrôlés avant la réservation de production. Cette liaison, fondée sur un secret de service et un contrôle local des fichiers, ne constitue pas une attestation matérielle ni une garantie sur les appels directs de l’ancienne API.

La source est ajoutée à ce dépôt sur une branche isolée, sans modifier les anciens projets. Pour cette candidate v2, `app/release-source.json` associe exactement quatre chemins à leur SHA256 : `api/job.py`, `api/mcp.py`, `bridge_runtime.py` et `vercel.json`. Sa portée annoncée est `file_scope=BUNDLED_SERVER_FILES_ONLY`. `app/build-info.json` est généré **après** le commit pour éviter une référence circulaire. Le manifeste ne contient pas son propre SHA ni le fichier généré.

Les fichiers `public/*` restent figés par le commit GitHub et font l'objet d'un contrôle distinct de leur livraison par le CDN : URL, déploiement ou alias observé, date UTC, code HTTP et empreinte des octets reçus doivent être conservés et comparés au commit. Le contrôle Python ne lit pas le CDN, ne remplace pas un fichier manquant par une copie et ne prétend pas vérifier les assets publics dans son propre processus. Une lecture CDN datée ne garantit pas l'état futur d'un alias.

La première preview de cette extension (`dpl_bcBJNStnWYpRbYdjy77zwtKwDZAo`) a refusé le manifeste pour métadonnées absentes ou intégrité différente ; le service antérieur a été rétabli sans y lancer de job métier. Le diagnostic a retrouvé dans le [builder Python Vercel](https://github.com/vercel/vercel/blob/main/packages/python/src/index.ts), blob Git observé `abc51249f9c454d6f046a18e43e80dad328d35df`, l'exclusion de `public/**` et l'absence de traitement de `includeFiles`. La correction retire cette configuration inopérante et réduit le manifeste. Cette nouvelle candidate ne reprend aucun succès ni verdict de la précédente ; sa présence effective dans un nouveau runtime et ses observations CDN restent à vérifier séparément. La source du builder consultée n'atteste pas sa version exacte dans le déploiement.

`/mcp` expose uniquement `release_manifest`, avec sa portée de quatre fichiers serveur, sans accès aux tâches, CSV, capacités ou secrets. Le contrôle MCP Conduct Register porte sur la présence du protocole, de la carte descriptive, de la déclaration de compensation et sur le déterminisme mesuré. Tout résultat antérieur reste historique ; un contrôle de la nouvelle candidate doit être exécuté et conservé séparément. Il ne certifie pas les calculs, la sécurité ou une réussite générale.

StorageChain a été consulté en recherche/lecture. Les recherches ciblées n’ont retourné aucun document et le connecteur fourni ne propose pas de dépôt. Aucun ancrage StorageChain ni raccord permanent à ce fournisseur n’est revendiqué.

## Installation séparée

Le service de base est requis. La nouvelle migration `backend.sql` crée uniquement `sol_action_bridge` et son wrapper ; elle refuse un schéma déjà existant. Les anciennes fonctions SQL restent intactes. Le secret `SOL_BRIDGE_TOKEN` se configure directement dans l’environnement serveur Vercel et son empreinte seule est inscrite dans la release admise. Aucun secret de service ni capacité de tâche n’est livré ici. Les tables de liaison sont privées sous RLS, append-only, sans résistance WORM contre le propriétaire.

Le code public fait partie d’un prototype borné, sans transfert de poids, mémoire interne permanente, contrôle universel de Codex ou avantage général démontré. Un résultat exige ses observations actuelles ; un reçu historique ne donne jamais une permission ou une validation actuelle.

La politique documentaire du dépôt SECURITY_COMMAND et la continuité de Conscience C sont conservées. Cette application n’est pas raccordée à un contrôle AEGIS-24 live et ne prétend pas l’être.

Les preuves de cette installation sont livrées séparément de la source publique afin de ne pas publier les mandats, données privées et capacités. Les premières erreurs, les adaptations des fixtures et leurs limites restent conservées dans le paquet de preuves.
