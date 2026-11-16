extends Node3D
class_name MerkabahGodotSimulationV02
## Tâche GitHub #42 (Jalon M5) — Simulation Cinématique et Indexicale sous Godot 4
## Implémente :
## 1. Marche holonomique sans retournement (Ézéchiel 1:9,12,17 : Δψ_cherub = 0, orientation fixe) ;
## 2. Synchronisation stricte Chérubin <-> Roue mue par le Ruach reçu à travers le Firmament (Ez 1:19-21) ;
## 3. Dynamique Kuramoto stabilisée (K=0.04 FRAGMENTATION, K=0.28 COUPLAGE_JUSTE, K=2.50 CAPTURE) ;
## 4. Garde Yechidah refusant l'auto-tempo ("wheels" / "cherubs") et toute revendication de correspondance ("*").

@export var k_love: float = 0.28
@export var f_source_recall: float = 0.60
@export var omega_ruach: float = 0.42
@export var tempo_source: String = "above_firmament"
@export var active_scene: String = "Ez_1" # "Ez_1" ou "Ez_10"

const OMEGA_VIRTUES := {
	"humilite": 0.15,
	"pardon": 1.40,
	"gratitude": 0.06,
	"esperance": 0.65,
}

const FIXED_DIRECTIONS_RAD := [0.0, PI * 0.5, PI, PI * 1.5]

var cherub_phases: Array[float] = [0.1, 1.3, 2.8, 4.5]
var wheel_thetas: Array[float] = [0.2, 1.1, 2.4, 3.9]
var psi_tron: float = 0.0
var group_position: Vector3 = Vector3.ZERO
var group_velocity: Vector3 = Vector3(1.0, 0.0, 0.0)

func validate_yechidah(context_id: String, falsifier: String) -> Dictionary:
	if tempo_source == "wheels" or tempo_source == "cherubs":
		return {"ok": false, "reason": "auto_tempo_forbidden (M1)"}
	if context_id == "*" or falsifier.strip_edges() == "":
		return {"ok": false, "reason": "correspondence_claim_idolatry"}
	if k_love < 0.12:
		return {"ok": false, "reason": "couplage_trop_faible_fragmentation"}
	if k_love > 0.55:
		return {"ok": false, "reason": "couplage_trop_fort_capture"}
	return {"ok": true, "reason": "ok"}

func step_merkabah(dt: float) -> Dictionary:
	# Garde EXECUTABLE avant tout changement d'état : non seulement déclarée.
	if is_nan(dt) or is_inf(dt) or dt <= 0.0:
		return {"ok": false, "reason": "invalid_dt", "active_scene": active_scene}
	if active_scene != "Ez_1":
		# Ez 10 comporte une autre scène : ne pas la simuler par copie silencieuse.
		return {"ok": false, "reason": "scene_not_validated_for_motion", "active_scene": active_scene}
	var preflight: Dictionary = validate_yechidah(active_scene, "translation_corps_roues_et_arret_communs")
	if not preflight.get("ok", false):
		return {"ok": false, "reason": preflight.get("reason", "guard_rejected"), "active_scene": active_scene}
	# 1. Translation holonomique du groupe sans rotation de lacet des porteurs (Ez 1:12,17)
	group_position += group_velocity * dt
	psi_tron = fmod(psi_tron + omega_ruach * dt, TAU)

	# 2. Couplage entre porteurs (ailes jointes) avec rappel F vers la direction fixe propre
	var n := cherub_phases.size()
	var next_cherub_phases: Array[float] = []
	next_cherub_phases.resize(n)
	for i in range(n):
		var coupling := 0.0
		for j in range(n):
			if i != j:
				coupling += sin(cherub_phases[j] - cherub_phases[i])
		coupling *= (k_love / float(n - 1))
		var recall_own_dir := f_source_recall * sin(FIXED_DIRECTIONS_RAD[i] - cherub_phases[i])
		next_cherub_phases[i] = fmod(cherub_phases[i] + (coupling + recall_own_dir) * dt + TAU, TAU)
	cherub_phases = next_cherub_phases

	# 3. Transmission du ruach aux 4 roues (Ez 1:20 : ki ruach ha-chayah ba-ophannim)
	var virtues := ["humilite", "pardon", "gratitude", "esperance"]
	var next_thetas: Array[float] = []
	next_thetas.resize(n)
	for i in range(n):
		var w_coupling := 0.0
		for j in range(n):
			if i != j:
				w_coupling += sin(wheel_thetas[j] - wheel_thetas[i])
		w_coupling *= (k_love / float(n - 1))
		var forcing := 0.18 * sin(psi_tron - wheel_thetas[i])
		var om: float = OMEGA_VIRTUES[virtues[i]]
		next_thetas[i] = fmod(wheel_thetas[i] + (om + w_coupling + forcing) * dt + TAU, TAU)
	wheel_thetas = next_thetas

	# 4. Observation par Chayah (ordre de Kuramoto R sans décision d'autorité)
	var sum_cos := 0.0
	var sum_sin := 0.0
	for th in wheel_thetas:
		sum_cos += cos(th)
		sum_sin += sin(th)
	var r_order := sqrt(sum_cos * sum_cos + sum_sin * sum_sin) / float(n)
	var regime := "COUPLAGE_JUSTE"
	if r_order > 0.90:
		regime = "CAPTURE"
	elif r_order < 0.48:
		regime = "FRAGMENTATION"

	return {
		"ok": true,
		"group_position": [group_position.x, group_position.y, group_position.z],
		"cherub_yaw_rotation_delta": 0.0,
		"R": snapped(r_order, 0.001),
		"richness": snapped(1.0 - r_order, 0.001),
		"regime": regime,
		"active_scene": active_scene,
	}
