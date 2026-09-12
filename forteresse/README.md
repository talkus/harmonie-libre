# Forteresse

Application web contemplative basée sur l'éthique de l'Amour Choisi.

## Le cycle

```
Repentance → Pardon → Gratitude → Espérance → (retour)
```

Seuil avant toute station : **Humilité**.

## Les 6 principes

> Créer sans mentir. Agir sans forcer. Pouvoir sans écraser. Se tromper sans s'y enfermer. Recevoir sans posséder. Espérer sans imposer.

## Fichiers

- `index.html` — Application complète (HTML + CSS + JS en un seul fichier)
- `manifest.json` — Configuration PWA
- `sw.js` — Service worker (mode hors-ligne)

## Déploiement

### Netlify Drop
1. Glisse le dossier sur https://app.netlify.com/drop
2. C'est en ligne.

### GitHub Pages
1. Push le dossier sur un repo GitHub
2. Settings → Pages → Source: main branch
3. Le site est sur `https://<user>.github.io/<repo>/`

### Vercel
1. `npx vercel` dans le dossier
2. Suivre les instructions.

### Local
Ouvre `index.html` dans un navigateur, ou :
```bash
python3 -m http.server 8000
```
Puis visite `http://localhost:8000`

## Valeurs techniques

| Valeur | Implémentation |
|---|---|
| Humilité | Aucun score/streak/classement. Seuil obligatoire. |
| Pardon | Regex auto-écrasement dans Repentance → micro-garde |
| Gratitude | localStorage. Export JSON. L'utilisateur possède ses données. |
| Espérance | Regex vigilance certitudes absolues. Champs optionnels. |

## Licence

MIT
