# Adaptateur InsForge optionnel — cohérence multi-échelle

**Statut :** contrat d'intégration seulement. Aucun backend InsForge n'est créé ou modifié par ce candidat.

Le noyau Python reste provider-agnostic. Une application TypeScript peut persister les reçus via `@insforge/sdk` derrière une interface `MultiscaleStore`, sans faire d'InsForge une autorité épistémique.

## Frontière proposée

```ts
export interface MultiscaleStore {
  appendReceipt(receipt: MultiscaleReceipt): Promise<void>;
  getReceipt(hash: string): Promise<MultiscaleReceipt | null>;
  listChildren(parentHash: string): Promise<MultiscaleReceipt[]>;
}
```

Configuration navigateur/Vite :

```ts
import { createClient } from "@insforge/sdk";

const insforge = createClient({
  baseUrl: import.meta.env.VITE_INSFORGE_URL,
  anonKey: import.meta.env.VITE_INSFORGE_ANON_KEY,
});
```

Ne jamais embarquer une clé admin/API dans le navigateur. Les opérations privilégiées éventuelles utilisent un client admin uniquement côté serveur.

## Schéma logique minimal

Une table de reçus peut conserver :

```text
receipt_hash PK
receipt_id
scale
parent_receipt_hash nullable
payload_json
status
created_at
```

Une table append-only de contestations peut conserver :

```text
contestation_id PK
source_receipt_hash
target_receipt_hash
target_assertion_ref
trace_refs_json
created_at
```

Règles :

- aucun UPDATE destructif d'une ancienne trace pour « corriger » l'histoire ;
- RLS par défaut pour les écritures utilisateur ;
- hash recalculé côté application avant admission ;
- `UNKNOWN` reste une donnée épistémique, jamais une permission ;
- le stockage d'un reçu ne prouve ni sa vérité ni son indépendance ;
- les migrations/RLS doivent être testées sur une branche backend avant production.

Ce fichier documente seulement la couture d'intégration. Il n'ajoute aucun secret, aucune URL de projet et aucune migration de production.
