# Security Command — entrée du hub projets

Cette fiche ne définit **pas** une seconde politique.

Références canoniques :

- politique : [SECURITY_COMMAND.md](../../SECURITY_COMMAND.md)
- page publique : [Security Command](../../security-command/)
- registre machine : [project-registry.json](../../security-command/project-registry.json)
- Conscience C : [registre C(tₙ)](../../conscience-c/)

Verdicts canoniques :

`ALLOW · ALLOW_WITH_LOG · REQUIRE_HUMAN · BLOCK · UNKNOWN`

AEGIS-24 est la surface de sécurité désignée dans la politique publique. Une intégration documentaire n'est pas une preuve de protection AEGIS live : celle-ci exige des heartbeats, un état et des journaux attestés.

Le runtime privé WayMaker possède un préflight déterministe et une garde CI qui reprennent cette politique sans donner au modèle de langage l'autorité de la relâcher.
