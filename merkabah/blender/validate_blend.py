"""Headless Blender structural check for the unvalidated Ezekiel 1 visual candidate.

Run from Blender: blender -b merkabah/blender/generated/merkabah_candidate.blend --python merkabah/blender/validate_blend.py
This is NOT a test of biblical fidelity or animated behavior.
"""
import bpy
import json
import sys

names = {obj.name for obj in bpy.data.objects}
failures = []
def require(condition, message):
    if not condition:
        failures.append(message)

for i in range(1, 5):
    prefix = f"cherub_{i}"
    require(f"{prefix}_body" in names, prefix + ": body missing")
    for face in ("human", "lion", "ox", "eagle"):
        require(f"{prefix}_face_{face}" in names, prefix + ": face " + face + " missing")
    for n in range(1, 5):
        require(f"{prefix}_wing_{n}" in names, prefix + ": wing " + str(n) + " missing")
    for s in (-1, 1):
        require(f"{prefix}_leg_{s}" in names, prefix + ": leg " + str(s) + " missing")
        require(f"{prefix}_foot_{s}" in names, prefix + ": foot " + str(s) + " missing")
        require(f"{prefix}_hand_{s}" in names, prefix + ": hand " + str(s) + " missing")
    for n in (1, 2):
        require(f"{prefix}_hand_frontback_{n}" in names, prefix + ": additional hand missing")
    for ring in ("outer", "inner"):
        require(f"{prefix}_{ring}_ring" in names, prefix + ": ring " + ring + " missing")
    for j in range(1, 13):
        require(f"{prefix}_symbolic_eye_{j}" in names, prefix + ": symbolic eye missing")

for name in ("expanse_placeholder", "throne_placeholder"):
    require(name in names, "Missing " + name)

scene = bpy.context.scene
require(scene.get("STATUS") == "PROPOSED_NOT_VALIDATED", "Candidate status changed")
require("ox" in scene.get("EZ10_14", "") and "cherub" in scene.get("EZ10_14", ""), "Verse distinction hidden")
require(scene.get("SCENE_RENDERED") == "EZEKIEL_1_ONLY", "Scene scope is not explicit")
require(scene.get("MOTION") == "TRANSLATION_ONLY_CANDIDATE", "Animation scope incorrect")
require(scene.get("WHEEL_INTERNAL_ROLLING") == "NOT_IMPLEMENTED", "Internal wheel rolling falsely claimed")
require(scene.frame_start == 1 and scene.frame_end == 121, "Unexpected animation range")

require(scene.get("EYES_EZ10_12") == "BODY_AND_WING_EYES_NOT_IMPLEMENTED", "Incomplete Ez10 eyes hidden")
require(len(names) == 130, f"Unexpected number of objects: {len(names)} vs 130")
# Motion audit: identity of all four rigid rigs, no turning and no wheel drift
positions = [(1,(0.0,0.0,0.0)),(31,(0.0,-2.0,0.0)),(61,(2.0,-2.0,0.0)),
             (91,(2.0,0.0,0.0)),(121,(0.0,0.0,0.0))]
initial_offsets = {}
for frame, expected in positions:
    scene.frame_set(frame)
    for i in range(1,5):
        prefix=f"cherub_{i}"
        rig=bpy.data.objects.get(prefix+"_rig")
        body=bpy.data.objects.get(prefix+"_body")
        wheel=bpy.data.objects.get(prefix+"_outer_ring")
        require(rig is not None, prefix+": rig missing")
        if rig is None or body is None or wheel is None: continue
        actual=rig.matrix_world.translation
        require(all(abs(actual[j]-expected[j]) < 1e-5 for j in range(3)),
                f"{prefix}: incorrect path at frame {frame}")
        require(all(abs(v) < 1e-5 for v in rig.rotation_euler),
                f"{prefix}: body turned at frame {frame}")
        offset=wheel.matrix_world.translation-body.matrix_world.translation
        if prefix not in initial_offsets: initial_offsets[prefix]=offset.copy()
        require((offset-initial_offsets[prefix]).length < 1e-5,
                f"{prefix}: wheel drift at frame {frame}")
scene.frame_set(1)

result = {"status": "FAIL" if failures else "PASS", "objects": len(names),
          "beings": 4, "faces": 16, "wings": 16, "wheel_assemblies": 4,
          "symbolic_eyes_on_wheels": 48,
          "scope": "EZEKIEL_1_ONLY, PROPOSED_NOT_VALIDATED",
          "motion": "TRANSLATION_ONLY_CANDIDATE", "sampled_frames": [1,31,61,91,121],
          "wheel_internal_rolling": "NOT_IMPLEMENTED", "errors": failures}
print("MERKABAH_BLENDER_AUDIT=" + json.dumps(result, sort_keys=True))
if failures:
    sys.exit(1)
