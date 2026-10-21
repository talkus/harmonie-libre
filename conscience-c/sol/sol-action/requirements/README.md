# Garde des exigences : installation et frontières conservées

Le module additif est défini dans [migration.sql](migration.sql), son contrat borné dans [API.md](API.md), et sa préparation initiale dans [freeze.json](freeze.json). Ce dossier ne remplace aucune fonction, permission ou release ancienne. Les parcours Action/Bridge historiques restent disponibles et en dehors de l’obligation du nouveau garde ; l’absence d’interception universelle reste explicite.

Les reçus gardés ne transforment ni UNKNOWN sémantique, ni preuve historique, ni score déclaré en autorisation. Une exigence inconnue bloque le parcours gardé avant begin ; les contrats exacts sont réexaminés avant verify/complete. Une tentative ambiguë n’est pas rejouée automatiquement. La portée d’un refus reste celle de cet appel, sans annuler une tentative composite externe ou un worker antérieur.

Deux harnais distincts existent : [tests-dml.sql](tests-dml.sql) pour les régressions de l’auteur du backend ; [corpus-harness/tests-frozen-corpus-dml.sql](corpus-harness/tests-frozen-corpus-dml.sql) pour les entrées et attentes gelées par l’auditeur. Les résultats réels doivent être conservés séparément des préparations. Le nouveau harnais n’a pas été exécuté à distance par son auteur.

La [notice détaillée](corpus-harness/README.md) documente les sources exactes, les 39 cas SQL, les 14 sous-cas G40–G42, leurs limites, le rollback des fixtures, les chemins legacy et les garanties qui restent UNKNOWN ou NOT_EXECUTED. Les 42 cas complets ne sont jamais déclarés exécutés au seul motif que des sous-cas passent.
