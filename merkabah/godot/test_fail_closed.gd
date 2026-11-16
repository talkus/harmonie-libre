extends SceneTree
## Test d'exécution Godot 4, candidat M5. Exécuter avec :
## godot --headless --path merkabah/godot --script res://test_fail_closed.gd
## Une réussite n'est PAS une preuve d'exégèse ou d'animation 3D.

func _initialize() -> void:
	call_deferred("_run")

func _fail(message: String) -> void:
	push_error(message)
	quit(1)

func _run() -> void:
	var sim = load("res://merkabah_42_godot_simulation.gd").new()
	get_root().add_child(sim)
	var initial_position: Vector3 = sim.group_position
	var initial_psi: float = sim.psi_tron
	sim.tempo_source = "wheels"
	var r: Dictionary = sim.step_merkabah(0.1)
	if r.get("ok", true) or sim.group_position != initial_position or sim.psi_tron != initial_psi:
		_fail("Tempo auto-produit n'a pas été bloqué avant mutation")
		return
	sim.tempo_source = "above_firmament"
	sim.k_love = 2.50
	r = sim.step_merkabah(0.1)
	if r.get("ok", true) or sim.group_position != initial_position:
		_fail("Couplage excessif non bloqué")
		return
	sim.k_love = 0.28
	sim.active_scene = "Ez_10"
	r = sim.step_merkabah(0.1)
	if r.get("ok", true) or sim.group_position != initial_position:
		_fail("Scène Ez 10 non validée n'a pas été bloquée")
		return
	sim.active_scene = "Ez_1"
	# Ruach absent : aucune phase et aucun déplacement ne progressent.
	sim.omega_ruach = 0.0
	var before_phases: Array[float] = sim.cherub_phases.duplicate()
	var before_wheels: Array[float] = sim.wheel_thetas.duplicate()
	r = sim.step_merkabah(0.1)
	if not r.get("ok", false) or not r.get("paused", false) or sim.group_position != initial_position or sim.psi_tron != initial_psi:
		_fail("Ruach nul : la scène n'est pas restée immobile")
		return
	if sim.cherub_phases != before_phases or sim.wheel_thetas != before_wheels:
		_fail("Ruach nul : les phases ont changé malgré la pause")
		return
	sim.omega_ruach = -1.0
	r = sim.step_merkabah(0.1)
	if r.get("ok", true) or sim.group_position != initial_position:
		_fail("Ruach négatif : non bloqué")
		return
	sim.omega_ruach = 0.42
	r = sim.step_merkabah(-0.1)
	if r.get("ok", true) or sim.group_position != initial_position:
		_fail("Durée négative non bloquée")
		return
	r = sim.step_merkabah(0.1)
	if not r.get("ok", false) or sim.group_position == initial_position:
		_fail("Simulation autorisée incorrecte")
		return
	if not is_equal_approx(float(r.get("cherub_yaw_rotation_delta", -1.0)), 0.0):
		_fail("Lacet de chérubin non nul")
		return
	print("MERKABAH GODOT M5: preflight et cas interdits PASS (logique uniquement)")
	sim.queue_free()
	quit(0)
