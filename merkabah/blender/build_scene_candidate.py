"""Merkabah — maquette géométrique Blender, NON validation biblique.
Usage: blender --background --python merkabah/blender/build_scene_candidate.py
Lit le JSON v0.3 et refuse les cardinalités erronées.
Les silhouettes et formes sont des marqueurs abstraits, PAS un rendu fidèle.
"""
import bpy
import json
from pathlib import Path
from math import radians
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "schema" / "merkabah_candidate_v0.3.json"
OUT = ROOT / "blender" / "merkabah_candidate_v03.blend"
g = json.loads(DATA.read_text(encoding="utf-8"))
nodes = {n["id"]: n for n in g["nodes"]}
edges = g["edges"]

def targets(node, kind):
    return [e["to"] for e in edges if e["from"] == node and e["type"] == kind]

assert g["status"] == "PROPOSED_NOT_VALIDATED"
assert len(nodes) == len(g["nodes"])
assert sum(n["type"] == "living_being" for n in nodes.values()) == 4
assert sum(n["type"] == "wheel_within_wheel" for n in nodes.values()) == 4
for i in range(1, 5):
    c = f"cherub_{i}"
    assert len(targets(c, "has_face")) == 4
    assert len(targets(c, "has_wing")) == 4
    assert targets(c, "beside") == [f"wheel_{i}"]
    assert targets(f"wheel_{i}", "moves_with") == [c]

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def cube(name, location, scale, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    ob = bpy.context.object
    ob.name = name
    ob.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if parent:
        ob.parent = parent
        ob.matrix_parent_inverse = parent.matrix_world.inverted()
    return ob

def sphere(name, location, radius, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=radius, location=location)
    ob = bpy.context.object
    ob.name = name
    if parent:
        ob.parent = parent
        ob.matrix_parent_inverse = parent.matrix_world.inverted()
    return ob

def torus(name, location, major, minor, orientation, parent=None):
    bpy.ops.mesh.primitive_torus_add(major_segments=32, minor_segments=8, location=location,
                                    major_radius=major, minor_radius=minor,
                                    rotation=orientation)
    ob = bpy.context.object
    ob.name = name
    if parent:
        ob.parent = parent
        ob.matrix_parent_inverse = parent.matrix_world.inverted()
    return ob

positions = [(-3, -3, 0), (3, -3, 0), (-3, 3, 0), (3, 3, 0)]
headings = [(0, -1, 0), (1, 0, 0), (0, 1, 0), (-1, 0, 0)]
for index, (x, y, _) in enumerate(positions, 1):
    root = bpy.data.objects.new(f"cherub_{index}_ROOT", None)
    bpy.context.collection.objects.link(root)
    root.location = (x, y, 0)
    cube(f"cherub_{index}_BODY_ABSTRACT", (x, y, 1.7), (0.9, 0.9, 2.0), root)
    for j, form in enumerate(("human", "lion", "ox", "eagle")):
        dx, dy, dz = headings[j]
        sphere(f"cherub_{index}_face_{form}_PLACEHOLDER", (x + dx*0.68, y + dy*0.68, 2.65), 0.3, root)
    for j, (dx,dy) in enumerate(((-1,-1),(1,-1),(-1,1),(1,1)), 1):
        cube(f"cherub_{index}_wing_{j}_PLACEHOLDER",
             (x + dx*0.7, y + dy*0.7, 2.25), (0.9,0.18,0.1), root)
    cube(f"cherub_{index}_legs_PLACEHOLDER", (x,y,0.55), (0.25,0.25,0.9), root)
    cube(f"cherub_{index}_feet_PLACEHOLDER", (x,y,0.08), (0.55,0.55,0.16), root)
    cube(f"cherub_{index}_hands_PLACEHOLDER", (x,y-0.62,1.35), (0.5,0.15,0.12), root)
    wx = x + 1.55
    wheel_root = bpy.data.objects.new(f"wheel_{index}_ROOT_FOLLOWS_CHERUB", None)
    bpy.context.collection.objects.link(wheel_root)
    wheel_root.location = (wx,y,1.0)
    # Deux anneaux orthogonaux: approximation pédagogique, forme non déterminée.
    torus(f"wheel_{index}_ring_A_PLACEHOLDER", (wx,y,1.0), 0.68,0.065,(radians(90),0,0),wheel_root)
    torus(f"wheel_{index}_ring_B_PLACEHOLDER", (wx,y,1.0), 0.68,0.065,(0,radians(90),0),wheel_root)
    for j in range(8):
        from math import sin, cos, pi
        a = j * 2*pi/8
        sphere(f"wheel_{index}_eye_{j+1}_SYMBOLIC", (wx+0.68*cos(a),y,1+0.68*sin(a)),0.07,wheel_root)
    # Déplacement couplé sans changement d'orientation de chaque chérubin.
    for frame, offset in ((1,0.0),(48,1.0),(96,0.0)):
        root.location = (x,y+offset,0)
        wheel_root.location = (wx,y+offset,1.0)
        root.keyframe_insert(data_path="location",frame=frame)
        wheel_root.keyframe_insert(data_path="location",frame=frame)

cube("expanse_ABSTRACT", (0,0,4.3), (10,10,0.12))
cube("throne_ABSTRACT", (0,0,5.3), (1.8,1.3,0.7))
bpy.context.scene.frame_start=1
bpy.context.scene.frame_end=96
bpy.context.scene.render.fps=24
OUT.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
print("MERKABAH_CANDIDATE_SCENE_SAVED",OUT)
print("LIMITS: abstract placeholders; faces orientation conjectural; Ez10 divergence unresolved; not validated")
