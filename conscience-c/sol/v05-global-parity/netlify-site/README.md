# Sol v0.5 — site statique Netlify

Cette interface **ne contient pas** de traduction JavaScript du vote. Le calcul dépend uniquement de `api/index.py::evaluate` et des modules Python originaux du commit figé [`112ce958e21a874416b76c4cfa7753019d265ea9`](https://github.com/talkus/harmonie-libre/commit/112ce958e21a874416b76c4cfa7753019d265ea9). Le worker vérifie les empreintes SHA-256 des cinq sources téléchargées, importe Python via Pyodide et n'affiche jamais de vote de substitution si le chargement échoue.

## Installation sur Netlify

Depuis le dépôt public, utiliser **Deploy to Netlify** :

[Déployer le site statique](https://app.netlify.com/start/deploy?repository=https%3A%2F%2Fgithub.com%2Ftalkus%2Fharmonie-libre&create_from_path=conscience-c%2Fsol%2Fv05-global-parity%2Fnetlify-site)

Il faut sélectionner le compte Netlify visé et confirmer l'opération. Le paramètre `create_from_path` demande à Netlify de cloner ce **sous-dossier uniquement** (le `netlify.toml` de ce sous-dossier se retrouve donc à la racine du nouveau repo). Ne pas utiliser une connexion Git ordinaire à la racine de `harmonie-libre` : ce dépôt est un monorepo contenant d'autres projets.

Sans ce clic et le retour d'un déploiement `ready`, **le site Netlify n'est pas publié**. Ne pas présenter une URL de projet vide comme un déploiement fonctionnel.

## Contrôles

- Serveur statique à lancer localement, par ex. `python3 -m http.server 8080`, puis ouvrir `http://localhost:8080/`. Pyodide et les sources demandent Internet.
- Cas médian : A/B 1–1 ; majorité : 2–1 ; provenance divisée X : 1–1, X abstentionniste.
- Pas de stockage applicatif, ni secret, ni base de données. La requête Python est évaluée **dans le navigateur**, pas sur l'infrastructure Netlify.
- Ce laboratoire ne réalise **ni déploiement serveur du microkernel ni certification d'équité**, et il n'est pas connecté à AEGIS-24.
