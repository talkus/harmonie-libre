# Outils pour le suivi du cas-limite nº 1

Ce guide documente des opérations ponctuelles. Il ne configure aucune veille automatique.

## Publier un commentaire avec GitHub CLI

La documentation officielle actuelle décrit `gh discussion comment`, `--repo` et `--body-file`. Vérifier que la version installée expose cette commande :

```bash
gh discussion comment --help
```

Après relecture du fichier et décision de le publier, depuis la racine du dépôt :

```bash
gh discussion comment 1 \
  --repo talkus/harmonie-libre \
  --body-file discussions/001-reponses-objections.md
```

Cette commande envoie un nouveau commentaire public sous le compte GitHub authentifié. Elle ne prépare pas un brouillon. Vérifier ensuite son lien direct. Ne pas relancer l’envoi sans vérifier si le premier a abouti, afin d’éviter un doublon. Le fichier de réponses reste une proposition tant que cet envoi n’est pas effectué.

Si la commande n’est pas reconnue, consulter la version installée et la documentation ; l’interface de la Discussion permet aussi de commenter. Ne pas remplacer une Discussion par une issue portant le même numéro.

Source : [manuel officiel de gh discussion comment](https://cli.github.com/manual/gh_discussion_comment), consulté le 2026-09-09. La syntaxe a été vérifiée dans la documentation ; aucun nouveau commentaire n’a été envoyé pour la tester.

## Vérifier la lecture publique

`curl -I` récupère les en-têtes. Un statut HTTP 200 ne suffit pas à confirmer la présence du texte ou le fonctionnement des commentaires. Un contrôle du contenu peut utiliser :

```bash
curl -q -sS -L --connect-timeout 10 --max-time 30 \
  --dump-header discussion-1-headers.txt \
  --output discussion-1.html \
  --write-out 'HTTP %{http_code}\n' \
  https://github.com/talkus/harmonie-libre/discussions/1
```

Cette invocation ne fournit ni cookie ni identifiant ; `-q`, en première option, désactive la lecture de la configuration curl par défaut. Examiner le fichier HTML reçu : titre, cas et texte des commentaires visés. La présence d’une ancre seule n’est pas suffisante.

Pour vérifier l’interface, ouvrir aussi la page sans session connectée, par exemple dans une fenêtre privée, et contrôler la lecture effective du cas et des commentaires. Distinguer lecture et possibilité de répondre. Un indicateur global de disponibilité de GitHub ne vérifie pas cette page précise.

Source : [manuel officiel de curl](https://curl.se/docs/manpage.html).

### Contrôle du 2026-09-09 (UTC)

- Récupération HTTP sans authentification : statut 200.
- Le texte reçu contient le cas, la clarification 18361660 et la clarification consolidée 18361670.
- Le HTML contient aussi des messages d’erreur de chargement. Le fonctionnement complet de l’interface en navigation privée n’a pas été vérifié.
- Les deux commentaires observés sont identifiés comme essais éditoriaux internes. Aucun retour indépendant n’a été observé dans ce contenu lors du contrôle.
- L’épinglage n’a pas été vérifié par ce contrôle.

Cette observation ponctuelle ne prouve ni l’absence de retours antérieurs ni l’accès sans incident pour tous les visiteurs. Elle ne vaut aucune adhésion.

## Consigner un contrôle ultérieur

- Date, heure et fuseau : [à compléter].
- Page et moyen utilisés : [URL ; navigation sans connexion ou récupération HTTP].
- Périmètre réellement lu : [cas, commentaires, réponses, pagination].
- Résultat constaté : [texte lisible ; lecture partielle ; consultation indisponible].
- Sources des éventuels retours : [liens directs ; distinguer essai interne et contribution indépendante].
- Suite : [proposition ; désaccord restant ; aucune conclusion si consultation impossible].

En cas d’échec : « Retours non vérifiés : consultation indisponible par le moyen utilisé. » Ne pas transformer un échec en absence de réponse.
