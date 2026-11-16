"""Contrôles STATIQUES du préflight Godot, sans exécution du moteur.
Tests comportementaux dans godot/test_fail_closed.gd : non exécutés par Python.
"""
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "godot" / "merkabah_42_godot_simulation.gd"

class TestGodotPreflightStatic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = SCRIPT.read_text(encoding="utf-8")
        cls.step = cls.src.split("func step_merkabah(dt: float) -> Dictionary:", 1)[1]

    def test_gate_before_position_mutation(self):
        gate = self.step.index("validate_yechidah(active_scene")
        change = self.step.index("group_position += ")
        self.assertLess(gate, change)
        self.assertIn('if not preflight.get("ok", false):', self.step[:change])

    def test_reject_invalid_scene_and_dt_before_mutation(self):
        change = self.step.index("group_position += ")
        prefix = self.step[:change]
        self.assertIn('active_scene != "Ez_1"', prefix)
        self.assertIn('dt <= 0.0', prefix)

    def test_result_has_explicit_success_indicator(self):
        self.assertIn('"ok": true', self.step)
        self.assertIn('"ok": false', self.step)

    def test_preserves_separate_motion_and_coupling_states(self):
        self.assertIn('group_position += group_velocity * dt', self.step)
        self.assertIn('cherub_yaw_rotation_delta": 0.0', self.step)
        self.assertIn('w_coupling', self.step)

if __name__ == "__main__":
    unittest.main()
