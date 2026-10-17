# Sol v0.5 — branche parité et équidistance globale (17 octobre 2026)

**Statut : version adoptée dans Google Drive, code source ajouté ici à titre traçable.** L'adoption ne crée pas à elle seule un service distant, ni une connexion AEGIS-24.

- Implémentation Python : `sol_parite_equidistance_globale_candidate_v05.py`.
- SHA-256 du code original : `044fb876a4f135b001b17b7d876181714dbd39caced93d1e2f9a28a69a3f1024`.
- API Python stateless : `api/index.py`, fonction `evaluate(payload)`.
- Dépendances historiques présentes dans ce dossier, mais aucune référence historique n'est remplacée.
- Acte d'adoption : [Google Drive](https://drive.google.com/file/d/12XRiFZuWZw-tuYRelHfBMTCiUnUqzwJZ/view).
- Paquet de référence et audit : [Google Drive](https://drive.google.com/file/d/11PqoIZRq9pAeKEMWbvKswKcv1atGWugM/view).

## Vérification locale minimale

Depuis ce dossier :

```python
from api.index import evaluate
x={"poles":["A","B"],"episodes":[
 {"provenance":"A","observation":[-1,0]},
 {"provenance":"B","observation":[1,0]},
 {"provenance":"N","observation":[0,0]}]}
assert evaluate(x)["counts"] == {"A":1,"B":1}
```

Contexte : des tests supplémentaires ont été exécutés dans la session de préparation ; leur résultat ne constitue pas une preuve formelle universelle. Paramètre neutre médian : 2,5 %. Pas de garantie de performances, pas d'authentification des identités de provenance. Construction Merkle héritée non conforme à RFC 6962.

## Intégration Lovable

Lovable est une façade de démonstration distincte. Si l'exécution utilise Pyodide dans le navigateur, elle doit importer les fichiers **Python originaux de cette version** sans traduire leur logique en TypeScript et afficher les échecs de chargement au lieu de simuler le moteur. Pas de mémoire externe, pas de décisions sur des personnes, aucune revendication de conscience ou de certification. 
