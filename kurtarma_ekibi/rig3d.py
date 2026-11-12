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

# --- vertex colours: project the 4 sheet views, blended by the surface normal
import numpy as np


def load(name):
    img = bpy.data.images.load(os.path.join(VIEWS, name + ".png"))
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    return a


IMG = {"F": load(vF), "B": load(vB), "Xp": load(vXp), "Xn": load(vXn)}


def sample(a, u, v):
    h, w = a.shape[:2]
    x = np.clip(u * (w - 1), 0, w - 1)
    y = np.clip(v * (h - 1), 0, h - 1)
    x0 = np.floor(x).astype(int); y0 = np.floor(y).astype(int)
    x1 = np.minimum(x0 + 1, w - 1); y1 = np.minimum(y0 + 1, h - 1)
    fx = (x - x0)[:, None]; fy = (y - y0)[:, None]
    c = (a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x1] * fx * (1 - fy) + a[y1, x0] * (1 - fx) * fy + a[y1, x1] * fx * fy)
    return c


me = ob.data
n = len(me.vertices)
co = np.zeros(n * 3, dtype=np.float32); me.vertices.foreach_get("co", co); co = co.reshape(n, 3)
me.calc_normals() if hasattr(me, "calc_normals") else None
nr = np.zeros(n * 3, dtype=np.float32); me.vertices.foreach_get("normal", nr); nr = nr.reshape(n, 3)
def fit(a):
    """Bounding box of the opaque pixels (u0,u1,v0,v1) in normalised image coords (v up)."""
    al = a[..., 3] > 0.5
    ys, xs = np.nonzero(al)
    h, w = al.shape
    return xs.min() / w, (xs.max() + 1) / w, ys.min() / h, (ys.max() + 1) / h


def proj(a, u, v):
    u0, u1, v0, v1 = fit(a)
    return sample(a, u0 + u * (u1 - u0), v0 + v * (v1 - v0))


vz = (co[:, 2] - mn.z) / (mx.z - mn.z)
ux = (co[:, 0] - mn.x) / (mx.x - mn.x)
uy = (co[:, 1] - mn.y) / (mx.y - mn.y)
FLIPX = "--flipx" in argv
cols = {"F": proj(IMG["F"], ux, vz), "B": proj(IMG["B"], ux, vz),
        "Xp": proj(IMG["Xp"], uy, vz), "Xn": proj(IMG["Xn"], 1 - uy, vz)}
K = 6.0
w = {"F": np.maximum(-nr[:, 1], 0) ** K * 1.6, "B": np.maximum(nr[:, 1], 0) ** K,
     "Xp": np.maximum(nr[:, 0], 0) ** K, "Xn": np.maximum(-nr[:, 0], 0) ** K}
# ignore transparent samples (outside the silhouette in that view)
for k in w:
    w[k] = w[k] * (cols[k][:, 3] > 0.5) + 1e-6
tot = sum(w.values())
rgb = sum(cols[k][:, :3] * (w[k] / tot)[:, None] for k in w)
ca = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
ca.data.foreach_set("color", np.hstack([rgb, np.ones((n, 1), np.float32)]).ravel())

# --- expression variants: re-project only the front of the head from each expression picture
def head_box(a, top_frac=0.46):
    al = a[..., 3] > 0.5
    h, w = al.shape
    ys, xs = np.nonzero(al)
    ytop = ys.max()                      # Blender pixels: row 0 = bottom
    ybody = ys.min()
    hh = (ytop - ybody) * top_frac
    sel = ys > ytop - hh
    return xs[sel].min() / w, (xs[sel].max() + 1) / w, (ytop - hh) / h, (ytop + 1) / h


neck = mn.z + (mx.z - mn.z) * 0.54
hv = co[:, 2] > neck
hx0, hx1 = co[hv, 0].min(), co[hv, 0].max()
hz0, hz1 = neck, mx.z
front_w = np.clip(-nr[:, 1] * 1.4, 0, 1) * np.clip((co[:, 2] - neck) / ((mx.z - mn.z) * 0.04), 0, 1)
for ex in ("happy", "sad", "surprised", "angry"):
    pth = os.path.join(VIEWS, ex + ".png")
    if not os.path.exists(pth):
        continue
    A = load(ex)
    u0, u1, v0, v1 = head_box(A)
    hu = (co[:, 0] - hx0) / (hx1 - hx0)
    hzv = (co[:, 2] - hz0) / (hz1 - hz0)
    c = sample(A, u0 + hu * (u1 - u0), v0 + hzv * (v1 - v0))
    wv = front_w * (c[:, 3] > 0.5)
    rgb_e = rgb * (1 - wv[:, None]) + c[:, :3] * wv[:, None]
    ce = me.color_attributes.new("Col_" + ex, "FLOAT_COLOR", "POINT")
    ce.data.foreach_set("color", np.hstack([rgb_e, np.ones((n, 1), np.float32)]).ravel())

final = bpy.data.materials.new(who + "_mat")
final.use_nodes = True
p = final.node_tree.nodes["Principled BSDF"]
t = final.node_tree.nodes.new("ShaderNodeVertexColor")
t.layer_name = "Col"
cur = t.outputs["Color"]
for ex in ("happy", "sad", "surprised", "angry"):
    if ("Col_" + ex) not in me.color_attributes:
        continue
    vc = final.node_tree.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "Col_" + ex
    mx_ = final.node_tree.nodes.new("ShaderNodeMix")
    mx_.data_type = "RGBA"
    mx_.name = "EXPR_" + ex
    mx_.inputs["Factor"].default_value = 0.0
    final.node_tree.links.new(cur, mx_.inputs[6])
    final.node_tree.links.new(vc.outputs["Color"], mx_.inputs[7])
    cur = mx_.outputs[2]
final.node_tree.links.new(cur, p.inputs["Base Color"])
p.inputs["Roughness"].default_value = 0.55
p.inputs["Specular IOR Level"].default_value = 0.3
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
