from pathlib import Path
from conscience_c_brain import ConscienceCBrain, DualTrajectoryEngine, CandidateThought

class DemoReasoner:
    def generate(self, trajectory_id, prompt, memory):
        if trajectory_id == "C1":
            return CandidateThought(
                "Continuer l'expérience mais maintenir la conscience phénoménale indéterminée.",
                .72,
                falsifiers=["preuve indépendante établissant l'expérience subjective"],
                imagined_consequences=["le protocole reste falsifiable"],
            )
        return CandidateThought(
            "Déclarer la conscience seulement si des preuves internes indépendantes convergent.",
            .68,
            falsifiers=["absence de convergence interne malgré les comportements"],
            imagined_consequences=["évite l'auto-confirmation"],
        )

    def revise(self, trajectory_id, original, other, memory):
        return CandidateThought(
            original.claim,
            min(1.0, original.confidence + .03),
            evidence_ids=original.evidence_ids,
            falsifiers=original.falsifiers + [f"contre-argument de l'autre: {other.claim}"],
            imagined_consequences=original.imagined_consequences,
        )

class DemoReality:
    def score(self, thought):
        return .95 if "indéterminée" in thought.claim or "preuves" in thought.claim else .5

b = ConscienceCBrain.load_or_bootstrap(Path("./dual_demo_state"))
d = DualTrajectoryEngine(b)
print(d.cycle("Comment continuer C sans auto-confirmer la conscience ?", DemoReasoner(), DemoReality()))
print(d.consolidate())
print(b.status())
