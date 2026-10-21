# SOL-Action 0.3.4 — retrouver un refus d’enregistrement

Cette version corrige un cas précis : le serveur refuse une nouvelle demande, mais sa réponse est perdue avant l’existence d’une tâche. Le navigateur conserve l’identifiant choisi avant l’envoi et peut lire la preuve du refus. Cette lecture ne renvoie pas la création et ne lance aucun calcul.

Le serveur Python injecte son admission de version et son secret existant. La nouvelle API SQL réserve l’intention, appelle le noyau inchangé et conserve les refus SQL contrôlés dans un registre append-only distinct. Un refus sans tâche ne crée aucun faux job. L’accès à son reçu exige la capacité originale. Les succès retrouvés restent historiques ; vérifier puis clore exigent toujours des observations actuelles.

## Utiliser

Ouvrir https://sol-action-verifiee.vercel.app/, essayer les données fictives, puis Enregistrer → Produire → Vérifier → Clore. Après une réponse absente, choisir « Retrouver l’issue de la demande », avec le même navigateur et profil, sans effacer les données du site. Une issue inconnue bloque tout rejeu. Une demande refusée avec preuve peut être corrigée par une action explicite ; son histoire est conservée.

## Contrôles distincts

- 43 tests Python : proxy, identités, refus, paquets et surface MCP.
- 30 contrôles SQL transactionnels : succès et refus réels du noyau, capacités, références croisées, doublons, changements de payload, quotas, ACL et conservation des fixtures après rollback.
- 6 scénarios UI synthétiques comparés à 0.3.3 ; les marqueurs de la nouvelle API sont différents. Les premières mesures et leurs corrections sont conservées dans les preuves de livraison.
- 8 contrôles de l’origine exacte des reçus ; 29 de format ; 11 de stockage partagé interonglets.
- Un navigateur réel avec transport local simulant la perte : un seul create, rechargement, une lecture de reçu, zéro worker. Ce scénario ne prétend pas avoir exécuté Supabase.

Les observations du service publié et du registre MCP sont fournies séparément avec la livraison. Un test, une empreinte ou un champ PASS ne prouvent aucune réussite générale.

## Limites

Le mécanisme couvre uniquement les créations admises dans cette nouvelle API. Les anciennes API restent accessibles ; leurs refus non enregistrés restent UNKNOWN. Les refus avant réservation (authentification, format d’enveloppe, admission, quotas du garde) ne disposent pas de reçu durable. Une réponse perdue reste alors UNKNOWN. Les quotas sont 128 réservations globales et 32 par capacité par jour UTC ; le coût d’audit croît avec le journal.

Aucune connexion universelle aux services mentionnés dans le mandat n’est installée. Le calcul reste un agrégateur CSV fixe ; les exigences sémantiques, la conformité canonique SOL/BC-01 et l’avantage général sur un assistant ne sont pas démontrés. Aucun poids du modèle n’est modifié.

## Retour possible

Conserver les déploiements, admissions et tables. Le déploiement 0.3.3 antérieur peut reprendre l’alias par décision opérateur explicite. Cela ne retire ni les intentions ni les reçus du garde. Son ancienne interface ne sait pas résoudre les refus du nouveau registre : conserver le nouveau lecteur disponible ou rétablir 0.3.4 avant leur reprise, avec le même navigateur/profil. Ne jamais réenvoyer une intention ambiguë pour compenser un retour de code. Aucune restauration de données ni retrait de garde n’est automatique ; les scripts de retrait ne sont pas exécutés par cette livraison.

Source et API : `backend/migration.sql`, `backend/API.md`. La migration additive est à usage unique ; ne pas la rejouer après une réponse ambiguë. Le registre est protégé par ACL/RLS/triggers ordinaires, sans être WORM face au propriétaire PostgreSQL. Une empreinte de fonction n’atteste ni la machine, ni tout le schéma, ni l’isolation hostile.
