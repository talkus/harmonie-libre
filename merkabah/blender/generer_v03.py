"""Build a schematic, inspectable prototype from a scene of the candidate graph.

Run: blender -b --factory-startup --python-exit-code 1 --python generer_modele.py
Optional scene: -- --scene ez10. No network, source mutations or animation.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
GRAPH_PATH = ROOT.parent / "schema" / "merkabah_candidate_v0.3.json"
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if args and (len(args) != 2 or args[0] != "--scene" or args[1] not in {"ez1", "ez10"}):
    raise ValueError("Utiliser -- --scene ez1 ou -- --scene ez10")
chapter = args[1] if args else "ez1"
OUT = ROOT / "generated"
OUT.mkdir(exist_ok=True)
raw = GRAPH_PATH.read_bytes()
graph = json.loads(raw)
nodes = {node["id"]: node for node in graph["nodes"]}
if len(nodes) != len(graph["nodes"]):
    raise ValueError("Graph has duplicate node ids")
for edge in graph["edges"]:
    if edge["from"] not in nodes or edge["to"] not in nodes:
        raise ValueError("Graph edge references a missing node")

beings = sorted(n["id"] for n in graph["nodes"]
                if n["type"] == "living_being" and n["scene"] == chapter)
if len(beings) != 4:
    raise ValueError(f"Expected four living beings in {chapter}, got {len(beings)}")

def related(source, relation):
    return [nodes[e["to"]] for e in graph["edges"]
            if e["from"] == source and e["type"] == relation]

for being in beings:
    faces = related(being, "has_face")
    wings = related(being, "has_wing")
    wheels = related(being, "beside")
    expected_faces = {"human", "lion", "ox", "eagle"} if chapter == "ez1" else {"human", "lion", "cherub", "eagle"}
    if {f.get("form") for f in faces} != expected_faces or len(faces) != 4:
        raise ValueError(f"Incorrect face relations: {being}")
    if len(wings) != 4 or any(w["type"] != "wing" for w in wings):
        raise ValueError(f"Incorrect wing relations: {being}")
    if len(wheels) != 1 or wheels[0]["type"] != "wheel":
        raise ValueError(f"Incorrect wheel relation: {being}")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for collection in list(bpy.data.collections):
    if collection.name != "Collection" and collection.users == 0:
        bpy.data.collections.remove(collection)

scene = bpy.context.scene
scene.name = "Prototype_" + chapter
scene["qualification"] = "PROTOTYPE_SCHEMATIQUE_NON_VALIDE"
scene["graph_sha256"] = hashlib.sha256(raw).hexdigest()
scene["limitations"] = (
    "Placement et apparence interpretes; yeux symboliques; pas de mouvement "
    "ni de mains/jambes explicites; le graphe reste candidat non valide."
)

def material(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    return m

body_mat = material("corps ivoire", (0.72, 0.66, 0.53))
wing_top = material("ailes hautes bleu", (0.15, 0.42, 0.69))
wing_low = material("ailes basses cyan", (0.16, 0.62, 0.67))
wheel_mat = material("roues cuivre", (0.86, 0.53, 0.16))
eye_mat = material("yeux symboliques or", (0.98, 0.85, 0.32))
face_mat = {
    "human": material("face humain", (0.80, 0.37, 0.22)),
    "lion": material("face lion", (0.95, 0.71, 0.19)),
    "ox": material("face boeuf", (0.37, 0.67, 0.40)),
    "cherub": material("face cherubin symbolique", (0.27, 0.72, 0.56)),
    "eagle": material("face aigle", (0.60, 0.39, 0.78)),
}
label_mat = material("texte clair", (0.95, 0.95, 0.92))
expanse_mat = material("etendue", (0.22, 0.64, 0.80))
throne_mat = material("trone", (0.19, 0.31, 0.71))
light_mat = material("eclat", (1.0, 0.85, 0.45))

def tag(obj, node_id, role):
    obj["graph_node"] = node_id
    obj["graph_source"] = json.dumps(nodes[node_id].get("references", []), ensure_ascii=False)
    obj["role"] = role
    obj["position_qualification"] = "CHOIX_SCHEMATIQUE"
    return obj

def assign(obj, mat, parent=None):
    obj.data.materials.append(mat)
    if parent:
        obj.parent = parent
    return obj

def sphere(name, loc, scale, mat, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    return assign(obj, mat, parent)

def cube(name, loc, scale, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    return assign(obj, mat)

def torus(name, loc, radius, thickness, rot, mat, parent=None):
    bpy.ops.mesh.primitive_torus_add(major_segments=32, minor_segments=8,
        location=loc, rotation=rot, major_radius=radius, minor_radius=thickness)
    obj = bpy.context.object
    obj.name = name
    return assign(obj, mat, parent)

def face_label(name, label, location, rotation, parent):
    curve = bpy.data.curves.new(name + "_curve", "FONT")
    curve.body = label
    curve.size = 0.17
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.extrude = 0.002
    obj = bpy.data.objects.new(name, curve)
    scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    assign(obj, label_mat, parent)
    # Text meshes remain visible when exporting glTF.
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    return bpy.context.object

def wing(name, origin, signx, signy, raised, mat, parent):
    x, y, z = origin
    bend = 0.55 if raised else -0.25
    vertices = [
        (x + signx*0.15, y + signy*0.11, z + 0.40),
        (x + signx*0.25, y + signy*0.20, z + 0.95),
        (x + signx*1.25, y + signy*0.63, z + 1.0 + bend),
        (x + signx*1.12, y + signy*0.82, z + 0.42 + bend),
    ]
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    return assign(obj, mat, parent)

placements = [(-3.1, -3.1, 0.0), (3.1, -3.1, 0.0),
              (-3.1, 3.1, 0.0), (3.1, 3.1, 0.0)]
face_configs = {
    "human": ((0, -0.48, 1.48), (0.31, 0.12, 0.31),
              (0, -0.615, 1.48), (math.pi/2, 0, 0), "HUMAIN"),
    "lion": ((0.48, 0, 1.48), (0.12, 0.31, 0.31),
             (0.615, 0, 1.48), (math.pi/2, 0, math.pi/2), "LION"),
    "ox": ((-0.48, 0, 1.48), (0.12, 0.31, 0.31),
           (-0.615, 0, 1.48), (math.pi/2, 0, -math.pi/2), "BOEUF"),
    "cherub": ((-0.48, 0, 1.48), (0.12, 0.31, 0.31),
               (-0.615, 0, 1.48), (math.pi/2, 0, -math.pi/2), "CHERUBIN"),
    "eagle": ((0, 0.48, 1.48), (0.31, 0.12, 0.31),
              (0, 0.615, 1.48), (math.pi/2, 0, math.pi), "AIGLE"),
}

for being, center in zip(beings, placements):
    x, y, z = center
    holder = bpy.data.objects.new(being + "_assembly", None)
    scene.collection.objects.link(holder)
    holder["interpretation"] = "Assemblage graphique non anime"
    body = tag(sphere(being, (x,y,z+0.90), (0.43,0.43,0.70), body_mat, holder),
               being, "living_being")
    face_label("label_" + being, being.upper().replace("_", " "),
               (x,y-0.48,z+0.55), (math.pi/2,0,0), holder)
    for face in related(being, "has_face"):
        offset, scale, label_offset, rot, label = face_configs[face["form"]]
        loc = tuple(center[i] + offset[i] for i in range(3))
        face_obj = tag(sphere(face["id"], loc, scale, face_mat[face["form"]], holder),
                       face["id"], "face")
        face_obj["form"] = face["form"]
        face_label("label_" + face["id"], label,
                   tuple(center[i]+label_offset[i] for i in range(3)), rot, holder)
    for n, wing_node in enumerate(sorted(related(being, "has_wing"), key=lambda item:item["id"])):
        sx, sy, raised = [(1,-1,True),(-1,-1,True),(1,1,False),(-1,1,False)][n]
        tag(wing(wing_node["id"], center, sx, sy, raised,
                 wing_top if raised else wing_low, holder), wing_node["id"], "wing")
    wheel_id = related(being, "beside")[0]["id"]
    wx, wy, wz = x+1.67, y, z+0.85
    wheel = bpy.data.objects.new(wheel_id, None)
    scene.collection.objects.link(wheel)
    wheel.parent = holder
    tag(wheel, wheel_id, "wheel")
    torus(wheel_id+"_outer", (wx,wy,wz), .75, .08, (math.pi/2,0,0), wheel_mat, wheel)
    torus(wheel_id+"_inner", (wx,wy,wz), .69, .07, (0,math.pi/2,0), wheel_mat, wheel)
    # Eight markers are a visual convention, not a statement of eye count.
    for n in range(8):
        a = n * math.tau / 8
        sphere(wheel_id+f"_eye_{n+1}", (wx+.75*math.cos(a),wy-.08,wz+.75*math.sin(a)),
               (.08,.06,.08), eye_mat, wheel)

# Expanse and throne are deliberately abstract, not proposed as reconstructions.
tag(torus("expanse", (0,0,3.0), 4.6, .08, (0,0,0), expanse_mat), chapter + "_expanse", "expanse")
tag(cube("throne", (0,0,3.65), (1.25,.85,.40), throne_mat), chapter + "_throne", "throne")

roles = [o.get("role") for o in bpy.data.objects]
counts = {key: roles.count(key) for key in ("living_being","face","wing","wheel")}
if counts != {"living_being":4,"face":16,"wing":16,"wheel":4}:
    raise RuntimeError(f"Object counts do not match graph: {counts}")
for node in graph["nodes"]:
    if node["scene"] == chapter and node["type"] in {"living_being","face","wing","wheel"}:
        matches = [o for o in bpy.data.objects if o.get("graph_node")==node["id"]]
        if len(matches) != 1:
            raise RuntimeError(f"Missing/duplicate graph object: {node['id']}")

scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.light = "STUDIO"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.background_type = "WORLD"
scene.world.color = (0.035, 0.045, 0.065)
scene.render.resolution_x = 1000
scene.render.resolution_y = 760
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"

def camera(name, location, target, scale):
    data = bpy.data.cameras.new(name)
    data.type = "ORTHO"
    data.ortho_scale = scale
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj

scene.camera = camera("Camera_Vue_Ensemble", (11,-15,11), (0,0,1.65), 15.3)
scene.render.filepath = str(OUT / ("vue_ensemble_" + chapter + ".png"))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / ("merkabah_" + chapter + "_schema.blend")))
bpy.ops.export_scene.gltf(filepath=str(OUT / ("merkabah_" + chapter + "_schema.glb")), export_format="GLB")
bpy.ops.render.render(write_still=True)

report = {
    "status":"PROTOTYPE_SCHEMATIQUE_NON_VALIDE",
    "scene": chapter,
    "graph_sha256":hashlib.sha256(raw).hexdigest(),
    "graph_nodes":len(nodes), "graph_edges":len(graph["edges"]),
    "object_counts":counts,
    "limitations":[
        "Positions et apparences sont des choix graphiques, non des faits bibliques.",
        "Les yeux sont symbolises par huit marqueurs par roue, sans pretention de nombre.",
        "Ni animation, ni mains/jambes explicites; scènes simplifiées et non vérifiées visuellement sous tous les angles.",
        "Pas de preuve que deux ailes se touchent ni que les roues se deplacent correctement.",
    ],
}
(OUT / ("rapport_structure_" + chapter + ".json")).write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
print("MERKABAH_STRUCTURAL_REPORT", json.dumps(report, ensure_ascii=False))

