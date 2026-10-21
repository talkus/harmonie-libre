# SOL-Coordination 0.1.0

Ce module réunit un mandat et ses compléments sans perdre leurs exigences lorsqu'un pointeur documentaire vise une ancienne tâche. Il complète les installations SOL-Lamarck, SOL-Preuve et SOL-Atelier existantes.

- `backend.sql` ajoute un schéma privé et une RPC de navigation, sans modifier les fonctions des modules existants. Une installation exige leurs schémas compatibles ; ne pas appliquer cette migration sur une base vierge ou une installation déjà créée.
- `hub.py` prépare explicitement une action Atelier après lecture actuelle, conserve son UUID avant envoi et rapproche son reçu. Il n'exécute aucun outil et ne rejoue aucune intention ambiguë.
- `ui/index.html` ouvre une console de lecture. Importer un reçu complet `bundle_status` avec ses mandats et exigences ; aucune donnée importée n'est envoyée au réseau par cette console.
- `connectors.json` recense des capacités exposées lors de la construction. L'existence d'un outil n'établit ni l'accès au compte, ni son intégration au runtime.

Le résolveur suit au plus 64 versions, contrôle les préfixes intégraux d'exigences et assemble au plus 17 tâches de 16 exigences. Les journaux sont append-only pour les rôles clients ; le propriétaire de la base ou du disque garde un pouvoir d'altération. Les exports locaux ne sont pas signés par les fournisseurs.

Le serveur ne fait que naviguer et assembler. Les actions Atelier restent distinctes, avec étape exacte et UUID fixé avant l'envoi. La conformité sémantique, le mandat externe et une éventuelle clôture bornée doivent être établis séparément. Une qualification historique ou un test local ne les remplace pas.

Les sources génériques sont publiées dans ce répertoire. Les mandats réels, bases locales et reçus de comptes sont conservés dans le paquet privé de livraison et ne sont pas inclus ici. Cette version n'établit aucune supériorité générale sur un assistant, conformité canonique SOL/BC-01, mémoire interne permanente ou intégration opérationnelle à dix-sept services.
