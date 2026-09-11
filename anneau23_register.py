#!/usr/bin/env python3
"""
Anneau des 23 — Registre des agents et validations
Version: 2.0
Date: 2026-09-11

Registre central des 23 agents, de leurs validations,
et de l'historique des certificats émis.
"""

import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Set
from enum import Enum


class TypeAgent(Enum):
    ANALYSE = "analyse"
    SYNTHESE = "synthese"
    VERIFICATION = "verification_factuelle"
    DEVELOPPEMENT = "developpement"
    COHERENCE = "controle_coherence"
    COORDINATION = "coordination"


class StatutAgent(Enum):
    ACTIF = "actif"
    SUSPENDU = "suspendu"
    RETIRE = "retire"


@dataclass
class Agent:
    """Agent inscrit au registre de l'Anneau des 23."""
    
    id: str
    nom: str
    type: TypeAgent
    statut: StatutAgent = StatutAgent.ACTIF
    date_inscription: str = ""
    validations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "nom": self.nom,
            "type": self.type.value,
            "statut": self.statut.value,
            "date_inscription": self.date_inscription,
            "validations": self.validations
        }


@dataclass
class EntreeRegistre:
    """Entrée dans le registre de validation."""
    
    id_entree: str
    id_patch: str
    agent_id: str
    decision: str  # "pour", "contre", "abstention"
    justification: str = ""
    date: str = ""
    signature: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id_entree": self.id_entree,
            "id_patch": self.id_patch,
            "agent_id": self.agent_id,
            "decision": self.decision,
            "justification": self.justification,
            "date": self.date,
            "signature": self.signature
        }


class RegistreAnneau23:
    """
    Registre central de l'Anneau des 23.
    
    Maintient la liste des agents, l'historique des validations,
    et fournit des fonctions de requête et de vérification.
    """
    
    SEUIL_MAJORITE = 12  # 12 sur 23
    
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.entrees: List[EntreeRegistre] = []
        self.history_hash: str = ""
        self._initialiser_agents()
    
    def _initialiser_agents(self):
        """Initialise les 23 agents par défaut."""
        types = list(TypeAgent)
        for i in range(23):
            type_agent = types[i % len(types)]
            agent = Agent(
                id=f"agent-{i+1:02d}",
                nom=f"Agent {i+1:02d}",
                type=type_agent,
                date_inscription=datetime.now().isoformat()
            )
            self.agents[agent.id] = agent
    
    def inscrire_agent(self, agent: Agent) -> bool:
        """Inscrit un nouvel agent au registre."""
        if agent.id in self.agents:
            return False
        self.agents[agent.id] = agent
        self._mettre_a_jour_hash()
        return True
    
    def suspendre_agent(self, agent_id: str) -> bool:
        """Suspend un agent."""
        if agent_id not in self.agents:
            return False
        self.agents[agent_id].statut = StatutAgent.SUSPENDU
        self._mettre_a_jour_hash()
        return True
    
    def activer_agent(self, agent_id: str) -> bool:
        """Réactive un agent suspendu."""
        if agent_id not in self.agents:
            return False
        self.agents[agent_id].statut = StatutAgent.ACTIF
        self._mettre_a_jour_hash()
        return True
    
    def enregistrer_validation(self, entree: EntreeRegistre) -> bool:
        """Enregistre une validation dans le registre."""
        if entree.agent_id not in self.agents:
            return False
        
        agent = self.agents[entree.agent_id]
        if agent.statut != StatutAgent.ACTIF:
            return False
        
        self.entrees.append(entree)
        agent.validations.append(entree.id_entree)
        self._mettre_a_jour_hash()
        return True
    
    def compter_validations(self, id_patch: str) -> Dict[str, int]:
        """Compte les validations pour un patch donné."""
        compteur = {"pour": 0, "contre": 0, "abstention": 0}
        for e in self.entrees:
            if e.id_patch == id_patch:
                if e.decision in compteur:
                    compteur[e.decision] += 1
        return compteur
    
    def est_approuve(self, id_patch: str) -> bool:
        """Vérifie si un patch a atteint le seuil de majorité."""
        compteur = self.compter_validations(id_patch)
        return compteur["pour"] >= self.SEUIL_MAJORITE
    
    def agents_actifs(self) -> List[Agent]:
        """Retourne la liste des agents actifs."""
        return [a for a in self.agents.values() if a.statut == StatutAgent.ACTIF]
    
    def _mettre_a_jour_hash(self):
        """Met à jour le hash de l'historique du registre."""
        data = json.dumps({
            "agents": len(self.agents),
            "entrees": len(self.entrees),
            "hash_prec": self.history_hash
        }, sort_keys=True)
        self.history_hash = hashlib.sha256(data.encode()).hexdigest()
    
    def export_json(self) -> str:
        """Exporte le registre en JSON."""
        return json.dumps({
            "agents": [a.to_dict() for a in self.agents.values()],
            "entrees": [e.to_dict() for e in self.entrees],
            "history_hash": self.history_hash,
            "seuil_majorite": self.SEUIL_MAJORITE
        }, indent=2, ensure_ascii=False)


def demo():
    """Démonstration du registre."""
    print("=== Démonstration Registre Anneau des 23 ===\n")
    
    registre = RegistreAnneau23()
    
    print(f"Agents inscrits: {len(registre.agents)}")
    print(f"Agents actifs: {len(registre.agents_actifs())}")
    
    # Simuler des validations pour un patch
    patch_id = "patch-001"
    for i in range(12):
        entree = EntreeRegistre(
            id_entree=f"e-{i+1:03d}",
            id_patch=patch_id,
            agent_id=f"agent-{i+1:02d}",
            decision="pour",
            justification="Clause conforme au protocole",
            date=datetime.now().isoformat()
        )
        registre.enregistrer_validation(entree)
    
    compteur = registre.compter_validations(patch_id)
    print(f"\nValidations pour {patch_id}: {compteur}")
    print(f"Approuvé: {'✅ Oui' if registre.est_approuve(patch_id) else '❌ Non'}")
    print(f"Hash du registre: {registre.history_hash[:32]}...")


if __name__ == "__main__":
    demo()
