"""Turn a Meshy rigged character (GLB with skeleton) into a chars3d/<who>.blend usable by anim3d.Char3D.

blender -b -P meshy_char.py -- <who> <rigged.glb> <height in metres> [expr=texture.png ...]

The Meshy skeleton is kept (hands, toes, neck, shoulders stay as passive bones); the bones anim3d drives are
renamed to its names, their tails are put on the next joint, and the model is scaled to the given height with
the feet on the ground, facing -Y. Extra textures on the same UVs become switchable expressions (EXPR_<name>).
"""
import bpy, sys, os
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:]
who, src, height = argv[0], argv[1], float(argv[2])
exprs = dict(a.split("=", 1) for a in argv[3:])
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chars3d")

NAMES = {"Hips": "hips", "Spine01": "spine", "Head": "head",
         "LeftArm": "upper_arm.L", "LeftForeArm": "forearm.L", "RightArm": "upper_arm.R", "RightForeArm": "forearm.R",
         "LeftUpLeg": "thigh.L", "LeftLeg": "shin.L", "LeftFoot": "foot.L",
         "RightUpLeg": "thigh.R", "RightLeg": "shin.R", "RightFoot": "foot.R"}
NEXT = {"Hips": "Spine02", "Spine02": "Spine01", "Spine01": "Spine", "Spine": "neck", "neck": "Head", "Head": "head_end"}
for s, S in (("Left", "L"), ("Right", "R")):
    NEXT.update({s + "Shoulder": s + "Arm", s + "Arm": s + "ForeArm", s + "ForeArm": s + "Hand",
                 s + "UpLeg": s + "Leg", s + "Leg": s + "Foot", s + "Foot": s + "ToeBase"})

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
ob = next(o for o in bpy.data.objects if o.type == "MESH" and o.parent == arm)
for o in list(bpy.data.objects):
    if o not in (arm, ob):
        bpy.data.objects.remove(o)
if arm.animation_data:
    arm.animation_data_clear()
for pb in arm.pose.bones:
    pb.matrix_basis = Matrix()

# --- bring everything into metres, feet on the ground, hips over the origin
mw = arm.matrix_world.copy()
pts = [mw @ ob.matrix_local @ v.co for v in ob.data.vertices]
zmin = min(p.z for p in pts); zmax = max(p.z for p in pts)
hip = mw @ arm.data.bones["Hips"].head_local
k = height / (zmax - zmin)
M = Matrix.Scale(k, 4) @ Matrix.Translation((-hip.x, -hip.y, -zmin))
ob.data.transform(M @ mw @ ob.matrix_local)
ob.matrix_local = Matrix()
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
eb = arm.data.edit_bones
heads = {b.name: (M @ mw @ b.head) for b in eb}
tails = {b.name: (M @ mw @ b.tail) for b in eb}
for b in eb:
    b.use_connect = False
for b in eb:
    b.head = heads[b.name]
    n = NEXT.get(b.name)
    if n and n in heads:
        b.tail = heads[n]
    else:
        d = (tails[b.name] - heads[b.name]).normalized()
        b.tail = heads[b.name] + d * 0.04 * height
for b in eb:
    if b.name in NAMES:
        b.name = NAMES[b.name]
bpy.ops.object.mode_set(mode="OBJECT")
arm.matrix_world = Matrix()
arm.name = who + "_rig"; ob.name = who + "_body"
for p in ob.data.polygons:
    p.use_smooth = True

# --- material: the model's own texture (+ optional expression textures on the same UVs)
old = ob.data.materials[0]
base = next(n.image for n in old.node_tree.nodes if n.type == "TEX_IMAGE" and n.image and "normal" not in n.image.name
            and "rough" not in n.image.name)
fn = os.path.join(OUT, who + "_tex.png")
base.filepath_raw = fn; base.file_format = "PNG"; base.save()
final = bpy.data.materials.new(who + "_mat")
final.use_nodes = True
nt = final.node_tree
p = nt.nodes["Principled BSDF"]


def tex(path):
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(path)
    t.interpolation = "Cubic"
    return t


cur = tex(fn).outputs["Color"]
for ex, path in exprs.items():
    t = tex(path)
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = "RGBA"; mx.name = "EXPR_" + ex
    mx.inputs["Factor"].default_value = 0.0
    nt.links.new(cur, mx.inputs[6]); nt.links.new(t.outputs["Color"], mx.inputs[7])
    cur = mx.outputs[2]
hs = nt.nodes.new("ShaderNodeHueSaturation")
hs.name = "VIVID"
hs.inputs["Saturation"].default_value = 1.1
nt.links.new(cur, hs.inputs["Color"])
nt.links.new(hs.outputs["Color"], p.inputs["Base Color"])
p.inputs["Roughness"].default_value = 0.6
p.inputs["Specular IOR Level"].default_value = 0.25
ob.data.materials.clear()
ob.data.materials.append(final)

sc = bpy.context.scene
col = bpy.data.collections.new(who)
sc.collection.children.link(col)
for o in (arm, ob):
    for c0 in list(o.users_collection):
        c0.objects.unlink(o)
    col.objects.link(o)
for c0 in list(bpy.data.collections):
    if c0 is not col:
        bpy.data.collections.remove(c0)
bs = arm.data.bones
print("H", round(max(v.co.z for v in ob.data.vertices), 3), "leg", round(bs["thigh.L"].length + bs["shin.L"].length, 3),
      "faces", len(ob.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, who + ".blend"))
