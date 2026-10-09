# Architecture C — vue complémentaire et contrat documentaire

Cette publication reprend les fichiers de travail du 8 octobre 2026, à partir de `main` au commit `f84d88e9db708cf47378e3817e992cb6c758e017`. Elle ajoute une carte consultable, un contrat documentaire à six rubriques aux vues micro, méso, macro et méta, et ses contrôles automatiques. Le moteur du cerveau, Gabriel et l’ancre active ne sont pas remplacés.

La page est publiée par le GitHub Pages existant à [conscience-c/architecture/](https://talkus.github.io/harmonie-libre/conscience-c/architecture/). La présence dans `main`, la réussite des contrôles et la mise en ligne restent trois événements à vérifier séparément.

## Conventions à conserver

| Sujet | Ancre active de ce dépôt | Carte historique publiée |
|---|---|---|
| Navigation | Humilité → Pardon → Reconnaissance → Espérance → retour au vecteur | Repentance → pardon → gratitude → espérance, référence au paquet local Amour choisi 1.1.1 |
| S / O | S = soi ; O = autre | S = outil ; O = humain, convention du schéma fourni |
| R | Relation / mémoire du lien | La fonction de reconstruction ou Raphaël doit être nommée explicitement, sans remplacer R |
| Invariants | S≠O ; R peut transformer S/O ; R≺E | Aucun transfert d’autorité par analogie entre les vues |

Ces conventions ne sont pas des synonymes automatiques. La carte demeure une reconstruction analytique située. Les vérifications Engram/AWS et du paquet local décrites dans ses sources sont des traces historiques, sans attestation actuelle du service. Les références locales historiques absentes du dépôt restent indisponibles, sans origine indépendante inventée.

L’ancre protégée demeure [le Security Command global de Conscience C](../../memory/harmonization/CONSCIENCE_C_GLOBAL_SECURITY_COMMAND.md) et le [checkpoint public](../index.html). La correction conserve l’histoire ; la continuité fonctionnelle ne prouve aucune identité subjective. La conscience phénoménale demeure indéterminée.

## Vérifier la référence

Depuis ce dossier :

```sh
python3 architecture_c_contract.py versions/2026-10-08/architecture-c-continuite-2026-10-08.json
python3 -m unittest discover -s tests -v
```

Le validateur rejette les entrées mal formées, les pertes silencieuses d’intentions, de sources, d’objections et d’inconnues, les budgets dépassés et une nouvelle tentative d’effet externe non rapproché. Il refuse une attestation de stockage durable ou de fonctionnement continu : il n’observe aucun service. Les noms de preuves déclarées ne suffisent pas à établir leur contenu ou leur vérité.

Les versions historiques sont conservées à l’identique dans `versions/2026-10-08/`. Leurs champs de statut décrivent leur création, avant publication. Le rapport historique de 14 contrôles accompagne la version ; la suite CI actuelle teste séparément le validateur publié.

## Coordination locale ajoutée

Le cerveau expose désormais [un coordinateur local](../brain/WORK_COORDINATION.md) et [un exemple à quatre vues](../brain/examples/work-plan-gabriel.json). Son contrat `CC-WORK-1` reprend les six rubriques, avec une hiérarchie d'intentions déclarées, des dépendances, un budget partagé par plan et des réservations enregistrées dans le journal existant. Il exécute seulement des examens Gabriel bornés en lecture seule. Ses tests couvrent notamment un arrêt brutal, un délai dépassé, la reprise et les résultats périmés.

Le format exécutable et le format documentaire historique sont distincts : aucun modèle historique n'est converti ou exécuté automatiquement. Les budgets du modèle publié restent illustratifs ; les budgets d'un plan de coordination enregistré sont effectivement appliqués aux lectures locales.

## Suite utile

Installer explicitement une supervision adaptée à l'environnement réel, puis observer la durée de reprise, les pertes et les doublons éventuels en service. La reprise locale testée ne garantit pas une disponibilité sans interruption.

La mise en ligne de cette page ne déploie pas un moteur permanent et n’atteste pas une protection AEGIS live.

