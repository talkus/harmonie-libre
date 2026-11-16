"""Merkabah candidate movement invariants: synthetic paths, NOT scriptural validation."""
import math
import unittest

def translation(start, delta, facing):
    """Move without changing the four face orientations."""
    pos = tuple(a + b for a, b in zip(start, delta))
    return pos, tuple(facing)

def synchronized_step(beings, wheels, delta):
    """Wheels remain rigidly offset from their matched carriers."""
    assert len(beings) == len(wheels) == 4
    new_beings = []
    new_wheels = []
    for (bpos, facing), wpos in zip(beings, wheels):
        moved, orientation = translation(bpos, delta, facing)
        new_beings.append((moved, orientation))
        new_wheels.append(tuple(a + d for a, d in zip(wpos, delta)))
    return new_beings, new_wheels

class TestMovementCandidate(unittest.TestCase):
    def setUp(self):
        self.positions = [(-3,-3,0),(3,-3,0),(3,3,0),(-3,3,0)]
        self.faces = (0, math.pi / 2, math.pi, 3 * math.pi / 2)
        self.beings = [(p, self.faces) for p in self.positions]
        self.wheels = [(x+1.35,y,z) for x,y,z in self.positions]

    def test_motion_preserves_face_orientation(self):
        moved,_ = synchronized_step(self.beings,self.wheels,(1,2,0.5))
        self.assertEqual([f for _,f in moved],[self.faces]*4)

    def test_motion_preserves_each_wheel_offset(self):
        moved,wheels=synchronized_step(self.beings,self.wheels,(1,2,0.5))
        for (p,_),w in zip(moved,wheels):
            self.assertEqual(tuple(round(b-a,8) for a,b in zip(p,w)),(1.35,0,0))

    def test_motion_reversible(self):
        moved,wheels=synchronized_step(self.beings,self.wheels,(2,1,-0.5))
        restored,original_wheels=synchronized_step(moved,wheels,(-2,-1,0.5))
        self.assertEqual(restored,self.beings)
        self.assertEqual(original_wheels,self.wheels)

    def test_individual_changing_direction_does_not_require_turning(self):
        group,w=synchronized_step(self.beings,self.wheels,(0,2,0))
        group2,_=synchronized_step(group,w,(-3,0,0))
        self.assertEqual([f for _,f in group2],[self.faces]*4)

if __name__ == "__main__":
    unittest.main()
