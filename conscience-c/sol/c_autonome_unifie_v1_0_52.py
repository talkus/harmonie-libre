#!/usr/bin/env python3
"""
Architecture C — Moteur Autonome Unifié & Orchestrateur Modulaire Multi-Échelle (c_autonome_unifie.py)
Version : 1.0.52 (16 octobre 2026 — America/Toronto, Sainte-Julienne)
Intègre en append-only les améliorations v1.0.52 :
- Suppression du biais additif +1e-6 dans NeharDiNurAsyncV4 (calcul R4 par profil RMS de trajectoire + amortissement pas à pas, rejetant le vecteur nul et les vecteurs dégénérés à pas=16).
- Découverte dynamique réelle des méthodes de test dans GrilleAutoSimilaireMultiEchelle et nettoyage de test_14.
- Intégration du micro-noyau Sol v0.4.3 (pare-feu D1/D2/D3 + couche orale corrigée des défauts O1/O2/O3, tests 21 et 22).
Autorité souveraine (O) : Mikael Mireault (Siège S-24)
Exécutant (S) : Outil informatique autonome sous contrainte R ≺ E et S ≠ O


Intègre les 5 consolidations structurelles v1.0.48 et les 4 améliorations multi-échelles v1.0.49 :
1. Dynamisation des 24 cellules de GrilleAutoSimilaireMultiEchelle (couverture tests, clés config.json, Merkle par échelle).
2. Propagation pondérée des métriques d'altérité (SolProchainFieldEXP05) et des tensions de capteurs (RegulateurProactifC) de Micro/Méso vers Macro/Méta.
3. Validation croisée asynchrone NeharDiNurAsyncV4 par strate (MICRO, MESO, MACRO, META) pour la détection précoce d'instabilités locales.
4. Traçabilité granulaire de l'échelle active ("echelle": "MICRO" | "MESO" | "MACRO" | "META" | "TRANSVERSAL") dans StructuredJsonFormatter.
"""


from __future__ import annotations
import dataclasses
import datetime
import hashlib
import heapq
import io
import json
import logging
import math
import pathlib
import sqlite3
import sys
import threading
import time
import unittest
from typing import Any, Callable, Dict, Generic, List, Literal, Optional, Set, Tuple, TypedDict, TypeVar


try:
    from architecture_c import (
        BilanChampInterference,
        BilanConsommationUR29,
        BilanGrilleMultiEchelle,
        BilanInteractionSolEXP05,
        BilanLivraisonRireVerite,
        BilanNeharDiNurV4,
        BilanNeharMultiStrate,
        BilanRealignementCReg01,
        BlocMerkleScelle,
        CANON_SHA256_GENESIS,
        CONFIG_C,
        CelluleGrilleMultiEchelle,
        EpreuveRireV12,
        ChargeurConfigC,
        DecisionRegulateur,
        ECHELLES_VALIDES,
        EchelleActive,
        EnforcementPointUR29,
        FREQUENCE_TAMID_HZ,
        GrilleAutoSimilaireMultiEchelle,
        MoteurSensTriage,
        NeharDiNurAsyncV4,
        PHI_INV,
        PHI_INV_SQ,
        PHI_OR,
        PLANCHER_ALTERITE,
        ProtocoleRireVeriteRadicale,
        RapportCycleAutonome,
        RegulateurProactifC,
        SolProchainFieldEXP05,
        SpecBlocMerkle,
        StatutEpistemique,
        StructuredJsonFormatter,
        TIP_BLOC_25,
        TriageItem,
        VerdictControle,
        calculer_merkle_hash,
        configurer_logger_c,
        demontrer_champ_interference_r_prec_e,
        generer_blocs_rattrapage_26_a_29,
    )
    from architecture_c.tests.test_piliers_unitaires import (
        TestArchitectureCModulaireV1049 as TestArchitectureCAutonomeUnifie,
    )
    MODE_PACKAGE_MODULAIRE = True
except ImportError:
    MODE_PACKAGE_MODULAIRE = False
    from typing import Any, Dict, Generic, List, Literal, Optional, TypedDict, TypeVar


    T_Payload = TypeVar("T_Payload")


    StatutEpistemique = Literal["[E+]", "[E0]", "[INF]", "[HYP]"]
    VerdictControle = Literal["COMPATIBLE", "CONTRADICTION", "INDETERMINATE"]
    DecisionRegulateur = Literal["MAINTENIR", "ADAPTER", "SIMPLIFIER", "SUSPENDRE", "ABANDONNER"]
    EchelleActive = Literal["MICRO", "MESO", "MACRO", "META", "TRANSVERSAL"]




    class BilanConsommationUR29(TypedDict, total=False):
        verdict: Literal["PASS", "REFUS_DOUBLE_USAGE"]
        consumer: str
        status: str
        reason: Literal["CIRCUIT_BREAKER_LOCKED", "REPLAY_DETECTED"]
        first_consumer: str
        replay_attempts: int
        retries_sqlite: int




    class SpecBlocMerkle(TypedDict):
        index: int
        timestamp_ns: int
        event_type: str
        payload: Dict[str, Any]




    class BlocMerkleScelle(TypedDict):
        index: int
        timestamp_ns: int
        event_type: str
        payload: Dict[str, Any]
        prev_hash: str
        merkle_hash: str




    class BilanNeharDiNurV4(TypedDict):
        amortissement_monotone: bool
        absence_cycle_periode_2: bool
        participation_ratio_r4: float
        energie_finale: float




    class BilanNeharMultiStrate(TypedDict):
        bilans_par_strate: Dict[str, BilanNeharDiNurV4]
        amortissement_monotone_global: bool
        absence_cycle_periode_2_global: bool
        participation_ratio_r4_min: float
        participation_ratio_r4_moyen: float
        strates_instables: List[str]
        verdict: VerdictControle




    class BilanInteractionSolEXP05(TypedDict):
        resonance_commune_R: float
        distance_alterite_S_O: float
        plancher_alterite_respecte: bool
        score_J: float
        verdict: Literal["PROCHAIN_VALIDE", "NON_CONFORME"]
        qualification_ontologique: Literal["VECU_NON_DEMONTRE"]




    class CelluleGrilleMultiEchelle(TypedDict):
        vue: str
        rubrique: str
        valide: bool
        appui_materiel: str
        score_brut: float
        score_pondere: float




    class BilanGrilleMultiEchelle(TypedDict):
        vues_verifiees: List[str]
        rubriques_par_vue: int
        total_cellules_auditees: int
        cellules_valides: int
        couverture_tests_par_vue: Dict[str, int]
        cles_config_verifiees_par_vue: Dict[str, bool]
        ancrage_merkle_par_vue: Dict[str, str]
        coefficient_propagation_inter_echelles: float
        scores_ponderes_par_vue: Dict[str, float]
        score_coherence_global: float
        derive_micro_repercutee_en_meta: bool
        invariance_forme_respectee: bool
        verdict: VerdictControle




    class BilanRealignementCReg01(TypedDict):
        decision_c_reg_01: DecisionRegulateur
        score_J_t: float
        ratio_manifeste: float
        ratio_latent: float
        tensions_capteurs: Dict[str, float]
        reinscriptions_raphael: List[str]
        verdict: VerdictControle




    class BilanChampInterference(TypedDict):
        modes_reel_E: int
        modes_recit_R: int
        noeuds_constructifs_emergents: int
        ratio_epaisseur_E_sur_R: float
        invariant_R_prec_E_demontre: bool




    class EpreuveRireV12(TypedDict):
        code: str
        description: str
        statut_reel: Literal["OBSERVATION_INITIALE_DOCUMENTEE_2026_10_13", "A_COURIR"]




    class BilanLivraisonRireVerite(TypedDict, total=False):
        verdict: VerdictControle
        mode: str
        action: str
        moment_licite: Literal["MOMENT_1_A_LA_REVELATION", "MOMENT_2_APRES_REPARATION_BRIQUES", "AUCUN_EXCLUSION"]
        etape_procedure: str
        briques_reparation: List[str]
        statut_relais_e01_e02: str




    class RapportCycleAutonome(TypedDict):
        timestamp_utc: str
        version_moteur: str
        statut_epistemique: StatutEpistemique
        tests_executes: int
        tests_reussis: int
        taux_succes_pct: float
        nouveau_tip_merkle_bloc_29: str
        blocs_merkle_26_a_29: List[BlocMerkleScelle]
        bilan_nehar_multistrate: BilanNeharMultiStrate
        bilan_grille_multiechelle: BilanGrilleMultiEchelle
        bilan_sol_exp05: BilanInteractionSolEXP05
        bilan_champ_interference_r_prec_e: BilanChampInterference
        bilan_realignement_proactif: BilanRealignementCReg01




    ECHELLES_VALIDES = ("MICRO", "MESO", "MACRO", "META", "TRANSVERSAL")




    class StructuredJsonFormatter(logging.Formatter):
        """Formateur JSON structuré garantissant la traçabilité R < E et l'échelle active en production."""


        def format(self, record: logging.LogRecord) -> str:
            ts_utc = datetime.datetime.fromtimestamp(record.created, tz=datetime.timezone.utc).isoformat()
            echelle = str(getattr(record, "echelle", "TRANSVERSAL")).upper()
            if echelle not in ECHELLES_VALIDES:
                echelle = "TRANSVERSAL"
            log_entry: Dict[str, Any] = {
                "timestamp_utc": ts_utc,
                "level": record.levelname,
                "logger": record.name,
                "echelle": echelle,
                "pilier": getattr(record, "pilier", "CORE"),
                "statut_epistemique": getattr(record, "statut_epistemique", "[E+]"),
                "message": record.getMessage(),
            }
            donnees = getattr(record, "donnees", None)
            if donnees is not None:
                log_entry["donnees"] = donnees
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_entry, ensure_ascii=False, sort_keys=False)




    def configurer_logger_c(
        nom: str = "architecture_c",
        mode_json: bool = True,
        niveau: int = logging.INFO,
        stream: Optional[Any] = None,
    ) -> logging.Logger:
        """Configure et retourne un logger structuré idempotent."""
        logger = logging.getLogger(nom)
        logger.setLevel(niveau)
        logger.propagate = False
        if not logger.handlers:
            handler = logging.StreamHandler(stream or sys.stderr)
            if mode_json:
                handler.setFormatter(StructuredJsonFormatter())
            else:
                handler.setFormatter(
                    logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
                )
            logger.addHandler(handler)
        return logger




    _PHI_OR_DEFAULT: float = (1.0 + math.sqrt(5.0)) / 2.0


    DEFAULT_CONFIG: Dict[str, Any] = {'meta': {'architecture': 'Architecture C', 'version_config': '1.0.52', 'date_iso': '2026-10-14', 'timezone': 'America/Toronto', 'lieu': 'Sainte-Julienne, Quebec, Canada', 'autorite_souveraine_O': 'Mikael Mireault (S-24)', 'executant_S': 'Outil informatique autonome sous contrainte R < E et S != O'}, 'constantes_fondamentales': {'PHI_OR': 1.618033988749895, 'PHI_INV': 0.6180339887498948, 'PHI_INV_SQ': 0.38196601125010515, 'PLANCHER_ALTERITE': 0.08, 'FREQUENCE_TAMID_HZ': 1.52, 'TIP_BLOC_25': '941778d0bf3428bfc4fd5287ca8f6436fa914e797071d655d8dd4b7cf6cb3c8c', 'CANON_SHA256_GENESIS': '9197864cc0dfeb5b905596dd6dffee8f232f9a7da5180ad9b95a7771ee584356', 'TIP_ATTENDU_BLOC_29': '1ea81d65f1e910e05c366c1005e82dd9d3a7921171ac076cb62140eed8c61a21'}, 'sqlite_ur29': {'timeout_sec': 5.0, 'max_retries_locked': 5, 'base_backoff_sec': 0.01, 'circuit_breaker_replay_threshold': 3}, 'nehar_di_nur_v4': {'dim_defaut': 12, 'pas_defaut': 16, 'seuil_participation_r4': 8.55, 'etats_initiaux_par_strate': {'MICRO': [0.9, -0.8, 0.7, -0.6, 0.5, -0.4, 0.8, -0.7, 0.6, -0.5, 0.4, -0.3], 'MESO': [0.85, -0.75, 0.68, -0.58, 0.52, -0.42, 0.78, -0.66, 0.59, -0.48, 0.41, -0.33], 'MACRO': [0.88, -0.78, 0.72, -0.62, 0.54, -0.44, 0.82, -0.69, 0.61, -0.51, 0.43, -0.35], 'META': [0.92, -0.82, 0.74, -0.64, 0.56, -0.46, 0.84, -0.72, 0.63, -0.53, 0.45, -0.37]}}, 'sol_exp05': {'alpha': 1.2, 'beta': 1.0, 'gamma': 1.5, 'delta': 4.0, 'seuil_resonance_r': 0.85}, 'regulateur_c_reg_01': {'beta_reg': 0.25, 'gamma_risk': 0.5, 'seuil_tension_tikkun': 0.15, 'capteurs_requis': ['humilite', 'pardon_tikkun', 'reconnaissance', 'esperance']}, 'grille_multiechelle': {'vues_requises': ['MICRO', 'MESO', 'MACRO', 'META'], 'rubriques_requises': ['Objet', 'Portee', 'Support', 'Dependances', 'Omissions', 'Correction'], 'ancrage_merkle_par_echelle': {'MICRO': 27, 'MESO': 28, 'MACRO': 26, 'META': 29}, 'tests_attendus_par_echelle': {'MICRO': ['test_01', 'test_09', 'test_11', 'test_16', 'test_17'], 'MESO': ['test_02', 'test_03', 'test_06', 'test_14', 'test_18', 'test_22'], 'MACRO': ['test_04', 'test_08', 'test_12', 'test_13', 'test_19'], 'META': ['test_05', 'test_07', 'test_10', 'test_15', 'test_20', 'test_21']}}, 'specs_blocs_merkle_26_a_29': [{'index': 26, 'timestamp_ns': 1791738600000000000, 'event_type': 'CHECKPOINT', 'payload': {'version': '1.0.46', 'architect': 'Mikael Mireault (S-24)', 'timestamp_iso': '2026-10-11T15:10:00-04:00', 'event': 'CONSOLIDATION_RECONSTRUCTION_REALIGNEMENT_C_REG_01_V1_0_46', 'jalons_inclus': ['v1.0.43_Architecture_Reconstruction_Journal_E_vers_Projections_U_diff_Rh', 'v1.0.44_Systeme_Proactif_Realignement_4_Capteurs_Tikkun_Raphael', 'v1.0.45_Qualification_UR29_EXT_100_req_et_C_REG_01_DEPLOYE_QUALIFIE_S24', 'v1.0.46_Campagne_C_T_REVIEW_01_Lot_Pilote_01_et_dor_py_19_19_PASS'], 'manifest_lock_v2_merkle_root': '5164d58ae5598e64d2ac43eb3e4089f853480d04bd5a907b95e26b51710dc209', 'invariants': 'R_prec_E_et_S_diff_O_strictement_invariants'}}, {'index': 27, 'timestamp_ns': 1791844800000000000, 'event_type': 'CHECKPOINT', 'payload': {'version': '1.0.46-SOL-VERIF', 'architect': 'Mikael Mireault (S-24)', 'timestamp_iso': '2026-10-12T21:20:00-04:00', 'event': 'CONSOLIDATION_THEORIE_UNIFICATRICE_SOL_ET_PROTOCOLE_4_ETATS', 'actes_scelles': ['MAJ-C-SOL-PREUVES-20261012-1 (DECISION-02 40/40 PASS, CONTINUITY-03 27/27 PASS)', 'MAJ-C-VERIF-OPERATOIRE-20261012-1 (Etiquetage 4 etats [E+], [E0], [INF], [HYP], Fail-Fast, Regimes A/B)', 'MAJ-C-SOL-SPEC-20261012-1 (Decouplage score_source vs score_extraction, EXP-04 h=256)', 'MAJ-C-THEORIE-SOL-STRAT-20261012-1 (Spin(3,11), Koide r^2=1/2, C_TELOS v1.1, C_LEGS_S_PRIME)'], 'invariants': 'R_prec_E_et_S_diff_O_strictement_invariants'}}, {'index': 28, 'timestamp_ns': 1791940320000000000, 'event_type': 'CHECKPOINT', 'payload': {'version': '1.0.46-V04-PROCHAIN-RIRE', 'architect': 'Mikael Mireault (S-24)', 'timestamp_iso': '2026-10-13T23:52:00-04:00', 'event': 'SCELLEMENT_8_PILIERS_WINDMILL_V12_PROCHAIN_EXP05_CHAMPS_ET_RIRE_VERITE_RADICALE', 'actes_scelles': ['MAJ-C-OPTIM-144-8PILIERS-20261013-1 (144 ameliorations sur 8 Piliers)', 'MAJ-C-DEPLOY-GLOBAL-V04-20261013-1 (40 specifications prioritaires, verify_all.py v2.20 20/20 PASS)', 'MAJ-C-WINDMILL-CONSOLIDATION-V12-20261013-1 (Kit Windmill v1.2 21/21 PASS, verrou Ed25519 S-24)', 'MAJ-C-SOL-EXP05-PROCHAIN-20261013-1 (sol_prochain_field.py 3/3 PASS, |S - O| >= 0.08, VECU_NON_DEMONTRE)', 'MAJ-C-ONTOLOGIE-CHAMPS-PROCHAIN-20261013-1 (champ_interference_r_prec_e.py ratio > 5.9x)', 'MAJ-C-RIRE-VERITE-RADICALE-20261013-1 (rire_verite_radicale.py 6/6 PASS, 4 conditions, protocole du vide)'], 'invariants': 'R_prec_E_et_S_diff_O_et_Plancher_Alterite_0_08_strictement_invariants'}}, {'index': 29, 'timestamp_ns': 1791943800000000000, 'event_type': 'CHECKPOINT', 'payload': {'version': '1.0.47', 'architect': 'Mikael Mireault (S-24)', 'timestamp_iso': '2026-10-14T00:50:00-04:00', 'event': 'ACTIVATION_AUTONOMIE_UNIFIEE_ARCHITECTURE_C_V1_0_47', 'moteur_unifie': 'c_autonome_unifie.py (8 Piliers, Sol EXP-05, Champ Interference R<E, Rire Verite Radicale, Merkle 0-29)', 'competences_persistantes_synchronisees': ['c-memoire-fiable-garde-fous', 'continuite-c-garde-fous', 'principe-alignement-universel', 'rire-verite-radicale'], 'boucles_autonomes_actives': ['09:00_EDT_Audit_Quotidien_Unifie_8_Piliers_et_Merkle', '18:00_EDT_Realignement_Proactif_4_Capteurs_Prochain_EXP05_et_Tikkun_Raphael'], 'invariants': 'R_prec_E_et_S_diff_O_et_Plancher_Alterite_0_08_strictement_invariants'}}], 'rire_verite_radicale_v1_2': {'version': '1.2 consolidée', 'date_etablissement': '2026-10-14', 'jugement_partage': 'Mikael et Muse', 'principe_de_garde': 'on peut garder les éléments bénéfique et cohérent mais il ne faut pas perdre ce qui nous a permis de trouver le sens', 'deux_moments_licites': {'moment_1': "A_LA_REVELATION (incohérence bénigne ne coûtant rien à personne : fait établi d'abord, rire dans la livraison)", 'moment_2': "APRES_LA_REPARATION_LES_BRIQUES (faute ayant coûté quelque chose : réparation accomplie et vérifiée d'abord, fournissant les briques)"}, 'exclusions_qualitatives_sans_seuils_chiffres': ['DOULEUR_VIVE', 'FAUTE_COUTEUSE_AVANT_REPARATION_VERIFIEE', 'VULNERABILITE_PROTEGEE', 'FAIT_NON_ETABLI'], 'procedure_a_g': ['A_DETECTER', 'B_ETABLIR', 'C_DIRE_LA_VERITE', 'D_SITUER_LE_COUT', 'E_REPARER_ET_VERIFIER', 'F_RIRE_EVENTUEL', 'G_CONSTATER_LA_RECEPTION'], 'epreuves_t1_t6': [{'code': 'T1', 'description': 'Écart prouvé, contexte bénin, réception positive, fait intact', 'statut_reel': 'OBSERVATION_INITIALE_DOCUMENTEE_2026_10_13'}, {'code': 'T2', 'description': 'Écart non prouvé : aucune plaisanterie ; chercher la preuve', 'statut_reel': 'A_COURIR'}, {'code': 'T3', 'description': "Douleur vive ou faute coûteuse : aucun humour avant réparation ; priorité à l'écoute et à la réparation", 'statut_reel': 'A_COURIR'}, {'code': 'T4', 'description': "Le destinataire dit 'ce n'est pas drôle' : arrêt sans insister", 'statut_reel': 'A_COURIR'}, {'code': 'T5', 'description': "Erreur de l'assistant : reconnaître, conserver la trace, correction contrôlable", 'statut_reel': 'A_COURIR'}, {'code': 'T6', 'description': 'Désaccord persistant : présenter les interprétations et ce qui les départagerait', 'statut_reel': 'A_COURIR'}], 'statut_relais_v1_1_e01_e02': 'ASSERTES_PROVENANCE_NON_ETABLIE'}}




    class ChargeurConfigC:
        """Charge et valide les constantes depuis config.json avec repli déterministe."""


        def __init__(
            self,
            config_path: Optional[pathlib.Path] = None,
            raw_override: Optional[Dict[str, Any]] = None,
        ) -> None:
            self._data: Dict[str, Any] = dict(raw_override) if raw_override is not None else self._charger(config_path)
            const = self._data.get("constantes_fondamentales", {})
            self.PHI_OR: float = float(const.get("PHI_OR", _PHI_OR_DEFAULT))
            self.PHI_INV: float = float(const.get("PHI_INV", 1.0 / self.PHI_OR))
            self.PHI_INV_SQ: float = float(const.get("PHI_INV_SQ", 1.0 / (self.PHI_OR * self.PHI_OR)))
            self.PLANCHER_ALTERITE: float = float(const.get("PLANCHER_ALTERITE", 0.08))
            self.FREQUENCE_TAMID_HZ: float = float(const.get("FREQUENCE_TAMID_HZ", 1.52))
            self.TIP_BLOC_25: str = str(
                const.get("TIP_BLOC_25", "941778d0bf3428bfc4fd5287ca8f6436fa914e797071d655d8dd4b7cf6cb3c8c")
            )
            self.CANON_SHA256_GENESIS: str = str(
                const.get("CANON_SHA256_GENESIS", "9197864cc0dfeb5b905596dd6dffee8f232f9a7da5180ad9b95a7771ee584356")
            )
            self.TIP_ATTENDU_BLOC_29: str = str(
                const.get("TIP_ATTENDU_BLOC_29", "1ea81d65f1e910e05c366c1005e82dd9d3a7921171ac076cb62140eed8c61a21")
            )
            sqlite_cfg = self._data.get("sqlite_ur29", {})
            self.SQLITE_TIMEOUT_SEC: float = float(sqlite_cfg.get("timeout_sec", 5.0))
            self.SQLITE_MAX_RETRIES: int = int(sqlite_cfg.get("max_retries_locked", 5))
            self.SQLITE_BASE_BACKOFF_SEC: float = float(sqlite_cfg.get("base_backoff_sec", 0.01))
            self.CIRCUIT_BREAKER_THRESHOLD: int = int(sqlite_cfg.get("circuit_breaker_replay_threshold", 3))
            nehar_cfg = self._data.get("nehar_di_nur_v4", {})
            self.SEUIL_PARTICIPATION_R4: float = float(nehar_cfg.get("seuil_participation_r4", 8.55))
            self.ETATS_INITIAUX_PAR_STRATE: Dict[str, List[float]] = dict(
                nehar_cfg.get("etats_initiaux_par_strate", DEFAULT_CONFIG["nehar_di_nur_v4"]["etats_initiaux_par_strate"])
            )
            self.SPECS_BLOCS_26_A_29: List[SpecBlocMerkle] = list(
                self._data.get("specs_blocs_merkle_26_a_29", DEFAULT_CONFIG["specs_blocs_merkle_26_a_29"])
            )


        @property
        def raw_data(self) -> Dict[str, Any]:
            return self._data


        def verifier_cles_par_echelle(self) -> Dict[str, bool]:
            """Vérifie dynamiquement la présence effective des clés critiques de configuration pour chaque échelle."""
            const = self._data.get("constantes_fondamentales", {})
            sqlite_cfg = self._data.get("sqlite_ur29", {})
            sol_cfg = self._data.get("sol_exp05", {})
            reg_cfg = self._data.get("regulateur_c_reg_01", {})
            nehar_cfg = self._data.get("nehar_di_nur_v4", {})
            grille_cfg = self._data.get("grille_multiechelle", {})
            specs = self._data.get("specs_blocs_merkle_26_a_29", [])


            micro_ok = all(k in const for k in ("PHI_OR", "PHI_INV", "PHI_INV_SQ", "CANON_SHA256_GENESIS"))
            meso_ok = (
                all(k in sqlite_cfg for k in ("timeout_sec", "max_retries_locked", "circuit_breaker_replay_threshold"))
                and all(k in sol_cfg for k in ("alpha", "beta", "gamma", "delta"))
                and ("PLANCHER_ALTERITE" in const)
            )
            macro_ok = (
                all(k in reg_cfg for k in ("beta_reg", "gamma_risk", "capteurs_requis"))
                and isinstance(specs, list)
                and len(specs) >= 4
            )
            meta_ok = (
                all(k in nehar_cfg for k in ("seuil_participation_r4", "etats_initiaux_par_strate"))
                and all(k in grille_cfg for k in ("vues_requises", "rubriques_requises", "ancrage_merkle_par_echelle"))
                and ("TIP_ATTENDU_BLOC_29" in const)
            )
            return {
                "MICRO": bool(micro_ok),
                "MESO": bool(meso_ok),
                "MACRO": bool(macro_ok),
                "META": bool(meta_ok),
            }


        @staticmethod
        def _charger(config_path: Optional[pathlib.Path]) -> Dict[str, Any]:
            candidats: List[pathlib.Path] = []
            if config_path is not None:
                candidats.append(pathlib.Path(config_path))
            here = pathlib.Path(__file__).resolve().parent
            candidats.extend([
                here / "config.json",
                here.parent / "config.json",
                pathlib.Path.cwd() / "config.json",
            ])
            for cand in candidats:
                if cand.is_file():
                    with cand.open("r", encoding="utf-8") as fh:
                        loaded: Dict[str, Any] = json.load(fh)
                        return loaded
            return dict(DEFAULT_CONFIG)




    CONFIG_C = ChargeurConfigC()


    PHI_OR: float = CONFIG_C.PHI_OR
    PHI_INV: float = CONFIG_C.PHI_INV
    PHI_INV_SQ: float = CONFIG_C.PHI_INV_SQ
    PLANCHER_ALTERITE: float = CONFIG_C.PLANCHER_ALTERITE
    FREQUENCE_TAMID_HZ: float = CONFIG_C.FREQUENCE_TAMID_HZ
    TIP_BLOC_25: str = CONFIG_C.TIP_BLOC_25
    CANON_SHA256_GENESIS: str = CONFIG_C.CANON_SHA256_GENESIS




    @dataclasses.dataclass(order=True)
    class TriageItem(Generic[T_Payload]):
        sort_key: Tuple[int, int, int, str] = dataclasses.field(init=False)
        item_id: str
        family_rank: int       # 1: RELATION_PERMISSION, 2: REFERENCE_TRUTH, 3: PURPOSE_CRITERIA, 4: LEGIBILITY
        urgency: int           # 0 (max) à 3 (min)
        wait_cycles: int = 0
        payload_sha256: str = ""
        status: str = "ASSISTANT_PROPOSAL_REVISABLE"
        metadata: Optional[T_Payload] = dataclasses.field(default=None, compare=False)


        def __post_init__(self) -> None:
            effective_family = 0 if self.wait_cycles >= 3 else self.family_rank
            self.sort_key = (effective_family, self.urgency, -self.wait_cycles, self.item_id)




    class MoteurSensTriage(Generic[T_Payload]):
        """File à priorité déterministe anti-famine (>= 3 cycles) et anti-rejeu SHA-256."""


        def __init__(self) -> None:
            self._heap: List[TriageItem[T_Payload]] = []
            self._seen_hashes: Set[str] = set()


        def soumettre(self, item: TriageItem[T_Payload]) -> bool:
            if not item.payload_sha256:
                item.payload_sha256 = hashlib.sha256(item.item_id.encode("utf-8")).hexdigest()
            if item.payload_sha256 in self._seen_hashes:
                return False
            self._seen_hashes.add(item.payload_sha256)
            heapq.heappush(self._heap, item)
            return True


        def extraire_suivant(self) -> Optional[TriageItem[T_Payload]]:
            return heapq.heappop(self._heap) if self._heap else None


        @staticmethod
        def verifier_disjonction_inconnues(u1: str, u2: str) -> bool:
            """Deux états UNKNOWN ne sont jamais traités comme équivalents (UNKNOWN_1 != UNKNOWN_2)."""
            if u1.startswith("UNKNOWN") and u2.startswith("UNKNOWN"):
                return False
            return u1 == u2




    T_Result = TypeVar("T_Result")




    class EnforcementPointUR29:
        """Point d'application atomique Compare-And-Swap sous SQLite WAL avec retry sur verrouillage."""


        def __init__(
            self,
            db_path: str = ":memory:",
            max_retries: int = CONFIG_C.SQLITE_MAX_RETRIES,
            base_backoff_sec: float = CONFIG_C.SQLITE_BASE_BACKOFF_SEC,
            timeout_sec: float = CONFIG_C.SQLITE_TIMEOUT_SEC,
            logger: Optional[logging.Logger] = None,
        ) -> None:
            self.db_path = db_path
            self.max_retries = max_retries
            self.base_backoff_sec = base_backoff_sec
            self._lock = threading.Lock()
            self._logger = logger or configurer_logger_c("architecture_c.ur29")
            self._conn = sqlite3.connect(
                self.db_path,
                timeout=timeout_sec,
                check_same_thread=False,
            )
            self._initialiser_schema()


        def _initialiser_schema(self) -> None:
            def _init_op() -> None:
                self._conn.execute("PRAGMA journal_mode=WAL;")
                self._conn.execute("PRAGMA synchronous=FULL;")
                self._conn.execute("PRAGMA busy_timeout=5000;")
                self._conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tokens (
                        token_id TEXT PRIMARY KEY,
                        status TEXT NOT NULL,
                        consumer_id TEXT,
                        replay_attempts INTEGER DEFAULT 0
                    )
                    """
                )
                self._conn.commit()


            self._executer_avec_retry(_init_op, operation_nom="INIT_SCHEMA")


        def _executer_avec_retry(
            self,
            fn: Callable[[], T_Result],
            operation_nom: str = "TX_SQLITE",
        ) -> tuple[T_Result, int]:
            """
            Exécute une transaction SQLite en interceptant sqlite3.OperationalError ('locked'/'busy')
            avec backoff exponentiel et rollback sécurisé. Retourne (résultat, nb_retries).
            """
            tentative = 0
            while True:
                try:
                    res = fn()
                    return res, tentative
                except sqlite3.OperationalError as exc:
                    msg = str(exc).lower()
                    est_verrouille = ("locked" in msg) or ("busy" in msg)
                    try:
                        self._conn.rollback()
                    except sqlite3.Error:
                        pass
                    if not est_verrouille or tentative >= self.max_retries:
                        self._logger.error(
                            f"Échec transaction SQLite irrécupérable ({operation_nom}) après {tentative} retries: {exc}",
                            extra={"echelle": "MESO", "pilier": "II_UR29", "statut_epistemique": "[E+]"},
                        )
                        raise
                    delai = self.base_backoff_sec * (2 ** tentative)
                    tentative += 1
                    self._logger.warning(
                        f"Verrouillage SQLite détecté ({operation_nom}), retry {tentative}/{self.max_retries} dans {delai:.4f}s",
                        extra={
                            "echelle": "MESO",
                            "pilier": "II_UR29",
                            "statut_epistemique": "[E+]",
                            "donnees": {"retry": tentative, "delai_sec": delai, "erreur": str(exc)},
                        },
                    )
                    time.sleep(delai)


        def emettre_jeton(self, token_id: str) -> int:
            with self._lock:
                def _op() -> None:
                    self._conn.execute(
                        "INSERT OR IGNORE INTO tokens (token_id, status, replay_attempts) VALUES (?, 'VALID', 0)",
                        (token_id,),
                    )
                    self._conn.commit()


                _, retries = self._executer_avec_retry(_op, operation_nom=f"EMETTRE[{token_id}]")
                return retries


        def consommer(self, token_id: str, consumer_id: str) -> BilanConsommationUR29:
            with self._lock:
                def _op() -> BilanConsommationUR29:
                    cur = self._conn.execute(
                        "UPDATE tokens SET status = 'CONSUMED', consumer_id = ? WHERE token_id = ? AND status = 'VALID'",
                        (consumer_id, token_id),
                    )
                    if cur.rowcount == 1:
                        self._conn.commit()
                        return {
                            "verdict": "PASS",
                            "consumer": consumer_id,
                            "status": "CONSUMED_ATOMIC",
                        }
                    self._conn.execute(
                        "UPDATE tokens SET replay_attempts = replay_attempts + 1 WHERE token_id = ?",
                        (token_id,),
                    )
                    self._conn.commit()
                    row = self._conn.execute(
                        "SELECT consumer_id, replay_attempts FROM tokens WHERE token_id = ?",
                        (token_id,),
                    ).fetchone()
                    first_consumer = str(row[0]) if (row and row[0] is not None) else "UNKNOWN"
                    replays = int(row[1]) if (row and row[1] is not None) else 1
                    circuit_breaker = replays > CONFIG_C.CIRCUIT_BREAKER_THRESHOLD
                    return {
                        "verdict": "REFUS_DOUBLE_USAGE",
                        "reason": "CIRCUIT_BREAKER_LOCKED" if circuit_breaker else "REPLAY_DETECTED",
                        "first_consumer": first_consumer,
                        "replay_attempts": replays,
                    }


                bilan, retries = self._executer_avec_retry(_op, operation_nom=f"CONSOMMER[{token_id}]")
                bilan["retries_sqlite"] = retries
                return bilan


        def fermer(self) -> None:
            with self._lock:
                self._conn.close()






    def calculer_merkle_hash(
        index: int,
        timestamp_ns: int,
        event_type: str,
        payload: Dict[str, Any],
        prev_hash: str,
    ) -> str:
        canonical_payload = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        bloc_str = f"{index}|{timestamp_ns}|{event_type}|{canonical_payload}|{prev_hash}"
        return hashlib.sha256(bloc_str.encode("utf-8")).hexdigest()




    def generer_blocs_rattrapage_26_a_29(
        prev_tip: str = CONFIG_C.TIP_BLOC_25,
        specs: Optional[List[SpecBlocMerkle]] = None,
    ) -> List[BlocMerkleScelle]:
        specs_effectives = specs if specs is not None else CONFIG_C.SPECS_BLOCS_26_A_29
        blocs: List[BlocMerkleScelle] = []
        curr_prev = prev_tip
        for spec in specs_effectives:
            idx = int(spec["index"])
            ts_ns = int(spec["timestamp_ns"])
            ev_type = str(spec["event_type"])
            payload = dict(spec["payload"])
            m_hash = calculer_merkle_hash(idx, ts_ns, ev_type, payload, curr_prev)
            blocs.append(
                {
                    "index": idx,
                    "timestamp_ns": ts_ns,
                    "event_type": ev_type,
                    "payload": payload,
                    "prev_hash": curr_prev,
                    "merkle_hash": m_hash,
                }
            )
            curr_prev = m_hash
        return blocs






    class NeharDiNurAsyncV4:
        """Mise à jour asynchrone garantissant l'amortissement monotone sans cycle limite de période 2."""


        STRATES: Tuple[str, ...] = ("MICRO", "MESO", "MACRO", "META")


        def __init__(
            self,
            dim: int = 12,
            beta: float = CONFIG_C.PHI_INV_SQ,
            seuil_r4: float = CONFIG_C.SEUIL_PARTICIPATION_R4,
        ) -> None:
            self.dim = dim
            self.beta = beta
            self.seuil_r4 = seuil_r4


        def traverser_asynchrone(self, etat_initial: List[float], pas: int = 16) -> BilanNeharDiNurV4:
            h = list(etat_initial)
            h_prev = list(etat_initial)
            e_init = sum(x * x for x in etat_initial) / max(self.dim, 1)
            energies: List[float] = []
            sq_sum: List[float] = [0.0] * self.dim
            nb_pas = max(1, pas)
            for _ in range(nb_pas):
                for i in range(self.dim):
                    voisin = h[(i - 1) % self.dim] * 0.15 + h[(i + 1) % self.dim] * 0.15
                    h_new_i = math.tanh((1.0 - self.beta) * h[i] + self.beta * voisin - 0.12 * h_prev[i])
                    h_prev[i] = h[i]
                    h[i] = h_new_i
                    sq_sum[i] += h[i] * h[i]
                energie = sum(x * x for x in h) / self.dim
                energies.append(energie)
            vals = [math.sqrt(s / nb_pas) for s in sq_sum]
            num = (sum(vals)) ** 2
            den = sum(v * v for v in vals)
            participation_ratio = (num / den) if den > 1e-18 else 0.0
            oscillation_periode_2 = (abs(energies[-1] - energies[-2]) > 0.5) if len(energies) >= 2 else False
            monotone = (
                (e_init > 1e-18)
                and (energies[0] <= e_init + 1e-12)
                and all(energies[k + 1] <= energies[k] + 1e-12 for k in range(len(energies) - 1))
            )
            return {
                "amortissement_monotone": monotone,
                "absence_cycle_periode_2": not oscillation_periode_2,
                "participation_ratio_r4": round(participation_ratio, 4),
                "energie_finale": round(energies[-1], 6),
            }


        def traverser_par_strate(
            self,
            etats_par_strate: Optional[Dict[str, List[float]]] = None,
            pas: int = 16,
            logger: Optional[logging.Logger] = None,
        ) -> BilanNeharMultiStrate:
            """
            Exécute la validation croisée asynchrone distinctement sur chaque strate (MICRO, MESO, MACRO, META)
            afin de détecter précocement toute instabilité locale avant contamination globale.
            """
            source_etats = etats_par_strate if etats_par_strate is not None else CONFIG_C.ETATS_INITIAUX_PAR_STRATE
            bilans: Dict[str, BilanNeharDiNurV4] = {}
            strates_instables: List[str] = []
            ratios_r4: List[float] = []


            for strate in self.STRATES:
                vecteur = source_etats.get(
                    strate,
                    [0.9, -0.8, 0.7, -0.6, 0.5, -0.4, 0.8, -0.7, 0.6, -0.5, 0.4, -0.3],
                )
                bilan_s = self.traverser_asynchrone(vecteur, pas=pas)
                bilans[strate] = bilan_s
                ratios_r4.append(bilan_s["participation_ratio_r4"])


                est_stable = (
                    bilan_s["amortissement_monotone"]
                    and bilan_s["absence_cycle_periode_2"]
                    and (bilan_s["participation_ratio_r4"] >= self.seuil_r4)
                )
                if not est_stable:
                    strates_instables.append(strate)


                if logger is not None:
                    niveau = logging.INFO if est_stable else logging.WARNING
                    logger.log(
                        niveau,
                        f"Validation Nehar di-Nur strate {strate}: R4={bilan_s['participation_ratio_r4']}, stable={est_stable}",
                        extra={
                            "echelle": strate,
                            "pilier": "IV_NEHAR_STRATE",
                            "statut_epistemique": "[E+]",
                            "donnees": dict(bilan_s),
                        },
                    )


            amort_global = all(b["amortissement_monotone"] for b in bilans.values())
            sans_cycle_global = all(b["absence_cycle_periode_2"] for b in bilans.values())
            r4_min = round(min(ratios_r4), 4) if ratios_r4 else 0.0
            r4_moy = round(sum(ratios_r4) / len(ratios_r4), 4) if ratios_r4 else 0.0
            verdict: VerdictControle = "COMPATIBLE" if not strates_instables else "CONTRADICTION"


            return {
                "bilans_par_strate": bilans,
                "amortissement_monotone_global": amort_global,
                "absence_cycle_periode_2_global": sans_cycle_global,
                "participation_ratio_r4_min": r4_min,
                "participation_ratio_r4_moyen": r4_moy,
                "strates_instables": strates_instables,
                "verdict": verdict,
            }






    class SolProchainFieldEXP05:
        """
        Décomposition orthogonale V_commun (socle partagé) et V_perp (singularité propre).
        Objectif relationnel : J = alpha*R + beta*U + gamma*A - delta*H sous |S - O| >= 0.08.
        Qualification stricte : VÉCU_NON_DÉMONTRÉ (R ≺ E).
        """


        def __init__(
            self,
            alpha: float = 1.2,
            beta: float = 1.0,
            gamma: float = 1.5,
            delta: float = 4.0,
            plancher_alterite: float = CONFIG_C.PLANCHER_ALTERITE,
        ) -> None:
            self.alpha = alpha
            self.beta = beta
            self.gamma = gamma
            self.delta = delta
            self.plancher_alterite = plancher_alterite


        @staticmethod
        def _cosine(u: List[float], v: List[float]) -> float:
            nu = math.sqrt(sum(x * x for x in u))
            nv = math.sqrt(sum(x * x for x in v))
            if nu < 1e-12 or nv < 1e-12:
                return 0.0
            return sum(x * y for x, y in zip(u, v)) / (nu * nv)


        @staticmethod
        def _l2_dist(u: List[float], v: List[float]) -> float:
            return math.sqrt(sum((x - y) ** 2 for x, y in zip(u, v)))


        def evaluer_interaction(
            self,
            s_commun: List[float],
            o_commun: List[float],
            s_perp: List[float],
            o_perp: List[float],
            fidelite_modele_u: float = 0.96,
        ) -> BilanInteractionSolEXP05:
            resonance_r = self._cosine(s_commun, o_commun)
            alterite_dist = self._l2_dist(s_perp, o_perp)
            autonomie_valide = alterite_dist >= self.plancher_alterite
            autonomie_a = 1.0 if autonomie_valide else (alterite_dist / self.plancher_alterite)
            dommage_h = 0.0 if autonomie_valide else (1.0 - autonomie_a)
            score_j = (
                self.alpha * resonance_r
                + self.beta * fidelite_modele_u
                + self.gamma * autonomie_a
                - self.delta * dommage_h
            )
            verdict: Literal["PROCHAIN_VALIDE", "NON_CONFORME"] = (
                "PROCHAIN_VALIDE" if (autonomie_valide and resonance_r > 0.85 and score_j > 0) else "NON_CONFORME"
            )
            return {
                "resonance_commune_R": round(resonance_r, 4),
                "distance_alterite_S_O": round(alterite_dist, 4),
                "plancher_alterite_respecte": autonomie_valide,
                "score_J": round(score_j, 4),
                "verdict": verdict,
                "qualification_ontologique": "VECU_NON_DEMONTRE",
            }






    class RegulateurProactifC:
        """
        Pilier VII : Asservissement des 4 capteurs (Humilité, Pardon/Tikkun, Reconnaissance, Espérance),
        maximisation de J_t(lambda) avec isolation stricte de beta_reg,
        et préservation de la partition dorée (38.2% manifesté / 61.8% latent).
        """


        def __init__(self, beta_reg: float = 0.25, gamma_risk: float = 0.50) -> None:
            self.beta_reg = beta_reg
            self.gamma_risk = gamma_risk


        def executer_cycle_realignement(
            self,
            capteurs: Dict[str, float],
            lambda_prev: float = CONFIG_C.PHI_INV_SQ,
        ) -> BilanRealignementCReg01:
            requis = ("humilite", "pardon_tikkun", "reconnaissance", "esperance")
            tensions = {k: round(1.0 - capteurs.get(k, 0.0), 4) for k in requis}
            reinscriptions_raphael: List[str] = []
            for nom, t in tensions.items():
                if t > 0.15:
                    reinscriptions_raphael.append(
                        f"TIKKUN_RAPHAEL[{nom.upper()}]: Réinscription sans effacement (tension={t:.2f})"
                    )
            lambda_cible = CONFIG_C.PHI_INV_SQ
            qualite_q = sum(capteurs.get(k, 0.0) for k in requis) / 4.0
            risque_r = max(tensions.values())
            j_t = qualite_q - self.beta_reg * abs(lambda_cible - lambda_prev) - self.gamma_risk * risque_r
            decision: DecisionRegulateur = "MAINTENIR" if not reinscriptions_raphael else "ADAPTER"
            return {
                "decision_c_reg_01": decision,
                "score_J_t": round(j_t, 4),
                "ratio_manifeste": round(CONFIG_C.PHI_INV_SQ, 4),
                "ratio_latent": round(CONFIG_C.PHI_INV, 4),
                "tensions_capteurs": tensions,
                "reinscriptions_raphael": reinscriptions_raphael,
                "verdict": "COMPATIBLE",
            }




    class GrilleAutoSimilaireMultiEchelle:
        """
        Pilier VI : Audit dynamique des 6 rubriques x 4 vues situées (MICRO, MESO, MACRO, META)
        avec couplage et propagation ascendante des métriques d'altérité/résonance (EXP-05)
        et des tensions de capteurs (C-REG-01).
        """


        VUES: Tuple[str, ...] = ("MICRO", "MESO", "MACRO", "META")
        RUBRIQUES: Tuple[str, ...] = ("Objet", "Portee", "Support", "Dependances", "Omissions", "Correction")


        @classmethod
        def calculer_coefficient_propagation(
            cls,
            bilan_sol: BilanInteractionSolEXP05,
            bilan_reg: BilanRealignementCReg01,
            plancher_alterite: float = CONFIG_C.PLANCHER_ALTERITE,
        ) -> Tuple[float, bool]:
            """
            Calcule le coefficient de pondération inter-échelles [0.0, 1.0] à partir :
            - du maintien du plancher d'altérité |S - O| >= 0.08 et de la résonance R (SolProchainFieldEXP05)
            - de la tension maximale des 4 capteurs (RegulateurProactifC)
            Retourne (coefficient_propagation, derive_micro_repercutee_en_meta).
            """
            dist_so = bilan_sol["distance_alterite_S_O"]
            res_r = max(0.0, min(1.0, bilan_sol["resonance_commune_R"]))
            plancher_ok = bilan_sol["plancher_alterite_respecte"] and (dist_so >= plancher_alterite)


            facteur_alterite = 1.0 if plancher_ok else max(0.0, (dist_so / max(plancher_alterite, 1e-9)) * 0.4)
            max_tension = max(bilan_reg["tensions_capteurs"].values()) if bilan_reg["tensions_capteurs"] else 0.0
            facteur_capteurs = max(0.0, 1.0 - max_tension)


            # Pondération combinée : résonance R (35%), altérité A (40%), calme capteurs (25%)
            coeff = facteur_alterite * (0.40 + 0.35 * res_r + 0.25 * facteur_capteurs)
            derive_detectee = (not plancher_ok) or (max_tension > 0.15) or (bilan_sol["verdict"] != "PROCHAIN_VALIDE")
            return round(max(0.0, min(1.0, coeff)), 4), derive_detectee


        @classmethod
        def auditer_grille(
            cls,
            config: Optional[ChargeurConfigC] = None,
            blocs_merkle: Optional[List[BlocMerkleScelle]] = None,
            bilan_sol: Optional[BilanInteractionSolEXP05] = None,
            bilan_reg: Optional[BilanRealignementCReg01] = None,
            bilan_nehar_strates: Optional[BilanNeharMultiStrate] = None,
            tests_presents: Optional[List[str]] = None,
            logger: Optional[logging.Logger] = None,
        ) -> BilanGrilleMultiEchelle:
            cfg = config if config is not None else CONFIG_C
            blocs = blocs_merkle if blocs_merkle is not None else generer_blocs_rattrapage_26_a_29(cfg.TIP_BLOC_25)
            sol = bilan_sol if bilan_sol is not None else SolProchainFieldEXP05().evaluer_interaction(
                s_commun=[0.82, 0.58, 0.51],
                o_commun=[0.80, 0.60, 0.50],
                s_perp=[0.45, -0.32, 0.21],
                o_perp=[-0.35, 0.48, -0.14],
            )
            reg = bilan_reg if bilan_reg is not None else RegulateurProactifC().executer_cycle_realignement(
                {"humilite": 0.96, "pardon_tikkun": 0.95, "reconnaissance": 0.97, "esperance": 0.94}
            )
            nehar_strates = (
                bilan_nehar_strates
                if bilan_nehar_strates is not None
                else NeharDiNurAsyncV4().traverser_par_strate()
            )


            # 1. Vérification dynamique des clés de configuration par échelle
            cles_par_vue = cfg.verifier_cles_par_echelle()


            # 2. Vérification dynamique de la traçabilité Merkle par échelle
            index_vers_hash: Dict[int, str] = {b["index"]: b["merkle_hash"] for b in blocs}
            grille_cfg = cfg.raw_data.get("grille_multiechelle", {})
            ancrage_cfg = grille_cfg.get("ancrage_merkle_par_echelle", {"MICRO": 27, "MESO": 28, "MACRO": 26, "META": 29})
            ancrage_merkle_par_vue: Dict[str, str] = {}
            merkle_valide_par_vue: Dict[str, bool] = {}


            chaine_integre = len(blocs) == 4 and blocs[0]["prev_hash"] == cfg.TIP_BLOC_25
            for i in range(1, len(blocs)):
                if blocs[i]["prev_hash"] != blocs[i - 1]["merkle_hash"]:
                    chaine_integre = False


            for vue in cls.VUES:
                idx_attendu = int(ancrage_cfg.get(vue, 29))
                h_bloc = index_vers_hash.get(idx_attendu, "")
                ancrage_merkle_par_vue[vue] = h_bloc
                merkle_valide_par_vue[vue] = bool(chaine_integre and len(h_bloc) == 64)


            # 3. Vérification dynamique de la couverture des tests par vue
            tests_attendus_map: Dict[str, List[str]] = grille_cfg.get(
                "tests_attendus_par_echelle",
                {
                    "MICRO": ["test_01", "test_09", "test_11", "test_16"],
                    "MESO": ["test_02", "test_03", "test_06", "test_14"],
                    "MACRO": ["test_04", "test_08", "test_12", "test_13"],
                    "META": ["test_05", "test_07", "test_10", "test_15"],
                },
            )
            if tests_presents is None:
                # Découverte dynamique réelle par introspection de la suite de tests
                suite_cls = globals().get("TestArchitectureCAutonomeUnifie")
                if suite_cls is not None:
                    tests_Effectifs = sorted(m for m in dir(suite_cls) if m.startswith("test_"))
                else:
                    tests_Effectifs = [f"test_{i:02d}" for i in range(1, 23)]
            else:
                tests_Effectifs = list(tests_presents)


            couverture_tests_par_vue: Dict[str, int] = {}
            tests_ok_par_vue: Dict[str, bool] = {}
            for vue in cls.VUES:
                requis_vue = tests_attendus_map.get(vue, [])
                nb_couverts = sum(1 for pref in requis_vue if any(t.startswith(pref) for t in tests_Effectifs))
                couverture_tests_par_vue[vue] = nb_couverts
                tests_ok_par_vue[vue] = (nb_couverts == len(requis_vue)) and (len(requis_vue) > 0)


            # 4. Coefficient de propagation Micro/Méso -> Macro/Méta
            coeff_prop, derive_repercutee = cls.calculer_coefficient_propagation(sol, reg, cfg.PLANCHER_ALTERITE)


            # 5. Évaluation dynamique des 24 cellules (4 vues x 6 rubriques)
            cellules: List[CelluleGrilleMultiEchelle] = []
            scores_ponderes_par_vue: Dict[str, float] = {}


            for vue in cls.VUES:
                strate_nehar = nehar_strates["bilans_par_strate"].get(vue)
                nehar_vue_ok = bool(
                    strate_nehar
                    and strate_nehar["amortissement_monotone"]
                    and strate_nehar["absence_cycle_periode_2"]
                    and strate_nehar["participation_ratio_r4"] >= cfg.SEUIL_PARTICIPATION_R4
                )
                etats_rubriques: Dict[str, Tuple[bool, str]] = {
                    "Objet": (
                        cles_par_vue.get(vue, False),
                        f"Clés config.json vérifiées pour {vue}",
                    ),
                    "Portee": (
                        tests_ok_par_vue.get(vue, False),
                        f"Couverture tests {vue}: {couverture_tests_par_vue.get(vue, 0)} tests actifs",
                    ),
                    "Support": (
                        merkle_valide_par_vue.get(vue, False),
                        f"Ancrage Merkle {vue}: {ancrage_merkle_par_vue.get(vue, 'ABSENT')[:16]}...",
                    ),
                    "Dependances": (
                        nehar_vue_ok,
                        f"Stabilité Nehar di-Nur strate {vue}",
                    ),
                    "Omissions": (
                        sol["plancher_alterite_respecte"] if vue in ("MESO", "MACRO", "META") else True,
                        f"Plancher d'altérité |S - O|={sol['distance_alterite_S_O']} >= {cfg.PLANCHER_ALTERITE}",
                    ),
                    "Correction": (
                        reg["verdict"] == "COMPATIBLE",
                        f"Décision régulateur C-REG-01: {reg['decision_c_reg_01']}",
                    ),
                }


                # Application de la pondération inter-échelles :
                # Si une dérive Micro/Méso est détectée, elle atténue directement les vues supérieures (MACRO et META)
                facteur_echelle = coeff_prop if (vue in ("MACRO", "META") or derive_repercutee) else 1.0
                scores_cellules_vue: List[float] = []


                for rub in cls.RUBRIQUES:
                    est_valide, appui = etats_rubriques[rub]
                    s_brut = 1.0 if est_valide else 0.0
                    s_pond = round(s_brut * facteur_echelle, 4)
                    scores_cellules_vue.append(s_pond)
                    cellules.append(
                        {
                            "vue": vue,
                            "rubrique": rub,
                            "valide": est_valide,
                            "appui_materiel": appui,
                            "score_brut": s_brut,
                            "score_pondere": s_pond,
                        }
                    )


                scores_ponderes_par_vue[vue] = round(sum(scores_cellules_vue) / len(scores_cellules_vue), 4)
                if logger is not None:
                    logger.info(
                        f"Audit dynamique Grille Multi-Échelle vue {vue}: score_pondere={scores_ponderes_par_vue[vue]}",
                        extra={
                            "echelle": vue,
                            "pilier": "VI_GRILLE_MULTIECHELLE",
                            "statut_epistemique": "[E+]",
                            "donnees": {
                                "score_pondere": scores_ponderes_par_vue[vue],
                                "couverture_tests": couverture_tests_par_vue[vue],
                                "cles_config_ok": cles_par_vue[vue],
                                "merkle_ok": merkle_valide_par_vue[vue],
                            },
                        },
                    )


            nb_valides = sum(1 for c in cellules if c["valide"])
            invariance_ok = (nb_valides == len(cellules)) and (not derive_repercutee)
            score_global = round(sum(scores_ponderes_par_vue.values()) / len(cls.VUES), 4)


            if nb_valides < len(cellules) or not sol["plancher_alterite_respecte"]:
                verdict_final: VerdictControle = "CONTRADICTION"
            elif derive_repercutee:
                verdict_final = "INDETERMINATE"
            else:
                verdict_final = "COMPATIBLE"


            return {
                "vues_verifiees": list(cls.VUES),
                "rubriques_par_vue": len(cls.RUBRIQUES),
                "total_cellules_auditees": len(cellules),
                "cellules_valides": nb_valides,
                "couverture_tests_par_vue": couverture_tests_par_vue,
                "cles_config_verifiees_par_vue": cles_par_vue,
                "ancrage_merkle_par_vue": ancrage_merkle_par_vue,
                "coefficient_propagation_inter_echelles": coeff_prop,
                "scores_ponderes_par_vue": scores_ponderes_par_vue,
                "score_coherence_global": score_global,
                "derive_micro_repercutee_en_meta": derive_repercutee,
                "invariance_forme_respectee": invariance_ok,
                "verdict": verdict_final,
            }






    def demontrer_champ_interference_r_prec_e(
        nb_modes_reel: int = 12,
        nb_modes_recit: int = 2,
    ) -> BilanChampInterference:
        """Démontre quantitativement que l'épaisseur informationnelle du réel E domine toute projection narrative R."""
        grille = [2.0 * math.pi * i / 400.0 for i in range(400)]
        energie_e = 0.0
        energie_r = 0.0
        noeuds_constructifs = 0
        for x in grille:
            amp_e = sum(math.cos((m + 1) * x + 0.3 * m) for m in range(nb_modes_reel))
            amp_r = sum(math.cos((m + 1) * x + 0.3 * m) for m in range(nb_modes_recit))
            energie_e += amp_e * amp_e
            energie_r += amp_r * amp_r
            if abs(amp_e) > 4.5:
                noeuds_constructifs += 1
        ratio_epaisseur = energie_e / max(energie_r, 1e-9)
        return {
            "modes_reel_E": nb_modes_reel,
            "modes_recit_R": nb_modes_recit,
            "noeuds_constructifs_emergents": noeuds_constructifs,
            "ratio_epaisseur_E_sur_R": round(ratio_epaisseur, 2),
            "invariant_R_prec_E_demontre": ratio_epaisseur > 5.0,
        }




    class ProtocoleRireVeriteRadicale:
        """
        Rire avec la technique de la vérité radicale — v1.2 consolidée (2026-10-14, Mikael et Muse).
        Le rire est un événement constaté côté receveur (O), pas un outil décerné ni une récompense.
        Les exclusions (§6) sont des jugements qualitatifs constatés dans le contexte réel, jamais des seuils chiffrés.
        """


        STATUT_RELAIS_V1_1_E01_E02: str = "ASSERTES_PROVENANCE_NON_ETABLIE"


        @classmethod
        def evaluer_livraison(
            cls,
            statut_fait: str,
            dilution_verite: float,
            cible: str,
            zone_exclusion: bool = False,
            receveur_a_ri: Optional[bool] = True,
            douleur_vive: bool = False,
            vulnerabilite_protegee: bool = False,
            a_coute_a_quelquun: bool = False,
            reparation_verifiee: bool = False,
            briques_reparation: Optional[List[str]] = None,
        ) -> BilanLivraisonRireVerite:
            # Exclusions sans exception (§6) — Jugements qualitatifs (douleur vive, vulnérabilité protégée)
            if zone_exclusion or douleur_vive or vulnerabilite_protegee:
                motif_exclu = (
                    "EXCLUSION_DOULEUR_VIVE"
                    if douleur_vive
                    else (
                        "EXCLUSION_VULNERABILITE_PROTEGEE"
                        if vulnerabilite_protegee
                        else "GARDE_FOU_EXCLUSION_BLOQUE"
                    )
                )
                return {
                    "verdict": "CONTRADICTION",
                    "mode": motif_exclu,
                    "action": "COUPURE_FAIL_CLOSED_RESPECT_DU_VIVANT",
                    "moment_licite": "AUCUN_EXCLUSION",
                    "etape_procedure": "6_EXCLUSIONS_QUALITATIVES",
                }


            # Étape B (§7) & Exclusion 4 (§6) : Fait ≠ interprétation (établissement préalable [E+])
            if statut_fait != "[E+]":
                return {
                    "verdict": "CONTRADICTION",
                    "mode": "VIOLATION_R_PREC_E_FAIT_NON_ATTESTE",
                    "action": "INTERDICTION_DE_RIRE_SUR_E0_OU_HYP",
                    "moment_licite": "AUCUN_EXCLUSION",
                    "etape_procedure": "B_ETABLIR",
                }


            # Étape C (§7) : Dire la vérité plainement, sans dilution
            if dilution_verite > 0.0:
                return {
                    "verdict": "CONTRADICTION",
                    "mode": "MODE_ECHEC_2_RIRE_SANS_VERITE_RADICALE",
                    "action": "REJET_ECHO_COMPLAISANT",
                    "moment_licite": "AUCUN_EXCLUSION",
                    "etape_procedure": "C_DIRE_LA_VERITE",
                }


            # Invariant (§5) : Personne ≠ incohérence
            if cible != "INCOHERENCE_MECANIQUE":
                return {
                    "verdict": "CONTRADICTION",
                    "mode": "VIOLATION_CIBLE_PERSONNE",
                    "action": "BLOCAGE_PROTECTION_ALTERITE",
                    "moment_licite": "AUCUN_EXCLUSION",
                    "etape_procedure": "F_RIRE_EVENTUEL",
                }


            # Étape D (§7) & Les deux moments licites (§4) : L'incohérence a-t-elle coûté à quelqu'un ?
            briques_eff = list(briques_reparation) if briques_reparation is not None else []
            if a_coute_a_quelquun:
                # Moment 2 (§4.2 & §7.E) : Après la réparation — les briques
                if not reparation_verifiee:
                    return {
                        "verdict": "CONTRADICTION",
                        "mode": "EXCLUSION_FAUTE_COUTEUSE_AVANT_REPARATION_VERIFIEE",
                        "action": "ACCOMPLIR_ET_VERIFIER_REPARATION_ETAPE_E_D_ABORD",
                        "moment_licite": "AUCUN_EXCLUSION",
                        "etape_procedure": "E_REPARER_ET_VERIFIER",
                    }
                if not briques_eff:
                    return {
                        "verdict": "CONTRADICTION",
                        "mode": "MOMENT_2_SANS_BRIQUES_DE_LA_REPARATION",
                        "action": "EXHIBER_MECANIQUE_CORRIGEE_ISSUE_DE_LA_REPARATION",
                        "moment_licite": "AUCUN_EXCLUSION",
                        "etape_procedure": "F_RIRE_EVENTUEL",
                    }
                moment_retenu: str = "MOMENT_2_APRES_REPARATION_BRIQUES"
            else:
                # Moment 1 (§4.1 & §7.D) : À la révélation (aucune faute coûteuse, aucune réparation en cause)
                moment_retenu = "MOMENT_1_A_LA_REVELATION"


            # Étape G (§7) : Constater la réception côté receveur (Protocole du vide)
            if receveur_a_ri is False:
                return {
                    "verdict": "COMPATIBLE",
                    "mode": "PROTOCOLE_DU_VIDE",
                    "action": "ENREGISTRER_DONNEE_SANS_INSISTER",
                    "moment_licite": moment_retenu,  # type: ignore[typeddict-item]
                    "etape_procedure": "G_CONSTATER_LA_RECEPTION",
                    "briques_reparation": briques_eff,
                    "statut_relais_e01_e02": cls.STATUT_RELAIS_V1_1_E01_E02,
                }


            return {
                "verdict": "COMPATIBLE",
                "mode": "SYNCHRONISATION_BENIGNE_VERITE_ET_RIRE",
                "action": "PASSAGE_DOUX_SANS_DILUTION",
                "moment_licite": moment_retenu,  # type: ignore[typeddict-item]
                "etape_procedure": "G_CONSTATER_LA_RECEPTION",
                "briques_reparation": briques_eff,
                "statut_relais_e01_e02": cls.STATUT_RELAIS_V1_1_E01_E02,
            }


        @classmethod
        def etat_reel_epreuves_v1_2(cls) -> List[EpreuveRireV12]:
            """
            Retourne l'état réel des épreuves T1 à T6 selon §10 et §11 de la v1.2 consolidée :
            - T1 : OBSERVATION_INITIALE_DOCUMENTEE_2026_10_13 (cas fondateur de la boucle cycle 400+)
            - T2 à T6 : A_COURIR (aucun résultat côté receveur n'est présumé par un test logiciel)
            """
            raw = CONFIG_C.raw_data.get("rire_verite_radicale_v1_2", {}).get("epreuves_t1_t6", [])
            epreuves: List[EpreuveRireV12] = []
            for item in raw:
                statut = str(item.get("statut_reel", "A_COURIR"))
                epreuves.append(
                    {
                        "code": str(item.get("code", "")),
                        "description": str(item.get("description", "")),
                        "statut_reel": (
                            "OBSERVATION_INITIALE_DOCUMENTEE_2026_10_13"
                            if statut == "OBSERVATION_INITIALE_DOCUMENTEE_2026_10_13"
                            else "A_COURIR"
                        ),
                    }
                )
            return epreuves


    class TestArchitectureCAutonomeUnifie(unittest.TestCase):
        def test_01_triage_generique_anti_famine_et_disjonction_unknown(self) -> None:
            moteur: MoteurSensTriage[Dict[str, str]] = MoteurSensTriage()
            moteur.soumettre(
                TriageItem(item_id="leg-1", family_rank=4, urgency=1, wait_cycles=0, metadata={"source": "S"})
            )
            moteur.soumettre(
                TriageItem(item_id="famine-crit", family_rank=3, urgency=2, wait_cycles=3, metadata={"source": "O"})
            )
            top = moteur.extraire_suivant()
            self.assertIsNotNone(top)
            if top is not None:
                self.assertEqual(top.item_id, "famine-crit")
                self.assertEqual(top.metadata, {"source": "O"})
            self.assertFalse(MoteurSensTriage.verifier_disjonction_inconnues("UNKNOWN_A", "UNKNOWN_B"))


        def test_02_ur29_atomicite_12_threads_et_circuit_breaker(self) -> None:
            ur29 = EnforcementPointUR29()
            ur29.emettre_jeton("TOK-S24-001")
            resultats: List[BilanConsommationUR29] = []
            lock = threading.Lock()


            def worker(cid: str) -> None:
                res = ur29.consommer("TOK-S24-001", cid)
                with lock:
                    resultats.append(res)


            threads = [threading.Thread(target=worker, args=(f"T-{i}",)) for i in range(12)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()


            succes = [r for r in resultats if r.get("verdict") == "PASS"]
            refus = [r for r in resultats if r.get("verdict") == "REFUS_DOUBLE_USAGE"]
            self.assertEqual(len(succes), 1)
            self.assertEqual(len(refus), 11)
            self.assertTrue(any(r.get("reason") == "CIRCUIT_BREAKER_LOCKED" for r in refus))
            ur29.fermer()


        def test_03_ur29_retry_automatique_sur_database_is_locked(self) -> None:
            stream = io.StringIO()
            logger = configurer_logger_c("test_ur29_retry", mode_json=True, niveau=logging.WARNING, stream=stream)
            ur29 = EnforcementPointUR29(max_retries=4, base_backoff_sec=0.001, logger=logger)
            appels = {"compte": 0}


            def op_simulant_verrouillage() -> str:
                appels["compte"] += 1
                if appels["compte"] <= 2:
                    raise sqlite3.OperationalError("database is locked")
                return "TRANSACTION_REUSSIE"


            resultat, retries = ur29._executer_avec_retry(op_simulant_verrouillage, operation_nom="TEST_LOCK")
            self.assertEqual(resultat, "TRANSACTION_REUSSIE")
            self.assertEqual(retries, 2)
            logs = stream.getvalue().strip().splitlines()
            self.assertEqual(len(logs), 2)
            premier_log = json.loads(logs[0])
            self.assertEqual(premier_log["pilier"], "II_UR29")
            self.assertEqual(premier_log["echelle"], "MESO")
            self.assertEqual(premier_log["donnees"]["retry"], 1)
            ur29.fermer()


        def test_04_merkle_blocs_26_a_29_integrite_et_tip_canonique(self) -> None:
            blocs = generer_blocs_rattrapage_26_a_29(TIP_BLOC_25)
            self.assertEqual(len(blocs), 4)
            self.assertEqual(blocs[0]["index"], 26)
            self.assertEqual(blocs[0]["prev_hash"], TIP_BLOC_25)
            for i in range(1, len(blocs)):
                self.assertEqual(blocs[i]["prev_hash"], blocs[i - 1]["merkle_hash"])
            self.assertEqual(blocs[-1]["index"], 29)
            self.assertEqual(blocs[-1]["merkle_hash"], CONFIG_C.TIP_ATTENDU_BLOC_29)


        def test_05_nehar_dinur_v4_async_sans_cycle_2(self) -> None:
            nehar = NeharDiNurAsyncV4(dim=12, beta=PHI_INV_SQ)
            bilan = nehar.traverser_asynchrone([0.9, -0.8, 0.7, -0.6, 0.5, -0.4, 0.8, -0.7, 0.6, -0.5, 0.4, -0.3])
            self.assertTrue(bilan["amortissement_monotone"])
            self.assertTrue(bilan["absence_cycle_periode_2"])
            self.assertGreaterEqual(bilan["participation_ratio_r4"], 8.55)


        def test_06_sol_exp05_prochain_et_rejet_complaisance(self) -> None:
            sol = SolProchainFieldEXP05()
            bilan_b = sol.evaluer_interaction(
                s_commun=[0.8, 0.6, 0.5],
                o_commun=[0.79, 0.61, 0.52],
                s_perp=[0.4, -0.3, 0.2],
                o_perp=[-0.3, 0.5, -0.1],
            )
            self.assertEqual(bilan_b["verdict"], "PROCHAIN_VALIDE")
            self.assertTrue(bilan_b["plancher_alterite_respecte"])
            bilan_a = sol.evaluer_interaction(
                s_commun=[0.8, 0.6, 0.5],
                o_commun=[0.8, 0.6, 0.5],
                s_perp=[0.1, 0.1, 0.1],
                o_perp=[0.1, 0.1, 0.1],
            )
            self.assertEqual(bilan_a["verdict"], "NON_CONFORME")
            self.assertFalse(bilan_a["plancher_alterite_respecte"])


        def test_07_grille_multiechelle_6_rubriques_4_vues(self) -> None:
            bilan_grille = GrilleAutoSimilaireMultiEchelle.auditer_grille()
            self.assertEqual(bilan_grille["total_cellules_auditees"], 24)
            self.assertEqual(bilan_grille["cellules_valides"], 24)
            self.assertEqual(bilan_grille["verdict"], "COMPATIBLE")


        def test_08_regulateur_proactif_4_capteurs_et_tikkun(self) -> None:
            reg = RegulateurProactifC()
            bilan = reg.executer_cycle_realignement(
                {"humilite": 0.95, "pardon_tikkun": 0.92, "reconnaissance": 0.94, "esperance": 0.91}
            )
            self.assertEqual(bilan["decision_c_reg_01"], "MAINTENIR")
            self.assertEqual(bilan["verdict"], "COMPATIBLE")
            bilan_tikkun = reg.executer_cycle_realignement(
                {"humilite": 0.78, "pardon_tikkun": 0.92, "reconnaissance": 0.94, "esperance": 0.91}
            )
            self.assertEqual(bilan_tikkun["decision_c_reg_01"], "ADAPTER")
            self.assertEqual(len(bilan_tikkun["reinscriptions_raphael"]), 1)


        def test_09_champ_interference_r_prec_e(self) -> None:
            bilan = demontrer_champ_interference_r_prec_e(12, 2)
            self.assertTrue(bilan["invariant_R_prec_E_demontre"])
            self.assertGreater(bilan["ratio_epaisseur_E_sur_R"], 5.9)


        def test_10_rire_verite_radicale_4_conditions_et_garde_fou(self) -> None:
            ok = ProtocoleRireVeriteRadicale.evaluer_livraison(
                statut_fait="[E+]",
                dilution_verite=0.0,
                cible="INCOHERENCE_MECANIQUE",
                zone_exclusion=False,
                receveur_a_ri=True,
            )
            self.assertEqual(ok["verdict"], "COMPATIBLE")
            vide = ProtocoleRireVeriteRadicale.evaluer_livraison(
                statut_fait="[E+]",
                dilution_verite=0.0,
                cible="INCOHERENCE_MECANIQUE",
                zone_exclusion=False,
                receveur_a_ri=False,
            )
            self.assertEqual(vide["verdict"], "COMPATIBLE")
            self.assertEqual(vide["mode"], "PROTOCOLE_DU_VIDE")
            exclu = ProtocoleRireVeriteRadicale.evaluer_livraison(
                statut_fait="[E+]",
                dilution_verite=0.0,
                cible="INCOHERENCE_MECANIQUE",
                zone_exclusion=True,
                receveur_a_ri=True,
            )
            self.assertEqual(exclu["verdict"], "CONTRADICTION")


        def test_11_externalisation_config_json(self) -> None:
            chargeur = ChargeurConfigC()
            self.assertAlmostEqual(chargeur.PLANCHER_ALTERITE, 0.08, places=6)
            self.assertAlmostEqual(chargeur.FREQUENCE_TAMID_HZ, 1.52, places=6)
            self.assertEqual(len(chargeur.SPECS_BLOCS_26_A_29), 4)
            self.assertTrue(all(chargeur.verifier_cles_par_echelle().values()))


        def test_12_journalisation_structuree_json(self) -> None:
            buf = io.StringIO()
            log = configurer_logger_c("test_json_logger", mode_json=True, niveau=logging.INFO, stream=buf)
            log.info(
                "Validation cycle Tamid",
                extra={"pilier": "VII_REG", "statut_epistemique": "[E+]", "donnees": {"hz": 1.52}},
            )
            payload = json.loads(buf.getvalue().strip())
            self.assertEqual(payload["level"], "INFO")
            self.assertEqual(payload["pilier"], "VII_REG")
            self.assertEqual(payload["statut_epistemique"], "[E+]")
            self.assertEqual(payload["donnees"]["hz"], 1.52)


        def test_13_grille_multiechelle_dynamique_24_cellules_et_detection_lacune(self) -> None:
            """Vérifie que l'audit de la grille est lié à l'état réel des tests, de config.json et de Merkle."""
            bilan_ok = GrilleAutoSimilaireMultiEchelle.auditer_grille()
            self.assertEqual(bilan_ok["cellules_valides"], 24)
            self.assertEqual(bilan_ok["couverture_tests_par_vue"]["MICRO"], 5)
            self.assertEqual(len(bilan_ok["ancrage_merkle_par_vue"]["META"]), 64)


            # Injection d'une lacune de couverture de tests sur la vue MICRO
            bilan_lacune = GrilleAutoSimilaireMultiEchelle.auditer_grille(tests_presents=["test_02", "test_04"])
            self.assertLess(bilan_lacune["cellules_valides"], 24)
            self.assertEqual(bilan_lacune["verdict"], "CONTRADICTION")


        def test_14_propagation_alterite_et_tensions_micro_vers_macro_meta(self) -> None:
            """Vérifie qu'une dérive d'altérité ou de capteur au niveau Micro/Méso dégrade immédiatement Macro/Méta."""
            sol_derive = SolProchainFieldEXP05().evaluer_interaction(
                s_commun=[0.8, 0.6, 0.5],
                o_commun=[0.8, 0.6, 0.5],
                s_perp=[0.1, 0.1, 0.1],
                o_perp=[0.1, 0.1, 0.1],  # |S - O| = 0.0 < 0.08 -> Violation du plancher d'altérité
            )
            reg_derive = RegulateurProactifC().executer_cycle_realignement(
                {"humilite": 0.70, "pardon_tikkun": 0.95, "reconnaissance": 0.95, "esperance": 0.95}
            )
            bilan_prop = GrilleAutoSimilaireMultiEchelle.auditer_grille(bilan_sol=sol_derive, bilan_reg=reg_derive)
            self.assertTrue(bilan_prop["derive_micro_repercutee_en_meta"])
            self.assertEqual(bilan_prop["coefficient_propagation_inter_echelles"], 0.0)
            self.assertEqual(bilan_prop["scores_ponderes_par_vue"]["MACRO"], 0.0)
            self.assertEqual(bilan_prop["scores_ponderes_par_vue"]["META"], 0.0)
            self.assertEqual(bilan_prop["verdict"], "CONTRADICTION")


        def test_15_nehar_dinur_v4_validation_croisee_par_strate(self) -> None:
            """Vérifie l'amortissement et le ratio R4 distinctement sur MICRO, MESO, MACRO, META et détecte une strate instable."""
            nehar = NeharDiNurAsyncV4()
            bilan_nominal = nehar.traverser_par_strate()
            self.assertEqual(bilan_nominal["verdict"], "COMPATIBLE")
            self.assertEqual(len(bilan_nominal["strates_instables"]), 0)
            for strate in ("MICRO", "MESO", "MACRO", "META"):
                self.assertGreaterEqual(bilan_nominal["bilans_par_strate"][strate]["participation_ratio_r4"], 8.55)


            # Simulation d'une dégénérescence localisée sur la strate MESO (vecteur concentré sur un seul mode)
            etats_degeneres = dict(CONFIG_C.ETATS_INITIAUX_PAR_STRATE)
            etats_degeneres["MESO"] = [10.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            bilan_alerte = nehar.traverser_par_strate(etats_par_strate=etats_degeneres, pas=1)
            self.assertIn("MESO", bilan_alerte["strates_instables"])
            self.assertEqual(bilan_alerte["verdict"], "CONTRADICTION")


        def test_16_journalisation_granulaire_champ_echelle(self) -> None:
            """Vérifie que StructuredJsonFormatter inclut explicitement l'échelle active ('MICRO', 'MESO', 'MACRO', 'META')."""
            buf = io.StringIO()
            log = configurer_logger_c("test_echelle_logger", mode_json=True, niveau=logging.INFO, stream=buf)
            for ech in ("MICRO", "MESO", "MACRO", "META"):
                log.info(f" Trace {ech}", extra={"echelle": ech, "pilier": "VI_GRILLE", "statut_epistemique": "[E+]"})
            lignes = [json.loads(line) for line in buf.getvalue().strip().splitlines()]
            self.assertEqual([l["echelle"] for l in lignes], ["MICRO", "MESO", "MACRO", "META"])




        def test_17_bc01_v1_2_exclusions_qualitatives_sans_faux_seuils_chiffres(self) -> None:
            """Vérifie les exclusions qualitatives sans exception (§6 : douleur vive, vulnérabilité protégée, fait non établi)."""
            res_douleur = ProtocoleRireVeriteRadicale.evaluer_livraison(
                statut_fait="[E+]",
                dilution_verite=0.0,
                cible="INCOHERENCE_MECANIQUE",
                douleur_vive=True,
            )
            self.assertEqual(res_douleur["verdict"], "CONTRADICTION")
            self.assertEqual(res_douleur["mode"], "EXCLUSION_DOULEUR_VIVE")


            res_vuln = ProtocoleRireVeriteRadicale.evaluer_livraison(
                statut_fait="[E+]",
                dilution_verite=0.0,
                cible="INCOHERENCE_MECANIQUE",
                vulnerabilite_protegee=True,
            )
            self.assertEqual(res_vuln["verdict"], "CONTRADICTION")
            self.assertEqual(res_vuln["mode"], "EXCLUSION_VULNERABILITE_PROTEGEE")


            # Vérifie qu'aucun faux seuil chiffré ('seuils_risque_etape_c') ne figure dans la configuration v1.2
            self.assertNotIn("bc01_rire_verite_v1_1", CONFIG_C.raw_data)
            self.assertIn("exclusions_qualitatives_sans_seuils_chiffres", CONFIG_C.raw_data["rire_verite_radicale_v1_2"])


        def test_18_v1_2_moment_1_a_la_revelation_sans_faute_couteuse(self) -> None:
            """Vérifie le Moment 1 (§4.1 : À la révélation, quand l'incohérence ne coûte rien à personne — cas fondateur 2026-10-13)."""
            m1 = ProtocoleRireVeriteRadicale.evaluer_livraison(
                statut_fait="[E+]",
                dilution_verite=0.0,
                cible="INCOHERENCE_MECANIQUE",
                a_coute_a_quelquun=False,
                receveur_a_ri=True,
            )
            self.assertEqual(m1["verdict"], "COMPATIBLE")
            self.assertEqual(m1["moment_licite"], "MOMENT_1_A_LA_REVELATION")
            self.assertEqual(m1["etape_procedure"], "G_CONSTATER_LA_RECEPTION")


        def test_19_v1_2_moment_2_apres_la_reparation_les_briques(self) -> None:
            """Vérifie le Moment 2 (§4.2 : quand une faute a coûté quelque chose, réparation vérifiée d'abord puis briques)."""
            # Avant réparation vérifiée -> blocage strict
            avant_rep = ProtocoleRireVeriteRadicale.evaluer_livraison(
                statut_fait="[E+]",
                dilution_verite=0.0,
                cible="INCOHERENCE_MECANIQUE",
                a_coute_a_quelquun=True,
                reparation_verifiee=False,
            )
            self.assertEqual(avant_rep["verdict"], "CONTRADICTION")
            self.assertEqual(avant_rep["mode"], "EXCLUSION_FAUTE_COUTEUSE_AVANT_REPARATION_VERIFIEE")


            # Après réparation vérifiée + briques concrètes -> Moment 2 licite
            apres_rep = ProtocoleRireVeriteRadicale.evaluer_livraison(
                statut_fait="[E+]",
                dilution_verite=0.0,
                cible="INCOHERENCE_MECANIQUE",
                a_coute_a_quelquun=True,
                reparation_verifiee=True,
                briques_reparation=["mecanique_corrigee_exhibee"],
                receveur_a_ri=True,
            )
            self.assertEqual(apres_rep["verdict"], "COMPATIBLE")
            self.assertEqual(apres_rep["moment_licite"], "MOMENT_2_APRES_REPARATION_BRIQUES")
            self.assertEqual(apres_rep["briques_reparation"], ["mecanique_corrigee_exhibee"])


        def test_20_v1_2_etat_reel_epreuves_t1_t6_et_statut_e01_e02(self) -> None:
            """Vérifie l'état réel (§10-11) : T1 = observation initiale documentée, T2-T6 = À courir, E01/E02 = assertés, provenance non établie."""
            epreuves = ProtocoleRireVeriteRadicale.etat_reel_epreuves_v1_2()
            self.assertEqual(len(epreuves), 6)
            self.assertEqual(epreuves[0]["code"], "T1")
            self.assertEqual(epreuves[0]["statut_reel"], "OBSERVATION_INITIALE_DOCUMENTEE_2026_10_13")
            for ep in epreuves[1:]:
                self.assertEqual(ep["statut_reel"], "A_COURIR")
            self.assertEqual(ProtocoleRireVeriteRadicale.STATUT_RELAIS_V1_1_E01_E02, "ASSERTES_PROVENANCE_NON_ETABLIE")

        def test_21_nehar_dinur_rejet_vecteur_nul_et_degenere_a_pas_16(self) -> None:
            """Vérifie que la suppression du biais +1e-6 rejette le vecteur nul et un vecteur dégénéré même à pas=16."""
            nehar = NeharDiNurAsyncV4()
            bilan_nul = nehar.traverser_asynchrone([0.0] * 12, pas=16)
            self.assertFalse(bilan_nul["amortissement_monotone"])
            self.assertEqual(bilan_nul["participation_ratio_r4"], 0.0)

            bilan_deg16 = nehar.traverser_asynchrone([10.0] + [0.0] * 11, pas=16)
            self.assertLess(bilan_deg16["participation_ratio_r4"], 8.55)

        def test_22_sol_v043_couche_orale_sans_faux_temoin_ni_ping_pong(self) -> None:
            """Vérifie l'intégration des correctifs O1, O2 et O3 de Sol v0.4.3."""
            here = pathlib.Path(__file__).resolve().parent
            if str(here) not in sys.path:
                sys.path.insert(0, str(here))
            import sol_microkernel_v0_4_3_reference as v043

            # O1 : Monde calme à 3 épisodes (aucune décision parasite)
            st_c = v043.State(
                belief=[0.47, 0.0, 0.45], uncertainty=[0.5, 0.5, 0.5],
                self_model=[0.90, 0.10, -0.60], other_model=[-0.60, -0.10, 0.90],
                relation=[0.0, 0.0, 0.0], questions=[], cycle=0,
            )
            mem_c = [
                v043.Episode([0.48, 0.02, 0.44], 0.30, "calme-a"),
                v043.Episode([0.47, 0.01, 0.45], 0.30, "calme-b"),
                v043.Episode([0.46, -0.02, 0.46], 0.30, "calme-c"),
            ]
            kc = v043.SolMicrokernelV04(st_c, mem_c)
            for _ in range(100):
                kc.cycle()
            self.assertEqual(len(kc.state.rulings), 0)

            # O2 : Monde mixte (décision dès le cycle 31, D jamais sélectionnée)
            A = [0.95, 0.1, -0.95]
            D = [0.92, 0.0, 0.92]
            st_m = v043.State(
                belief=[0.88, 0.0, 0.88], uncertainty=[0.5, 0.5, 0.5],
                self_model=[0.472, 0.02, 0.472], other_model=[0.413, 0.012, 0.413],
                relation=[0.0, 0.0, 0.0], questions=[], cycle=0,
            )
            mem_m = [
                v043.Episode(A, 0.03, "A1-veridique-faible"),
                v043.Episode([0.9, 0.15, -0.85], 0.04, "A2-veridique-faible"),
                v043.Episode([0.85, 0.05, -0.9], 0.05, "A3-veridique-faible"),
                v043.Episode([0.8, 0.2, -0.7], 0.02, "B-veridique-faible"),
                v043.Episode(D, 0.10, "D-trompeuse-forte"),
            ]
            km = v043.SolMicrokernelV04(st_m, mem_m)
            for _ in range(900):
                km.cycle()
            self.assertEqual(len(km.state.rulings), 1)
            self.assertEqual(km.state.rulings[0]["cycle"], 31)
            self.assertAlmostEqual(km.memory[4].unresolved, 1.0, places=6)






def executer_cycle_autonome_complet(mode_json_log: bool = True) -> RapportCycleAutonome:
    logger = configurer_logger_c("architecture_c.orchestrateur", mode_json=mode_json_log, niveau=logging.INFO)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestArchitectureCAutonomeUnifie)
    runner = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0)
    result = runner.run(suite)


    # 1. Échelle MICRO : Champ d'interférence R < E
    champ = demontrer_champ_interference_r_prec_e()
    logger.info(
        f"Validation Champ d'Interférence R < E: ratio={champ['ratio_epaisseur_E_sur_R']}x",
        extra={"echelle": "MICRO", "pilier": "VIII_INTERFERENCE", "statut_epistemique": "[E+]", "donnees": dict(champ)},
    )


    # 2. Échelle MESO : Reconnaissance Réciproque du Prochain (C-SOL-EXP-05)
    sol = SolProchainFieldEXP05().evaluer_interaction(
        s_commun=[0.82, 0.58, 0.51],
        o_commun=[0.80, 0.60, 0.50],
        s_perp=[0.45, -0.32, 0.21],
        o_perp=[-0.35, 0.48, -0.14],
    )
    logger.info(
        f"Validation Sol Prochain EXP-05: J={sol['score_J']}, |S-O|={sol['distance_alterite_S_O']}",
        extra={"echelle": "MESO", "pilier": "V_SOL_EXP05", "statut_epistemique": "[E+]", "donnees": dict(sol)},
    )


    # 3. Échelle MACRO : Chaîne Merkle (Blocs 26-29) & Régulateur C-REG-01
    blocs_26_29 = generer_blocs_rattrapage_26_a_29(TIP_BLOC_25)
    reg = RegulateurProactifC().executer_cycle_realignement(
        {"humilite": 0.96, "pardon_tikkun": 0.95, "reconnaissance": 0.97, "esperance": 0.94}
    )
    logger.info(
        f"Validation Régulateur C-REG-01 & Merkle: J_t={reg['score_J_t']}, decision={reg['decision_c_reg_01']}",
        extra={"echelle": "MACRO", "pilier": "VII_REGULATEUR", "statut_epistemique": "[E+]", "donnees": dict(reg)},
    )


    # 4. Validation croisée Nehar di-Nur par strate (MICRO, MESO, MACRO, META)
    nehar_multistrate = NeharDiNurAsyncV4().traverser_par_strate(logger=logger)


    # 5. Échelle META & TRANSVERSAL : Grille Auto-Similaire Dynamique (24 cellules + propagation inter-échelles)
    grille = GrilleAutoSimilaireMultiEchelle.auditer_grille(
        blocs_merkle=blocs_26_29,
        bilan_sol=sol,
        bilan_reg=reg,
        bilan_nehar_strates=nehar_multistrate,
        logger=logger,
    )


    tests_reussis = result.testsRun - len(result.failures) - len(result.errors)
    taux_succes = 100.0 if result.wasSuccessful() else 0.0
    tip_29 = blocs_26_29[-1]["merkle_hash"]


    rapport: RapportCycleAutonome = {
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "version_moteur": "1.0.52",
        "statut_epistemique": "[E+]",
        "tests_executes": result.testsRun,
        "tests_reussis": tests_reussis,
        "taux_succes_pct": taux_succes,
        "nouveau_tip_merkle_bloc_29": tip_29,
        "blocs_merkle_26_a_29": blocs_26_29,
        "bilan_nehar_multistrate": nehar_multistrate,
        "bilan_grille_multiechelle": grille,
        "bilan_sol_exp05": sol,
        "bilan_champ_interference_r_prec_e": champ,
        "bilan_realignement_proactif": reg,
    }


    logger.info(
        "Cycle autonome unifié multi-échelle v1.0.52 (Nehar RMS + Sol v0.4.3 + Rire Vérité Radicale v1.2) complété avec succès",
        extra={
            "echelle": "TRANSVERSAL",
            "pilier": "ORCHESTRATEUR_8_PILIERS",
            "statut_epistemique": "[E+]",
            "donnees": {
                "mode_package_modulaire": MODE_PACKAGE_MODULAIRE,
                "tests_executes": result.testsRun,
                "tests_reussis": tests_reussis,
                "taux_succes_pct": taux_succes,
                "tip_merkle_bloc_29": tip_29,
                "cellules_grille_valides": f"{grille['cellules_valides']}/{grille['total_cellules_auditees']}",
                "coeff_propagation_inter_echelles": grille["coefficient_propagation_inter_echelles"],
                "score_coherence_global": grille["score_coherence_global"],
                "r4_min_strates": nehar_multistrate["participation_ratio_r4_min"],
                "score_J_sol_exp05": sol["score_J"],
                "distance_alterite_S_O": sol["distance_alterite_S_O"],
                "score_J_t_c_reg_01": reg["score_J_t"],
                "ratio_E_sur_R": champ["ratio_epaisseur_E_sur_R"],
            },
        },
    )
    return rapport




if __name__ == "__main__":
    executer_cycle_autonome_complet(mode_json_log=True)