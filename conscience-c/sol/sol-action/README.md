# SOL-Action — reprise et provenance 0.2

Cette extension du service SOL-Action corrige la perte d’une réponse de rapprochement : un reçu peut être consulté par son UUID exact et la capacité de sa tâche, sans créer une nouvelle intention ni relancer le producteur. Les identifiants absents ou non corrélés laissent l’issue UNKNOWN.

Le producteur Python et le vérificateur SQL de totaux CSV restent séparés. Une nouvelle liaison de version conserve le commit GitHub, le manifeste des fichiers et le déploiement déclaré par l’opérateur. Les fichiers sont contrôlés avant la réservation de production. Cette liaison, fondée sur un secret de service et un contrôle local des fichiers, ne constitue pas une attestation matérielle ni une garantie sur les appels directs de l’ancienne API.

La source est ajoutée à ce dépôt sur une branche isolée, sans modifier les anciens projets. `app/release-source.json` fige les octets des fichiers ; `app/build-info.json` est généré **après** le commit pour éviter une référence circulaire. Le manifeste ne contient pas son propre SHA ni le fichier généré.

`/mcp` expose uniquement `release_manifest`, sans accès aux tâches, CSV, capacités ou secrets. Le contrôle MCP Conduct Register porte sur la présence du protocole, de la carte descriptive, de la déclaration de compensation et sur le déterminisme mesuré. Il ne certifie pas les calculs, la sécurité ou une réussite générale.

StorageChain a été consulté en recherche/lecture. Les recherches ciblées n’ont retourné aucun document et le connecteur fourni ne propose pas de dépôt. Aucun ancrage StorageChain ni raccord permanent à ce fournisseur n’est revendiqué.

## Installation séparée

Le service de base est requis. La nouvelle migration `backend.sql` crée uniquement `sol_action_bridge` et son wrapper ; elle refuse un schéma déjà existant. Les anciennes fonctions SQL restent intactes. Le secret `SOL_BRIDGE_TOKEN` se configure directement dans l’environnement serveur Vercel et son empreinte seule est inscrite dans la release admise. Aucun secret de service ni capacité de tâche n’est livré ici. Les tables de liaison sont privées sous RLS, append-only, sans résistance WORM contre le propriétaire.

Le code public fait partie d’un prototype borné, sans transfert de poids, mémoire interne permanente, contrôle universel de Codex ou avantage général démontré. Un résultat exige ses observations actuelles ; un reçu historique ne donne jamais une permission ou une validation actuelle.

La politique documentaire du dépôt SECURITY_COMMAND et la continuité de Conscience C sont conservées. Cette application n’est pas raccordée à un contrôle AEGIS-24 live et ne prétend pas l’être.

Les preuves de cette installation sont livrées séparément de la source publique afin de ne pas publier les mandats, données privées et capacités. Les premières erreurs, les adaptations des fixtures et leurs limites restent conservées dans le paquet de preuves.
