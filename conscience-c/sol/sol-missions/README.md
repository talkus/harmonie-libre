# SOL-Missions — liaison d'un résultat à une mission

Extension additive de SOL-Action et de SOL-Coordination. Un opérateur enregistre avant production le bundle complet, tous ses mandats et exigences, le job CSV exact et la release admise attendue. Le service existant exécute ensuite le calcul. Une vérification explicite recalcule l'oracle SQL, compare les définitions, la source, le résultat, le journal, la release et une observation récente des fichiers serveur.

Le verdict favorable est limité à `CSV_EXACT_CENTS/v1`. Toutes les exigences naturelles restent conservées avec `validation:UNKNOWN`, et le mandat général reste `UNKNOWN`. La liaison documentaire déclarée par l'opérateur n'est pas une validation du sens du mandat.

Le module crée uniquement le schéma privé `sol_missions` et son API. Les anciennes fonctions ne changent pas. Les clients utilisent la capacité du job ; seul l'opérateur SQL peut enregistrer une mission. Les tables sont append-only et protégées par RLS, mais le propriétaire de base reste une racine de confiance : ce registre n'est pas WORM.

Une intention est conservée avant envoi. Après perte de réponse, `receipt` consulte le même identifiant sans relancer le calcul ni la vérification. Un reçu retrouvé ou relu est historique et ne prolonge aucune échéance. Un résultat technique actuel expire au plus après 60 secondes.

L'identité des fichiers est une déclaration du détenteur du token serveur, contrôlée contre les fichiers locaux et la release admise. Elle ne constitue pas une attestation matérielle. Le prototype n'entraîne pas les poids d'un modèle et ne démontre aucun avantage général sur Codex.

Le dossier adjacent `sol-action/app` contient le service Vercel étendu. Le manifeste couvre quatre fichiers Python serveur ; les fichiers publics sont contrôlés séparément. `build-info.json` est généré pour le déploiement après le commit source, afin d'éviter une référence circulaire. Aucun token serveur ni capacité de job n'appartient au dépôt.

Voir `API.md` pour les entrées, contrôles, limites et conditions de retrait. Les scripts de retrait ferment les accès au nouveau module sans effacer ses données ou les anciennes installations ; leur exécution demande un mandat actuel de retrait.
