"""Merkabah PROTOTYPE — schematic Blender geometry (not a faithful portrait).

Run: blender --background --python merkabah/blender/build_schematic.py
Produces four distinct marker beings and four adjacent wheel pairs, plus stage.
Intentionally uses labeled proxy geometry, NOT anatomical cherubim or faces.
Never present this as finished Ezekiel 1/10 reconstruction.
"""
import bpy
import math
from mathutils import Vector

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def material(name, color):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    return m

bronze=material("bronze_proxy",(0.55,0.34,0.12))
crystal=material("crystal_proxy",(0.24,0.58,0.72))
wheel_mat=material("wheel_proxy",(0.47,0.65,0.86))

def sphere(name, loc, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=loc)
    ob=bpy.context.object;ob.name=name;ob.scale=scale;ob.data.materials.append(mat)
    return ob

def torus(name, loc, rotation, major=0.9, minor=0.045):
    bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,location=loc,rotation=rotation)
    ob=bpy.context.object;ob.name=name;ob.data.materials.append(wheel_mat)
    return ob

# The XY layout is an EXPLICIT visual hypothesis, not a textual assertion.
centers=[(-3.0,-3.0),(3.0,-3.0),(-3.0,3.0),(3.0,3.0)]
face_labels=["human","lion","ox","eagle"]
offsets=[(0,-0.48,0),(0.48,0,0),(0,0.48,0),(-0.48,0,0)]
for idx,(x,y) in enumerate(centers,1):
    sphere(f"C{idx}_body_PROXY",(x,y,1.4),(.38,.33,.7),bronze)
    sphere(f"C{idx}_head_CORE_PROXY",(x,y,2.35),(.32,.32,.32),bronze)
    for face,(dx,dy,dz) in zip(face_labels,offsets):
        sphere(f"C{idx}_face_{face}_MARKER",(x+dx,y+dy,2.35+dz),(.14,.14,.14),crystal)
    for wing in range(4):
        angle=wing*math.pi/2
        sphere(f"C{idx}_wing_{wing+1}_PROXY",
               (x+0.73*math.cos(angle),y+0.73*math.sin(angle),1.85),
               (.64,.10,.24),bronze).rotation_euler[2]=angle
    # Two orthogonal wheel rings are proxies for wheel-within-wheel; geometry disputed.
    wx=x+1.15; wy=y
    torus(f"W{idx}_ring_A_PROXY",(wx,wy,0.95),(math.pi/2,0,0))
    torus(f"W{idx}_ring_B_PROXY",(wx,wy,0.95),(0,math.pi/2,0))
    for j in range(12):
        a=2*math.pi*j/12
        sphere(f"W{idx}_eye_marker_{j+1}",(wx+.89*math.cos(a),wy,0.95+.89*math.sin(a)),
               (.055,.055,.055),bronze)

bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,3.35))
plane=bpy.context.object;plane.name="EXPANSE_PROXY";plane.scale=(8.5,8.5,.07)
plane.data.materials.append(crystal)
sphere("THRONE_PROXY",(0,0,4.25),(0.8,0.6,0.4),crystal)
sphere("RADIANCE_PROXY",(0,0,5.1),(.3,.3,.75),bronze)
bpy.ops.wm.save_as_mainfile(filepath="/tmp/merkabah_schematic_candidate.blend")
print("SCHEMATIC_ONLY; no fidelity certification")
