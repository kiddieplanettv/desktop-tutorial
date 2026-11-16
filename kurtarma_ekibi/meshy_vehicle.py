"""Turn a Meshy vehicle model (GLB) into toys3d/<name>.blend: scaled, facing +X, standing on z=0, with the
wheels cut out as separate objects (so they can turn) and a small JSON with the measurements.

blender -b -P meshy_vehicle.py -- <name> <model.glb> <length m> [flip] [faces=70000] [axles=N]
"""
import bpy, bmesh, sys, os, json, math
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:]
name, src, length = argv[0], argv[1], float(argv[2])
opt = dict(a.split("=") for a in argv[3:] if "=" in a)
flip = "flip" in argv
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "toys3d")
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
ms = [o for o in bpy.data.objects if o.type == "MESH"]
bpy.context.view_layer.objects.active = ms[0]
for o in ms:
    o.select_set(True)
if len(ms) > 1:
    bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
ob.data.transform(ob.matrix_world); ob.matrix_world = Matrix(); ob.parent = None
for o in list(bpy.data.objects):
    if o is not ob:
        bpy.data.objects.remove(o)
target = int(opt.get("faces", 70000))
n0 = len(ob.data.polygons)
if n0 > target:
    md = ob.modifiers.new("dec", "DECIMATE"); md.ratio = target / n0
    bpy.ops.object.modifier_apply(modifier="dec")
me = ob.data
co = [v.co.copy() for v in me.vertices]
lo = Vector([min(c[i] for c in co) for i in range(3)]); hi = Vector([max(c[i] for c in co) for i in range(3)])
size = hi - lo
R = Matrix.Identity(4)
if size.y > size.x:                       # long axis -> X
    R = Matrix.Rotation(math.radians(-90), 4, "Z")
if flip:
    R = Matrix.Rotation(math.radians(180), 4, "Z") @ R
me.transform(R)
co = [v.co.copy() for v in me.vertices]
lo = Vector([min(c[i] for c in co) for i in range(3)]); hi = Vector([max(c[i] for c in co) for i in range(3)])
k = length / (hi.x - lo.x)
me.transform(Matrix.Scale(k, 4) @ Matrix.Translation((-(lo.x + hi.x) / 2, -(lo.y + hi.y) / 2, -lo.z)))
co = [v.co.copy() for v in me.vertices]
hi = Vector([max(c[i] for c in co) for i in range(3)]); lo = Vector([min(c[i] for c in co) for i in range(3)])
H, W = hi.z, hi.y - lo.y
print("SIZE", [round(x, 3) for x in (hi - lo)], "faces", len(me.polygons))

# ---- find the wheels: clusters of the points that touch the ground
band = [c for c in co if c.z < float(opt.get("band", 0.012)) * length]
xs = sorted(c.x for c in band)
groups = [[xs[0]]]
for x in xs[1:]:
    if x - groups[-1][-1] > 0.03 * length:
        groups.append([x])
    else:
        groups[-1].append(x)
groups = [g for g in groups if len(g) >= 6]
wheels = []
cxs = [(g[0] + g[-1]) / 2 for g in groups]
for gi, g in enumerate(groups):
    cx = cxs[gi]
    dmin = min([abs(cx - o) for o in cxs if o != cx] or [0.4 * length])
    lim = min(0.48 * dmin, 0.2 * length)
    rs = []
    for h in (0.02, 0.03, 0.04):
        hh = h * length
        sl = [c.x for c in co if abs(c.z - hh) < 0.005 * length and abs(c.x - cx) < lim]
        if len(sl) > 4:
            w = (max(sl) - min(sl)) / 2
            if w < lim * 0.97:
                rs.append((w * w + hh * hh) / (2 * hh))
    if not rs:
        continue
    r = sorted(rs)[len(rs) // 2]
    for sd in (1, -1):
        low = [c.y for c in band if abs(c.x - cx) < r * 0.5 and c.y * sd > 0]
        if len(low) < 3:
            continue
        ya, yb = min(low), max(low)
        pad = max(0.02 * length, (yb - ya) * 0.2)
        ya, yb = (max(0.0, ya - pad), yb + pad) if sd > 0 else (ya - pad, min(0.0, yb + pad))
        wheels.append(dict(x=cx, r=r, y0=ya, y1=yb))
for w in wheels:
    w["z"] = w["r"]
if "wheels" in opt:                      # manual axles: x:r:z,...  (side extent taken from the detected wheels)
    yp = [w for w in wheels if w["y0"] >= 0][0]; yn = [w for w in wheels if w["y1"] <= 0][0]
    wheels = []
    for it in opt["wheels"].split(","):
        x_, r_, z_ = [float(v) for v in it.split(":")]
        for src in (yp, yn):
            wheels.append(dict(x=x_, r=r_, z=z_, y0=src["y0"], y1=src["y1"]))
print("WHEELS", [(round(w["x"], 2), round(w["r"], 3), round(w["y0"], 2), round(w["y1"], 2)) for w in wheels])

# ---- cut each wheel out into its own object
bm = bmesh.new(); bm.from_mesh(me)
bm.faces.ensure_lookup_table()
tag = [-1] * len(bm.faces)
for wi, w in enumerate(wheels):
    rr = (w["r"] * float(opt.get("rcut", 1.03))) ** 2
    for f in bm.faces:
        if tag[f.index] >= 0:
            continue
        if all((v.co.x - w["x"]) ** 2 + (v.co.z - w["z"]) ** 2 < rr and w["y0"] - 0.01 <= v.co.y <= w["y1"] + 0.01 for v in f.verts):
            tag[f.index] = wi
bm.free()
mat = me.materials[0]
objs = []
for wi, w in enumerate(wheels):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="DESELECT"); bpy.ops.object.mode_set(mode="OBJECT")
    idx = [i for i, t in enumerate(tag) if t == wi]
    if not idx:
        continue
    for i in idx:
        me.polygons[i].select = True
    before = set(bpy.data.objects)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.separate(type="SELECTED"); bpy.ops.object.mode_set(mode="OBJECT")
    new = (set(bpy.data.objects) - before).pop()
    c = Vector((w["x"], (w["y0"] + w["y1"]) / 2, w["z"]))
    new.data.transform(Matrix.Translation(-c)); new.location = c
    new.name = f"{name}_wheel{wi}"
    objs.append(new)
    # the polygon indices changed: recompute the tags for the remaining wheels
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    tag = [-1] * len(bm.faces)
    for wj, w2 in enumerate(wheels):
        if wj <= wi:
            continue
        rr = (w2["r"] * float(opt.get("rcut", 1.03))) ** 2
        for f in bm.faces:
            if all((v.co.x - w2["x"]) ** 2 + (v.co.z - w2["z"]) ** 2 < rr and w2["y0"] - 0.01 <= v.co.y <= w2["y1"] + 0.01 for v in f.verts):
                tag[f.index] = wj
    bm.free()
ob.name = name + "_body"
for o in [ob] + objs:
    for p in o.data.polygons:
        p.use_smooth = True
# plastic toy material from the model's own colour texture
img = next(n.image for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image)
fn = os.path.join(OUT, name + "_tex.png")
img.filepath_raw = fn; img.file_format = "PNG"; img.save()
m2 = bpy.data.materials.new(name + "_mat"); m2.use_nodes = True
nt = m2.node_tree; p = nt.nodes["Principled BSDF"]
t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(fn)
hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = 1.12
nt.links.new(t.outputs["Color"], hs.inputs["Color"]); nt.links.new(hs.outputs["Color"], p.inputs["Base Color"])
p.inputs["Roughness"].default_value = 0.32; p.inputs["Specular IOR Level"].default_value = 0.5
for o in [ob] + objs:
    o.data.materials.clear(); o.data.materials.append(m2)
col = bpy.data.collections.new(name)
bpy.context.scene.collection.children.link(col)
for o in [ob] + objs:
    for c0 in list(o.users_collection):
        c0.objects.unlink(o)
    col.objects.link(o)
for c0 in list(bpy.data.collections):
    if c0 is not col:
        bpy.data.collections.remove(c0)
json.dump(dict(length=length, width=W, height=H, wheels=[dict(x=w["x"], y=(w["y0"] + w["y1"]) / 2, r=w["r"]) for w in wheels]),
          open(os.path.join(OUT, name + ".json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, name + ".blend"))
print("SAVED", name, "wheels", len(objs))
