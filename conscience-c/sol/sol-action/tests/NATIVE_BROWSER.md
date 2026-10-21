# Contrôle natif local : deux onglets, mêmes scripts publics

Serveur lancé par le relecteur : `http://127.0.0.1:8783/A` et `http://127.0.0.1:8783/B`. Session exec12756. État lisible : `/fixture/state`, copie mise à jour dans `audit/state-native-v2.json`. Le serveur écoute seulement127.0.0.1 ; aucune requête Supabase/Vercel ni capacité réelle. Une bannière rend cette limite visible.

Les fichiers `/intent-slot.js`, `/app.js`, `/missions.js` sont servis avec les octets exacts du gel1. Le serveur les fige au démarrage. La page de fixture ajoute un bootstrap et des contrôles distincts, sans modifier les scripts métier. Leurs hashes sont rendus par `/fixture/state`. Le HTML de fixture est donc différent du HTML produit ; il ne faut pas prétendre que son affichage est la page publiée.

## Cas natif1 : empêcher une seconde intention

1. Ouvrir les deux URLs dans le même navigateur et vérifier la bannière `Native Web Locks: true`. Les deux pages partagent l’origine127.0.0.1:8783.
2. Cliquer `#fixture-ready` sur chaque page. Ce bouton de fixture consulte status, sélectionne la mission fictive puis déclenche le change normal. Attendre que `#mission-verify` soit disponible. Le serveur compte normalement2 status.
3. Cliquer `#fixture-arm` pour retenir les retours verify. Puis cliquer le vrai `#mission-verify` de A et essayer celui de B rapidement. Le second peut déjà être désactivé par l’événement natif ; noter ce fait sans revendiquer un déclenchement simultané forcé.
4. Cliquer `#fixture-inspect` et conserver `#fixture-state`, `#mission-pending-id`, le statut disabled et la bannière. Attendu : un seul verify et le même UUID pending dans les deux onglets. Ne jamais inventer le clic d’un contrôle que le navigateur a refusé.
5. Cliquer `#fixture-release`. Si le délai de15s du vrai script s’est déjà écoulé, le retour ne sera pas adopté : l’intention reste alors UNKNOWN. Dans ce cas, le bouton `#mission-receipt` lit le même UUID, sans nouveau verify. Ce comportement reste une fixture locale, pas une panne fournisseur.

## Cas natif2 : préserver une intention étrangère

1. Après la fin explicite des requêtes du premier cas, conserver une copie de son état serveur. Cliquer `#fixture-reset` pour remettre seulement cette origine fictive, puis recharger les deux pages et utiliser `#fixture-ready` sur chacune.
2. Cliquer `#fixture-arm`. Dans A, cliquer `#mission-verify`. Dans B, cliquer rapidement `#fixture-foreign`, puis `#fixture-release` (idéalement avant le timeout15s de A).
3. Le contrôle de fixture injecte volontairement le pending exact `90000000-0000-4000-8000-000000000009`, pour éprouver la réponse tardive de A. Il ne simule pas une production ni une permission.
4. Dans A et B, cliquer `#fixture-inspect`. Attendu : l’UUID étranger reste dans le stockage après le retour de A, verify total1, aucun badge d’autorité actuelle dans A. Conserver le message de conflit ainsi que l’heure, pour distinguer réponse reçue et simple timeout.
5. Le bouton Action `#adapt` doit être désactivé pendant le pending Mission. Cela peut être consigné comme observation ciblée de blocage, sans prétendre avoir exécuté tout le parcours parent/enfant T08.

## Routes et entretien

`GET /fixture/state` ne lance rien. `POST /fixture/control` accepte uniquement `{"action":"hold"|"release"|"reset"}`. Les seules réponses métier supportées sont des fixtures locales status, verify, receipt. Aucun worker n’existe dans ce serveur. L’état et les compteurs séparent les lectures des demandes verify.

La v1 utilisait un aside sticky qui masquait le bouton et n’a émis aucun verify ; source et état historiques sont dans `audit/history/`. V2 ne change que ce style. Les résultats natifs sont à enregistrer par le coordinateur : ce fichier est une procédure, pas leur reçu.

Pour redémarrer après arrêt, choisir un **nouveau** state-file et conserver les précédents :

```sh
python3 -I -B tests/native_fixture.py --app-dir app --state-file audit/NOUVEL_ETAT.json --port 8783
```

Le serveur n’est pas un service installé. Le terminer après les contrôles en conservant son dernier état. Aucun nettoyage des données réelles ni retrait de service distant n’est nécessaire.
