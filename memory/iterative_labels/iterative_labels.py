"""Append-only iterative provenance labels. Experimental adapter; no automatic canon updates."""
import hashlib
import json

LABELS = frozenset(("SOURCE_PRIMAIRE","RETROUVE","RECONSTRUIT",
"RAPPORTE_HISTORIQUEMENT","RELU_VERIFIE","REJOUE","PROPOSE",
"MANQUANT","CONFLIT_OUVERT","INDETERMINE","HISTORIQUE_REFUTE"))

def hash_event(value):
    raw=json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

class IterativeLabels:
    def __init__(self): self.events=[]

    def append(self, *, claim_id, label, source_ref, lineage_id, actor, reason,
               prior_hash=None, independent_review=False):
        fields=(claim_id,label,source_ref,lineage_id,actor,reason)
        if not all(isinstance(x,str) and x.strip() for x in fields):
            raise ValueError("nonempty text fields required")
        if label not in LABELS: raise ValueError("unknown label")
        history=[e for e in self.events if e["claim_id"]==claim_id]
        if prior_hash != (history[-1]["hash"] if history else None):
            raise ValueError("stale or missing previous claim hash")
        if label in ("RELU_VERIFIE","REJOUE") and (
            not independent_review or not history):
            raise ValueError("promotion needs prior record and independent review")
        event=dict(claim_id=claim_id,label=label,source_ref=source_ref,
                   lineage_id=lineage_id,actor=actor,reason=reason,
                   prior_hash=prior_hash,independent_review=independent_review,
                   iteration=len(history)+1,
                   new_lineage=lineage_id not in {e["lineage_id"] for e in history})
        event["hash"]=hash_event(event)
        self.events.append(event)
        return dict(event)

    def view(self, claim_id):
        history=[e for e in self.events if e["claim_id"]==claim_id]
        if not history: return None
        return dict(claim_id=claim_id,current_label=history[-1]["label"],
                    head=history[-1]["hash"],iterations=len(history),
                    distinct_source_lineages=len({e["lineage_id"] for e in history}),
                    contested_in_history=any(e["label"]=="CONFLIT_OUVERT" for e in history),
                    history=[dict(e) for e in history],auto_authority=False)

    def audit(self):
        heads={}
        for event in self.events:
            body={k:v for k,v in event.items() if k!="hash"}
            if hash_event(body)!=event["hash"] or event["prior_hash"]!=heads.get(event["claim_id"]):
                return False
            heads[event["claim_id"]]=event["hash"]
        return True
