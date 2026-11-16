"""Prototype Blender schématique, NON VALIDÉ. blender --background --python merkabah_blender_candidate.py"""
import bpy, math
from pathlib import Path
from mathutils import Vector
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
def mat(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=color;return m
bronze=mat("bronze_interpretatif",(.65,.37,.11,1))
body=mat("corps_schematique",(.18,.3,.55,1))
wing=mat("ailes_schematiques",(.82,.87,.96,1))
eye=mat("yeux_symboliques",(.96,.82,.25,1))
face_mat=mat("faces_symboliques_non_realistes",(.7,.32,.28,1))
def sphere(name,loc,scale,material):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=loc)
 o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(material);return o
def limb(name,a,b,radius,material):
 a,b=Vector(a),Vector(b);d=b-a
 bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=radius,depth=d.length,location=(a+b)*.5)
 o=bpy.context.object;o.name=name;o.rotation_euler=d.to_track_quat("Z","Y").to_euler();o.data.materials.append(material);return o
def ring(name,loc,radius,minor,rotation,material):
 bpy.ops.mesh.primitive_torus_add(major_segments=48,minor_segments=8,location=loc,rotation=rotation,major_radius=radius,minor_radius=minor)
 o=bpy.context.object;o.name=name;o.data.materials.append(material)
for i,(x,y) in enumerate([(-3,-3),(3,-3),(3,3),(-3,3)],1):
 p=f"cherub_{i}"
 sphere(p+"_body",(x,y,1.6),(.5,.46,.8),body)
 for name,dx,dy in [("human",0,-.57),("lion",.57,0),("ox",0,.57),("eagle",-.57,0)]:
  sphere(p+"_face_"+name,(x+dx,y+dy,2.12),(.2,.2,.25),face_mat)
 for k,dx,dy in [(1,-.75,-.65),(2,.75,-.65),(3,-.75,.65),(4,.75,.65)]:
  limb(p+f"_wing_{k}",(x,y,1.95),(x+dx,y+dy,2.65),.15,wing)
 for s in [-1,1]:
  limb(p+f"_leg_{s}",(x+s*.25,y,1.15),(x+s*.25,y,.45),.14,bronze)
  sphere(p+f"_foot_{s}",(x+s*.25,y-.10,.35),(.24,.20,.12),bronze)
  sphere(p+f"_hand_{s}",(x+s*.49,y,1.58),(.13,.13,.13),bronze)
 for hand_idx,(dx,dy) in enumerate([(0,-.5),(0,.5)],1):
  sphere(p+f"_hand_frontback_{hand_idx}",(x+dx,y+dy,1.58),(.13,.13,.13),bronze)
 wx,wy,wz=x+1.35,y,1.0
 ring(p+"_outer_ring",(wx,wy,wz),.82,.09,(math.pi/2,0,0),bronze)
 ring(p+"_inner_ring",(wx,wy,wz),.68,.08,(0,math.pi/2,0),bronze)
 for j in range(12):
  a=2*math.pi*j/12
  sphere(p+f"_symbolic_eye_{j+1}",(wx+.82*math.cos(a),wy,wz+.82*math.sin(a)),(.075,.075,.075),eye)
 # The whole being and its adjacent wheel form one translating rig.
 # This path is illustrative and adds NO rotation to the being.
 rig = bpy.data.objects.new(p+"_rig", None)
 bpy.context.collection.objects.link(rig)
 for obj in list(bpy.data.objects):
  if obj is not rig and obj.name.startswith(p+"_"):
   obj.parent = rig
 for frame,offset in [(1,(0,0,0)),(31,(0,-2,0)),(61,(2,-2,0)),(91,(2,0,0)),(121,(0,0,0))]:
  rig.location = offset
  rig.keyframe_insert(data_path="location",frame=frame,group="Translation_only_candidate")
 if rig.animation_data and rig.animation_data.action:
  for curve in rig.animation_data.action.fcurves:
   for key in curve.keyframe_points:
    key.interpolation = 'LINEAR'
 rig.location = (0,0,0)
for name,loc,scale,material in [
 ("expanse_placeholder",(0,0,3.8),(8,8,.04),wing),
 ("throne_placeholder",(0,0,5.1),(1.6,1,.3),body)]:
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
 o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(material)
bpy.context.scene["STATUS"]="PROPOSED_NOT_VALIDATED"
bpy.context.scene["EZ10_14"]="UNCERTAIN: Ez 10:14 lists cherub, human, lion, eagle; Ez 1:10 lists human, lion, ox, eagle. Do not infer identity."
bpy.context.scene["MOTION"]="TRANSLATION_ONLY_CANDIDATE"
bpy.context.scene["WHEEL_INTERNAL_ROLLING"]="NOT_IMPLEMENTED"
bpy.context.scene.frame_start=1
bpy.context.scene.frame_end=121
bpy.context.scene.frame_set(1)
bpy.context.scene["SCENE_RENDERED"]="EZEKIEL_1_ONLY"
bpy.context.scene["EYES_EZ10_12"]="BODY_AND_WING_EYES_NOT_IMPLEMENTED"
bpy.context.scene["GEOMETRIC_STATUS"]="INTERPRETATION; sizes and face placements illustrative"
bpy.context.scene["WARNING"]="Primitive layout and orientation are illustrative, not proven by biblical text"
out = Path(__file__).resolve().parent / "generated" / "merkabah_candidate.blend"
out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out))
print("MERKABAH: draft 3D + translating rigs saved at "+str(out)+"; no internal wheel rolling and NO exegetical validation")
