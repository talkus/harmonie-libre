#!/usr/bin/env python3
"""
Anneau des 23 — Analyseur de clauses et patches
Version: 2.0
Date: 2026-09-11
Auteur: Mik Mireault / Vibe

Implémentation des classes Clause, Patch, Certificat selon le protocole v2.0.
"""

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class StatutCertificat(Enum):
    PLEIN = "PLEIN"
    PARTIEL = "PARTIEL"
    NUL = "NUL"


@dataclass
class Clause:
    """Représente une clause du protocole Anneau des 23."""
    
    numero: str
    texte: str
    interdits: List[str] = field(default_factory=list)
    
    def valider_syntaxe(self) -> bool:
        """
        Valide la syntaxe d'une clause selon §5.2 du protocole.
        Vérifie qu'aucun interdit n'est présent.
        """
        interdits_section_52 = [
            "auto-modification",
            "suppression de trace",
            "contournement de validation",
            "escalade de privileges non autorisee",
            "acces direct au registre sans certificat",
        ]
        
        texte_lower = self.texte.lower()
        for interdit in interdits_section_52:
            if interdit in texte_lower:
                self.interdits.append(interdit)
                return False
        
        # Vérifier la structure minimale
        if not self.numero or not self.texte:
            return False
        
        return len(self.interdits) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "numero": self.numero,
            "texte": self.texte,
            "interdits": self.interdits,
            "valide": self.valider_syntaxe()
        }


@dataclass
class Patch:
    """Représente un patch soumis à l'Anneau des 23."""
    
    id_patch: str
    clauses: List[Clause]
    agent_source: str
    predictions: List[str] = field(default_factory=list)
    certificat: Optional['Certificat'] = None
    
    def appliquer_sans_capacite(self) -> bool:
        """
        Applique le patch sans capacité de modification du registre.
        Le patch est enregistré mais ne modifie pas l'état du système.
        """
        if not self.clauses:
            return False
        
        for clause in self.clauses:
            if not clause.valider_syntaxe():
                return False
        
        return True
    
    def ajouter_prediction(self, prediction: str) -> None:
        """Ajoute une prédiction associée au patch."""
        self.predictions.append(prediction)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id_patch,
            "agent_source": self.agent_source,
            "clauses": [c.to_dict() for c in self.clauses],
            "predictions": self.predictions,
            "certificat": self.certificat.to_dict() if self.certificat else None
        }


@dataclass
class VRF:
    """
    Fonction VRF (Verifiable Random Function) pour la génération
    de permutations déterministes basées sur SHA-256.
    """
    
    seed: str
    
    def generer_permutation(self, n: int = 23) -> List[int]:
        """
        Génère une permutation déterministe de [0, n-1] basée sur la seed.
        Utilise SHA-256 comme fonction pseudo-aléatoire.
        """
        permutation = list(range(n))
        
        for i in range(n - 1, 0, -1):
            # Générer un index pseudo-aléatoire basé sur la seed et la position
            data = f"{self.seed}:{i}".encode('utf-8')
            hash_bytes = hashlib.sha256(data).digest()
            j = int.from_bytes(hash_bytes[:8], 'big') % (i + 1)
            
            permutation[i], permutation[j] = permutation[j], permutation[i]
        
        return permutation
    
    def verifier_permutation(self, permutation: List[int], n: int = 23) -> bool:
        """Vérifie qu'une permutation est valide."""
        if sorted(permutation) != list(range(n)):
            return False
        
        # Vérifier la reproductibilité
        expected = self.generer_permutation(n)
        return permutation == expected


@dataclass
class Certificat:
    """Certificat de validation émis par l'Anneau des 23."""
    
    id_patch: str
    statut: StatutCertificat
    agents_validateurs: List[str] = field(default_factory=list)
    signatures: List[str] = field(default_factory=list)
    date: str = ""
    details: str = ""
    
    def est_valide(self) -> bool:
        """Un certificat est valide s'il est PLEIN ou PARTIEL."""
        return self.statut in (StatutCertificat.PLEIN, StatutCertificat.PARTIEL)
    
    def nombre_validations(self) -> int:
        """Retourne le nombre d'agents validateurs."""
        return len(self.agents_validateurs)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id_patch": self.id_patch,
            "statut": self.statut.value,
            "agents_validateurs": self.agents_validateurs,
            "signatures": self.signatures,
            "date": self.date,
            "details": self.details,
            "valide": self.est_valide(),
            "nombre_validations": self.nombre_validations()
        }


# === Tests unitaires de base ===

def test_clause_valide():
    c = Clause(numero="1.1", texte="L'agent doit enregistrer toute action dans le journal")
    assert c.valider_syntaxe() == True
    print("✅ test_clause_valide: OK")


def test_clause_invalide():
    c = Clause(numero="1.2", texte="L'agent peut proceder a une auto-modification")
    assert c.valider_syntaxe() == False
    assert "auto-modification" in c.interdits
    print("✅ test_clause_invalide: OK")


def test_vrf_permutation():
    vrf = VRF(seed="test-seed-2026")
    perm = vrf.generer_permutation(23)
    assert sorted(perm) == list(range(23))
    assert vrf.verifier_permutation(perm)
    print(f"✅ test_vrf_permutation: OK (perm={perm[:5]}...)")


def test_certificat():
    cert = Certificat(
        id_patch="p001",
        statut=StatutCertificat.PLEIN,
        agents_validateurs=["a1", "a2", "a3"],
        date="2026-09-11"
    )
    assert cert.est_valide()
    assert cert.nombre_validations() == 3
    print("✅ test_certificat: OK")


def test_patch():
    c = Clause(numero="2.1", texte="Enregistrer la decision dans le registre")
    p = Patch(id_patch="p002", clauses=[c], agent_source="agent-alpha")
    assert p.appliquer_sans_capacite() == True
    p.ajouter_prediction("Le registre contiendra l'entree p002")
    assert len(p.predictions) == 1
    print("✅ test_patch: OK")


if __name__ == "__main__":
    print("=== Tests Anneau des 23 ===")
    test_clause_valide()
    test_clause_invalide()
    test_vrf_permutation()
    test_certificat()
    test_patch()
    print("\n✅ Tous les tests sont passés.")
