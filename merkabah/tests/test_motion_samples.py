"""Counterexamples for sampled motion, with an explicitly chosen fixed offset."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from validate_motion_samples import validate_motion  # noqa: E402

IDENTITY = [1, 0, 0, 0]
PAIRS = [(f"being_{i}", f"wheel_{i}") for i in range(1, 5)]


def frame(t, offset):
    objects = {}
    for i, (being, wheel) in enumerate(PAIRS):
        objects[being] = {"position": [i + offset[0], offset[1], offset[2]], "orientation": IDENTITY[:]}
        objects[wheel] = {"position": [i + offset[0] + 0.4, offset[1], offset[2]]}
    return {"time": t, "objects": objects}


class MotionTests(unittest.TestCase):
    def setUp(self):
        self.frames = [frame(0, (0, 0, 0)), frame(1, (2, 0, 0)), frame(2, (2, 0, 3)), frame(3, (2, 0, 3))]

    def test_translation_lift_and_stop(self):
        self.assertEqual(validate_motion(self.frames, PAIRS), [])

    def test_one_detached_wheel_fails(self):
        self.frames[1]["objects"]["wheel_2"]["position"][0] += 0.5
        self.assertTrue(any("wheel_2 not synchronized" in x for x in validate_motion(self.frames, PAIRS)))

    def test_one_being_turns_fails(self):
        self.frames[1]["objects"]["being_1"]["orientation"] = [0, 0, 0, 1]
        self.assertTrue(any("being_1 changed orientation" in x for x in validate_motion(self.frames, PAIRS)))

    def test_quaternion_sign_does_not_imply_rotation(self):
        self.frames[1]["objects"]["being_1"]["orientation"] = [-1, 0, 0, 0]
        self.assertEqual(validate_motion(self.frames, PAIRS), [])

    def test_missing_wheel_is_not_success(self):
        del self.frames[1]["objects"]["wheel_3"]
        self.assertTrue(any("wheel_3: invalid position" in x for x in validate_motion(self.frames, PAIRS)))

    def test_single_frame_is_not_success(self):
        self.assertTrue(validate_motion(self.frames[:1], PAIRS))

    def test_bad_timestamp_is_not_success(self):
        self.frames[1]["time"] = 0
        self.assertTrue(any("time must increase" in x for x in validate_motion(self.frames, PAIRS)))

    def test_duplicate_pair_is_not_success(self):
        self.assertTrue(validate_motion(self.frames, PAIRS + [PAIRS[0]]))

    def test_wheel_and_being_cannot_be_same_object(self):
        self.assertTrue(validate_motion(self.frames, [("being_1", "being_1")]))


if __name__ == "__main__":
    unittest.main()
