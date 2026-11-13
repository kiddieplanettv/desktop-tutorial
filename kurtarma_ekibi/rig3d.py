"""Turn a Hunyuan3D-2mv shape (.glb) + the user's character-sheet views into a textured, rigged Blender character.

blender -b -P rig3d.py -- <who> <shape.glb> <height_m> <front> <back> <left(+X camera)> <right(-X camera)>
Writes chars3d/<who>.blend (collection '<who>' with armature '<who>_rig' and mesh '<who>_body').
"""
import bpy, bmesh, sys, os, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
who, glb, H = argv[0], argv[1], float(argv[2])
vF, vB, vXp, vXn = argv[3:7]
HERE = os.path.dirname(os.path.abspath(__file__))
VIEWS = os.path.join(HERE, "chars2", who)
OUT = os.path.join(HERE, "chars3d")
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
for o in bpy.context.scene.objects:
    o.select_set(o in meshes)
bpy.context.view_layer.objects.active = meshes[0]
if len(meshes) > 1:
    bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
for o in list(bpy.context.scene.objects):
    if o.type != "MESH":
        bpy.data.objects.remove(o)
ob.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
ob.name = who + "_body"

# --- clean (keep full detail: colours live on the vertices)
bm = bmesh.new(); bm.from_mesh(ob.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(ob.data); bm.free()

# --- normalise: feet on the ground, centred, real height
bb = [Vector(v.co) for v in ob.data.vertices]
mn = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
mx = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))
s = H / (mx.z - mn.z)
c = (mn + mx) / 2
for v in ob.data.vertices:
    v.co = Vector(((v.co.x - c.x) * s, (v.co.y - c.y) * s, (v.co.z - mn.z) * s))
ob.data.shade_smooth()
ob.data.update()
bb = [Vector(v.co) for v in ob.data.vertices]
mn = Vector((min(v.x for v in bb), min(v.y for v in bb), min(v.z for v in bb)))
mx = Vector((max(v.x for v in bb), max(v.y for v in bb), max(v.z for v in bb)))

# --- smooth away the sculpted eye/nose/mouth relief on the face: the drawn face then sits on a clean
# surface instead of sliding over bumps that do not line up with the drawing
bm = bmesh.new(); bm.from_mesh(ob.data)
Hn = mx.z - mn.z
face_v = [v for v in bm.verts if v.co.z > mn.z + 0.55 * Hn and v.normal.y < -0.25]
for it in range(40):
    bmesh.ops.smooth_vert(bm, verts=face_v, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bm.normal_update()
bm.to_mesh(ob.data); bm.free()
ob.data.update()

# --- texture: every face takes its colours from exactly ONE sheet view (no blending -> no ghosting).
# UVs point into a 4-tile atlas built by tex_prep.py; per-row silhouette matching keeps faces aligned.
import numpy as np, json
from mathutils.bvhtree import BVHTree

meta = json.load(open(os.path.join(OUT, who + "_atlas.json")))
TW, TH = meta["tile_w"], meta["tile_h"]
AW = TW * len(meta["order"])
me = ob.data
n = len(me.vertices)
co = np.zeros(n * 3, dtype=np.float32); me.vertices.foreach_get("co", co); co = co.reshape(n, 3)
Hm = mx.z - mn.z
vz = (co[:, 2] - mn.z) / Hm
HC = {"F": (co[:, 0] - mn.x) / (mx.x - mn.x), "B": (co[:, 0] - mn.x) / (mx.x - mn.x),
      "Xp": (co[:, 1] - mn.y) / (mx.y - mn.y), "Xn": 1 - (co[:, 1] - mn.y) / (mx.y - mn.y)}
DIRS = {"F": Vector((0, -1, 0)), "B": Vector((0, 1, 0)), "Xp": Vector((1, 0, 0)), "Xn": Vector((-1, 0, 0))}
NB = 256
zb = np.clip((vz * NB).astype(int), 0, NB - 1)


def mesh_ext(h):
    L = np.full(NB, np.nan); R = np.full(NB, np.nan)
    order = np.argsort(zb)
    for b in range(NB):
        sel = h[zb == b]
        if len(sel):
            L[b], R[b] = sel.min(), sel.max()
    idx = np.arange(NB); ok = ~np.isnan(L)
    L = np.interp(idx, idx[ok], L[ok]); R = np.interp(idx, idx[ok], R[ok])
    from statistics import median
    def med(a, k=5):
        return np.array([median(a[max(0, i - k):i + k + 1]) for i in range(len(a))])
    return med(L), med(R)


UVV = {}
for k in meta["order"]:
    t = meta["tiles"][k]
    L, R = np.array(t["L"]), np.array(t["R"])
    h = HC[k]
    Lm, Rm = mesh_ext(h)
    zf = np.clip(vz * NB - 0.5, 0, NB - 1)
    lm = np.interp(zf, np.arange(NB), Lm); rm = np.interp(zf, np.arange(NB), Rm)
    row = t["top"] + (1 - vz) * (t["bot"] - t["top"])
    rl = np.interp(row, np.arange(TH), L); rr = np.interp(row, np.arange(TH), R)
    frac = (h - lm) / np.maximum(1e-6, rm - lm)
    px = rl + np.clip(frac, 0, 1) * (rr - rl)
    UVV[k] = np.stack([(t["x0"] + px) / AW, 1 - row / TH], 1)

bm = bmesh.new(); bm.from_mesh(me)
bm.faces.ensure_lookup_table()
bvh = BVHTree.FromBMesh(bm)
eps = 0.004 * Hm
choice = []
for f in bm.faces:
    c = f.calc_center_median(); nn = f.normal
    best, bk = -9, "F"
    head = c.z > mn.z + 0.52 * Hm
    if head and nn.dot(DIRS["F"]) > 0.15 and bvh.ray_cast(c + DIRS["F"] * eps, DIRS["F"])[0] is None:
        choice.append("F")      # the whole face hemisphere comes from the front drawing (one eye, one nose)
        continue
    for k, d in DIRS.items():
        if head and k == "F":
            continue
        sc_ = nn.dot(d) * (1.25 if k == "F" else 1.0)
        hit = bvh.ray_cast(c + d * eps, d)
        if hit[0] is not None:
            sc_ -= 2.0
        if sc_ > best:
            best, bk = sc_, k
    choice.append(bk)
uvl = bm.loops.layers.uv.new("UVMap")
for f, k in zip(bm.faces, choice):
    uv = UVV[k]
    for l in f.loops:
        l[uvl].uv = uv[l.vert.index]
bm.to_mesh(me); bm.free()
print("views", {k: choice.count(k) for k in DIRS})

final = bpy.data.materials.new(who + "_mat")
final.use_nodes = True
nt = final.node_tree
p = nt.nodes["Principled BSDF"]


def tex(fn):
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(os.path.join(OUT, fn))
    t.interpolation = "Cubic"
    t.extension = "EXTEND"
    return t


cur = tex(who + "_atlas.png").outputs["Color"]
for ex in meta["exprs"]:
    t = tex(f"{who}_atlas_{ex}.png")
    mx_ = nt.nodes.new("ShaderNodeMix")
    mx_.data_type = "RGBA"
    mx_.name = "EXPR_" + ex
    mx_.inputs["Factor"].default_value = 0.0
    nt.links.new(cur, mx_.inputs[6])
    nt.links.new(t.outputs["Color"], mx_.inputs[7])
    cur = mx_.outputs[2]
hs = nt.nodes.new("ShaderNodeHueSaturation")
hs.name = "VIVID"
hs.inputs["Saturation"].default_value = 1.12
hs.inputs["Value"].default_value = 1.03
nt.links.new(cur, hs.inputs["Color"])
nt.links.new(hs.outputs["Color"], p.inputs["Base Color"])
p.inputs["Roughness"].default_value = 0.6
p.inputs["Specular IOR Level"].default_value = 0.25
ob.data.materials.clear()
ob.data.materials.append(final)
sc = bpy.context.scene

# --- skeleton (chibi proportions measured from the mesh)
verts = [Vector(v.co) for v in ob.data.vertices]


def width_at(z, band=0.02):
    xs = [v.x for v in verts if abs(v.z - z) < band * H]
    return (min(xs), max(xs)) if xs else (0, 0)


hip_z = 0.30 * H
neck_z = 0.50 * H
top_z = H
sh_z = neck_z - 0.03 * H
torso = [v for v in verts if 0.35 * H < v.z < 0.45 * H and abs(v.x) < 0.2 * H]
tw = max(abs(v.x) for v in torso) if torso else 0.12 * H
# hands: extreme x at arm height band
arm_band = [v for v in verts if 0.25 * H < v.z < 0.48 * H]
hL = max(arm_band, key=lambda v: v.x)
hR = min(arm_band, key=lambda v: v.x)
feet = [v for v in verts if v.z < 0.06 * H]
fl = [v for v in feet if v.x > 0]
fr = [v for v in feet if v.x <= 0]
footL = Vector((sum(v.x for v in fl) / max(1, len(fl)), 0, 0.04 * H))
footR = Vector((sum(v.x for v in fr) / max(1, len(fr)), 0, 0.04 * H))

ad = bpy.data.armatures.new(who + "_arm")
arm = bpy.data.objects.new(who + "_rig", ad)
sc.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
for o in sc.objects:
    o.select_set(False)
arm.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
eb = ad.edit_bones
B = {}


def bone(n, a, b, parent=None, deform=True):
    e = eb.new(n)
    e.head, e.tail = Vector(a), Vector(b)
    e.use_deform = deform
    if parent:
        e.parent = B[parent]
    B[n] = e


cy = 0.0
bone("root", (0, cy, 0), (0, cy + 0.1 * H, 0), deform=False)
bone("hips", (0, cy, hip_z), (0, cy, hip_z + 0.08 * H), "root")
bone("spine", (0, cy, hip_z + 0.08 * H), (0, cy, neck_z), "hips")
bone("head", (0, cy, neck_z), (0, cy, top_z), "spine")
for side, sg, hand in (("L", 1, hL), ("R", -1, hR)):
    sh = Vector((sg * tw * 0.85, cy, sh_z))
    hd = Vector((hand.x * 0.95, cy, hand.z + 0.02 * H))
    el = sh.lerp(hd, 0.5) + Vector((0, 0.01 * H, 0))
    bone("upper_arm." + side, sh, el, "spine")
    bone("forearm." + side, el, hd, "upper_arm." + side)
    hipj = Vector((sg * 0.07 * H, cy, hip_z))
    foot = footL if side == "L" else footR
    knee = hipj.lerp(foot, 0.5) + Vector((0, -0.01 * H, 0))
    bone("thigh." + side, hipj, knee, "hips")
    bone("shin." + side, knee, foot, "thigh." + side)
    bone("foot." + side, foot, foot + Vector((0, -0.08 * H, -0.02 * H)), "shin." + side)
bpy.ops.object.mode_set(mode="OBJECT")

for o in sc.objects:
    o.select_set(False)
ob.select_set(True)
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type="ARMATURE_AUTO")
ok = sum(1 for g in ob.vertex_groups) > 0
print("RIG groups", [g.name for g in ob.vertex_groups], "ok", ok)

col = bpy.data.collections.new(who)
sc.collection.children.link(col)
for o in (ob, arm):
    for c0 in o.users_collection:
        c0.objects.unlink(o)
    col.objects.link(o)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, who + ".blend"))
print("SAVED", os.path.join(OUT, who + ".blend"), "faces", len(ob.data.polygons))
