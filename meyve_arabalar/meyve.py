"""Meyve Arabalar - Saklambac: a one-minute vertical 3D short made only with Blender 5.2 (no external models).
python meyve.py [--lo] [--frames N]     ->  build/meyve.blend      (run with Blender 5.2's Python, or blender -b -P)"""
import bpy, bmesh, sys, os, math, random
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
LO = "--lo" in sys.argv
MID = "--mid" in sys.argv          # 720x1280 preview
FPS = 24
N = 1440
if "--frames" in sys.argv:
    N = int(sys.argv[sys.argv.index("--frames") + 1])
R = math.radians

# ------------------------------------------------------------------ basics
bpy.ops.wm.read_factory_settings(use_empty=True)
S = bpy.context.scene
S.render.engine = "BLENDER_EEVEE"
S.render.resolution_x, S.render.resolution_y = (540, 960) if LO else (720, 1280) if MID else (1080, 1920)
S.render.fps = FPS
S.frame_start, S.frame_end = 0, N - 1
S.eevee.taa_render_samples = 8 if LO else 12 if MID else 32
S.view_settings.view_transform = "Standard"
S.view_settings.look = "None"
S.view_settings.gamma = 0.92; S.view_settings.exposure = 0.1
COLL = S.collection
_mats = {}


def mat(name, col, rough=0.45, emit=0.0, spec=0.5):
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*col, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Specular IOR Level"].default_value = spec
    if emit:
        p.inputs["Emission Color"].default_value = (*col, 1)
        p.inputs["Emission Strength"].default_value = emit
    _mats[name] = m
    return m


def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None); COLL.objects.link(o)
    o.location = loc; o.parent = parent
    return o


def obj(name, bm, m=None, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), smooth=True):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    o = bpy.data.objects.new(name, me); COLL.objects.link(o)
    if m:
        for x in (m if isinstance(m, (list, tuple)) else [m]):
            me.materials.append(x)
    o.parent = parent; o.location = loc; o.rotation_euler = rot; o.scale = scale
    return o


def sphere(name, r, m, parent=None, loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), u=24, v=14):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=r)
    return obj(name, bm, m, parent, loc, rot, scale)


def cyl(name, r, h, m, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), r2=None, seg=24, scale=(1, 1, 1), smooth=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=h)
    o = obj(name, bm, m, parent, loc, rot, scale, smooth)
    md = o.modifiers.new("e", "EDGE_SPLIT"); md.split_angle = R(40)
    return o


def box(name, size, m, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), bevel=0.0):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    o = obj(name, bm, m, parent, loc, rot, smooth=False)
    if bevel:
        md = o.modifiers.new("b", "BEVEL"); md.width = bevel; md.segments = 3
        for p in o.data.polygons:
            p.use_smooth = True
    return o


def torus(name, R_, r, m, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), arc=(0, 360), seg=32, scale=(1, 1, 1)):
    bm = bmesh.new()
    a0, a1 = R(arc[0]), R(arc[1]); n = seg; k = 10
    rings = []
    full = abs(arc[1] - arc[0]) >= 360
    cnt = n if full else n + 1
    for i in range(cnt):
        a = a0 + (a1 - a0) * i / n
        c = Vector((math.cos(a) * R_, math.sin(a) * R_, 0)); d = Vector((math.cos(a), math.sin(a), 0))
        rings.append([bm.verts.new(c + d * r * math.cos(2 * math.pi * j / k) + Vector((0, 0, r * math.sin(2 * math.pi * j / k)))) for j in range(k)])
    for i in range(cnt if full else cnt - 1):
        A, B = rings[i], rings[(i + 1) % cnt]
        for j in range(k):
            bm.faces.new((A[j], A[(j + 1) % k], B[(j + 1) % k], B[j]))
    if not full:
        bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    return obj(name, bm, m, parent, loc, rot, scale)


def key(o, path, f, v=None, idx=-1):
    if v is not None:
        if idx >= 0:
            getattr(o, path)[idx] = v
        else:
            setattr(o, path, v)
    o.keyframe_insert(path, frame=f, index=idx)


def jump_to(o, path, f, v):
    """Instant change at frame f (cut)."""
    o.keyframe_insert(path, frame=f - 1)
    setattr(o, path, v); o.keyframe_insert(path, frame=f)


# ------------------------------------------------------------------ fruit cars
C = dict(red=(0.93, 0.07, 0.10), orange=(1.0, 0.45, 0.02), yellow=(1.0, 0.80, 0.05), gold=(0.95, 0.62, 0.08),
         purple=(0.42, 0.14, 0.72), pear=(0.62, 0.85, 0.16), leaf=(0.16, 0.62, 0.14), leaf2=(0.30, 0.75, 0.18),
         stem=(0.42, 0.26, 0.10), glass=(0.45, 0.80, 1.0), tyre=(0.08, 0.08, 0.10), white=(1, 1, 1), black=(0.01, 0.01, 0.015),
         pink=(1.0, 0.45, 0.55), mouth=(0.45, 0.03, 0.06), tongue=(1.0, 0.35, 0.40), cream=(1.0, 0.93, 0.75), wood=(0.72, 0.48, 0.24))
SPEC = dict(
    cilek=dict(L=2.2, W=1.9, H=1.9, col=C["red"], hub=C["cream"]),
    portakal=dict(L=2.2, W=2.0, H=1.9, col=C["orange"], hub=C["cream"]),
    muz=dict(L=3.6, W=1.7, H=1.6, col=C["yellow"], hub=C["cream"]),
    ananas=dict(L=2.1, W=1.9, H=2.3, col=C["gold"], hub=C["leaf2"]),
    uzum=dict(L=2.0, W=1.8, H=1.7, col=C["purple"], hub=C["leaf2"]),
    armut=dict(L=2.1, W=1.9, H=2.2, col=C["pear"], hub=C["cream"]),
)


class Car:
    def __init__(self, kind):
        self.kind = kind; sp = SPEC[kind]; self.sp = sp
        L, W, H = sp["L"], sp["W"], sp["H"]
        self.root = empty(kind); self.b = empty(kind + "_bounce", parent=self.root)
        self.wheels = []; self.spin = 0.0; self.pos = (0.0, 0.0); self.rz = 0.0
        body_m = mat(kind + "_body", sp["col"], rough=0.3, spec=0.6)
        glass = mat("glass", C["glass"], rough=0.08, spec=1.0)
        self.clear = 0.22

        def shape(p):
            x, y, z = p
            e = 0.85
            x, y, z = (math.copysign(abs(c) ** e, c) for c in (x, y, z))
            if z < -0.5:
                z = -0.5 + (z + 0.5) * 0.35
            wx = wy = 1.0
            if kind == "armut":                    # narrow top, fat bottom
                t = max(0.0, z); wx = wy = 1 - 0.42 * t ** 1.3
            if kind == "ananas":
                t = abs(z); wx = wy = 1 - 0.10 * t
            if kind == "cilek":
                t = max(0.0, -z + 0.3); wx = 1 - 0.07 * t; wy = 1 - 0.07 * t
            px, py, pz = x * L / 2 * wx, y * W / 2 * wy, (z + 0.675) / 1.675 * H
            if kind == "muz":
                pz += 0.22 * (px / (L / 2)) ** 2 * H * 0.5
            return Vector((px, py, pz + self.clear))
        self.shape = shape
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=40, radius=1)
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(R(90), 3, "X"), verts=bm.verts)
        wins = []
        if kind == "muz":
            for a0 in (22, 62, 102, 142):
                wins.append((a0, a0 + 30, 50, 72))
            wins.append((30, 62, -40, 40))
        else:
            wins += [(30, 68, -42, 42), (28, 150, 52, 74)]
        for f in bm.faces:
            c = f.calc_center_median().normalized()
            th = math.degrees(math.atan2(c.z, c.x)); lat = math.degrees(math.asin(max(-1, min(1, c.y))))
            for (t0, t1, l0, l1) in wins:
                if t0 <= th <= t1 and (l0 <= lat <= l1 or (l0 > 0 and l0 <= -lat <= l1)):
                    f.material_index = 1
        for v in bm.verts:
            v.co = shape(v.co.normalized())
        self.body = obj(kind + "_body", bm, [body_m, glass], self.b)
        # wheels
        r = 0.36 if kind != "muz" else 0.34
        xs = [0.52 * L / 2, -0.52 * L / 2] if kind != "muz" else [0.62 * L / 2, -0.62 * L / 2]
        for x in xs:
            for sd in (1, -1):
                w = empty(kind + "_wheel", (x, sd * (W / 2 - 0.12), r), self.b)
                torus("tyre", r - 0.13, 0.13, mat("tyre", C["tyre"], rough=0.7), w, rot=(R(90), 0, 0), scale=(1, 1, 1.5))
                cyl("hub", r - 0.14, 0.44, mat(kind + "_hub", sp["hub"], rough=0.35), w, rot=(R(90), 0, 0))
                cyl("cap", 0.07, 0.48, mat(kind + "_body", sp["col"]), w, rot=(R(90), 0, 0))
                for i in range(5):
                    a = i * 2 * math.pi / 5
                    sphere("nut", 0.035, mat(kind + "_body", sp["col"]), w, (math.cos(a) * 0.14, sd * 0.225, math.sin(a) * 0.14), u=8, v=6)
                self.wheels.append(w)
        self.face()
        getattr(self, "deco_" + kind)()

    def surf(self, th, lat, out=0.0):
        """Point on the body: th = angle from the nose up to the roof (deg), lat = sideways angle (deg)."""
        d = Vector((math.cos(R(th)) * math.cos(R(lat)), math.sin(R(lat)), math.sin(R(th)) * math.cos(R(lat))))
        p = self.shape(d)
        return p + d * out

    def face(self):
        k = self.kind
        th_e, th_m = (4, -17) if k != "muz" else (2, -22)
        la = 21 if k != "muz" else 24
        white = mat("eye_w", C["white"], rough=0.25); black = mat("eye_b", C["black"], rough=0.15, spec=1.0)
        self.eyes = []; self.pupils = []
        for sd in (1, -1):
            p = self.surf(th_e, sd * la, -0.05)
            e = empty(k + "_eye", p, self.b)
            sphere("white", 0.24, white, e, scale=(0.55, 1, 1.12))
            pu = empty("pupil", (0.075, 0, 0), e)
            sphere("black", 0.15, black, pu, scale=(0.5, 1, 1.1))
            sphere("hl", 0.05, mat("eye_hl", C["white"], emit=0.6), pu, (0.065, 0.05 * 1, 0.07), scale=(0.5, 1, 1))
            sphere("hl2", 0.025, mat("eye_hl", C["white"], emit=0.6), pu, (0.07, -0.05, -0.05), scale=(0.5, 1, 1))
            self.eyes.append(e); self.pupils.append(pu)
            pc = self.surf(th_m + 3, sd * (la + 17), -0.03)
            sphere("cheek", 0.13, mat("cheek", C["pink"], rough=0.6), self.b, pc, scale=(0.3, 1, 0.7))
        pm = self.surf(th_m, 0, 0.0)
        self.smile = torus(k + "_smile", 0.15, 0.028, mat("mouth_line", C["black"]), self.b, pm + Vector((0.01, 0, 0.07)),
                           rot=(R(90), 0, R(90)), arc=(200, 340), seg=16)
        self.open = empty(k + "_open", pm + Vector((-0.01, 0, 0.03)), self.b)
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.17)
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0.02), plane_no=(0, 0, 1), clear_outer=True)
        bmesh.ops.holes_fill(bm, edges=bm.edges)
        obj("mouth", bm, mat("mouth", C["mouth"], rough=0.4), self.open, scale=(0.45, 1.05, 1.0))
        sphere("tongue", 0.085, mat("tongue", C["tongue"], rough=0.4), self.open, (0.035, 0, -0.105), scale=(0.5, 1.1, 0.6))
        self.open.scale = (0, 0, 0)

    # ---- decorations
    def leaf(self, loc, rz, tilt, size=0.5, m="leaf", parent=None):
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=1)
        for v in bm.verts:
            x, y, z = v.co
            w = (1 - x * x) ** 0.5 if abs(x) < 1 else 0
            v.co = Vector(((x + 1) * 0.5 * size, y * 0.26 * size * (0.4 + w * 0.9), z * 0.05 * size - 0.12 * size * ((x + 1) * 0.5) ** 2 * tilt))
        return obj("leaf", bm, mat(m, C[m], rough=0.5), parent or self.b, loc, (0, 0, rz))

    def stem(self, top, h=0.3, r=0.06, lean=0.25, m="stem"):
        return cyl("stem", r, h, mat(m, C[m], rough=0.6), self.b, top + Vector((0, 0, h / 2 - 0.03)), rot=(0, lean, 0), r2=r * 0.7, seg=10)

    def seeds(self, n, col, size=0.045, skip=lambda th, lat: False):
        bm = bmesh.new(); k = 0
        for i in range(n):
            z = 1 - 2 * (i + 0.5) / n; rr = (1 - z * z) ** 0.5; a = i * 2.39996
            d = Vector((rr * math.cos(a), rr * math.sin(a), z))
            if d.z < -0.45:
                continue
            th = math.degrees(math.atan2(d.z, d.x)); lat = math.degrees(math.asin(d.y))
            if skip(th, lat):
                continue
            p = self.shape(d)
            geom = bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=size)["verts"]
            q = Vector((0, 0, 1)).rotation_difference(d).to_matrix()
            for v in geom:
                v.co = q @ Vector((v.co.x * 0.8, v.co.y * 0.8, v.co.z * 0.45)) + p
            k += 1
        return obj("seeds", bm, mat("seed_" + self.kind, col, rough=0.4), self.b)

    def _clear_face(self, th, lat):
        win = (26 <= th <= 72 and abs(lat) < 46) or (24 <= th <= 154 and 48 <= abs(lat) <= 78)
        face = (-32 <= th <= 20 and abs(lat) < 46)
        return win or face

    def deco_cilek(self):
        self.seeds(420, (1.0, 0.85, 0.2), skip=self._clear_face)
        top = self.surf(90, 0)
        for i in range(7):
            self.leaf(top + Vector((0, 0, -0.02)), i * 2 * math.pi / 7 + 0.2, 1.6, size=0.85)
        self.stem(top, 0.34, 0.07, m="leaf")
        # the truck part: a little wooden bed with strawberries
        L, W = self.sp["L"], self.sp["W"]
        wood = mat("wood", C["wood"], rough=0.6)
        box("bed", (1.7, W * 0.92, 0.16), wood, self.b, (-L / 2 - 0.55, 0, 0.62), bevel=0.04)
        for sd in (1, -1):
            box("rail", (1.7, 0.1, 0.42), wood, self.b, (-L / 2 - 0.55, sd * (W * 0.46 - 0.05), 0.86), bevel=0.03)
        box("tail", (0.1, W * 0.92, 0.42), wood, self.b, (-L / 2 - 1.36, 0, 0.86), bevel=0.03)
        r = 0.36
        for sd in (1, -1):
            w = empty("cilek_wheel", (-L / 2 - 0.85, sd * (W / 2 - 0.12), r), self.b)
            torus("tyre", r - 0.13, 0.13, mat("tyre", C["tyre"]), w, rot=(R(90), 0, 0), scale=(1, 1, 1.5))
            cyl("hub", r - 0.14, 0.44, mat("cilek_hub", C["cream"]), w, rot=(R(90), 0, 0))
            cyl("cap", 0.07, 0.48, mat("cilek_body", C["red"]), w, rot=(R(90), 0, 0))
            self.wheels.append(w)
        rnd = random.Random(4)
        for i, (x, y) in enumerate([(-0.2, -0.45), (-0.25, 0.42), (-0.85, 0.0), (-0.75, -0.55), (-0.8, 0.55), (-0.5, 0.05)]):
            e = empty("mini", (-L / 2 - 0.25 + x, y, 0.98 + (0.25 if i == 5 else 0)), self.b)
            sphere("s", 0.3, mat("cilek_body", C["red"]), e, scale=(1, 1, 1.12), u=16, v=10)
            for j in range(5):
                self.leaf((0, 0, 0.31), j * 1.257 + i, 1.5, size=0.3, parent=e)
            e.rotation_euler = (rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), rnd.uniform(0, 3))

    def deco_portakal(self):
        self.seeds(170, (1.0, 0.56, 0.10), size=0.03, skip=self._clear_face)
        top = self.surf(90, 0)
        self.stem(top, 0.22, 0.06)
        self.leaf(top + Vector((0, 0, 0.1)), R(200), 1.0, size=0.85, m="leaf2")
        self.leaf(top + Vector((0, 0, 0.1)), R(-40), 1.0, size=0.6, m="leaf")

    def deco_muz(self):
        L = self.sp["L"]
        for sgn in (-1,):
            p = self.shape(Vector((sgn, 0, 0.0)))
            cyl("tip", 0.16, 0.34, mat("stem", C["stem"]), self.b, p + Vector((sgn * 0.08, 0, 0.06)), rot=(0, R(90) - sgn * 0.5, 0), r2=0.09, seg=12)
        bm = bmesh.new()
        for i in range(40):                           # darker stripe along the roof ridge
            pass
        bm.free()
        top = self.surf(90, 0)
        self.leaf(top + Vector((0.2, 0, 0.0)), R(180), 0.6, size=0.7, m="leaf2")

    def deco_ananas(self):
        self.seeds(150, (0.80, 0.42, 0.03), size=0.06, skip=self._clear_face)
        top = self.surf(90, 0)
        m = mat("leaf", C["leaf"]); m2 = mat("leaf2", C["leaf2"])
        for ring, (n, tilt, h) in enumerate([(8, 0.75, 0.9), (6, 0.45, 1.1), (4, 0.18, 1.25)]):
            for i in range(n):
                a = i * 2 * math.pi / n + ring * 0.4
                cyl("crown", 0.16, h, m if ring % 2 == 0 else m2, self.b, top + Vector((math.cos(a) * 0.12, math.sin(a) * 0.12, -0.08)),
                    rot=(0, tilt, a), r2=0.0, seg=6, scale=(1, 0.45, 1)).data.transform(Matrix.Translation((0, 0, h / 2)))

    def deco_uzum(self):
        top = self.surf(90, 0)
        m = mat("uzum_body", C["purple"]); rnd = random.Random(2)
        pts = [(0, 0, 0.5)] + [(math.cos(a) * 0.3, math.sin(a) * 0.3, 0.2) for a in (0, 1.26, 2.5, 3.77, 5.03)]
        for (x, y, z) in pts:
            sphere("grape", 0.27, m, self.b, top + Vector((x - 0.1, y, z - 0.12)), u=16, v=10)
        self.stem(top + Vector((-0.1, 0, 0.72)), 0.26, 0.05)
        self.leaf(top + Vector((-0.1, 0, 0.82)), R(160), 1.0, size=0.7, m="leaf2")
        L, W = self.sp["L"], self.sp["W"]
        for sd in (1, -1):                              # grape mud-guards
            for x in (0.52 * L / 2, -0.52 * L / 2):
                sphere("g", 0.2, m, self.b, (x, sd * (W / 2 - 0.02), 0.82), u=12, v=8)

    def deco_armut(self):
        top = self.surf(90, 0)
        self.stem(top, 0.4, 0.06, lean=0.35)
        self.leaf(top + Vector((0.05, 0, 0.2)), R(190), 1.0, size=0.8, m="leaf")
        self.seeds(90, (0.50, 0.74, 0.10), size=0.028, skip=self._clear_face)

    # ---- animation helpers
    def place(self, f, x, y, rz, cut=True):
        r = self.root
        if cut:
            r.keyframe_insert("location", frame=f - 1); r.keyframe_insert("rotation_euler", frame=f - 1)
        r.location = (x, y, 0); r.rotation_euler = (0, 0, R(rz))
        r.keyframe_insert("location", frame=f); r.keyframe_insert("rotation_euler", frame=f)
        self.pos = (x, y); self.rz = rz
        for w in self.wheels:
            key(w, "rotation_euler", f, self.spin, 1)

    def move(self, f0, f1, x, y, rz=None, back=False):
        r = self.root
        r.keyframe_insert("location", frame=f0); r.keyframe_insert("rotation_euler", frame=f0)
        for w in self.wheels:
            key(w, "rotation_euler", f0, self.spin, 1)
        d = math.hypot(x - self.pos[0], y - self.pos[1])
        self.spin += (-d if back else d) / 0.36
        r.location = (x, y, 0)
        if rz is not None:
            r.rotation_euler = (0, 0, R(rz)); self.rz = rz
        r.keyframe_insert("location", frame=f1); r.keyframe_insert("rotation_euler", frame=f1)
        for w in self.wheels:
            key(w, "rotation_euler", f1, self.spin, 1)
        self.pos = (x, y)

    def turn(self, f0, f1, rz):
        r = self.root
        r.keyframe_insert("rotation_euler", frame=f0)
        r.rotation_euler = (0, 0, R(rz)); r.keyframe_insert("rotation_euler", frame=f1); self.rz = rz

    def hop(self, f, h=0.6, dur=12, n=1, tilt=0.0):
        b = self.b
        for i in range(n):
            a = f + i * (dur + 4)
            key(b, "scale", a - 3, (1, 1, 1)); key(b, "scale", a, (1.12, 1.12, 0.82)); key(b, "location", a, (0, 0, 0))
            key(b, "scale", a + 3, (0.92, 0.92, 1.14)); key(b, "location", a + dur // 2, (0, 0, h))
            key(b, "rotation_euler", a, (0, 0, 0)); key(b, "rotation_euler", a + dur // 2, (0, tilt, 0)); key(b, "rotation_euler", a + dur, (0, 0, 0))
            key(b, "scale", a + dur - 2, (0.94, 0.94, 1.1)); key(b, "location", a + dur, (0, 0, 0))
            key(b, "scale", a + dur + 1, (1.14, 1.14, 0.8)); key(b, "scale", a + dur + 5, (1, 1, 1))

    def wiggle(self, f0, f1, amp=0.07, per=6):
        b = self.b
        key(b, "rotation_euler", f0, (0, 0, 0)); s = 1
        for f in range(f0 + per // 2, f1, per):
            key(b, "rotation_euler", f, (s * amp, 0, 0)); s = -s
        key(b, "rotation_euler", f1, (0, 0, 0))

    def squash(self, f, amt=0.15):
        b = self.b
        key(b, "scale", f - 2, (1, 1, 1)); key(b, "scale", f + 1, (1 + amt, 1 + amt, 1 - amt * 1.3)); key(b, "scale", f + 6, (1, 1, 1))

    def blink(self, f):
        for e in self.eyes:
            key(e, "scale", f - 2, (1, 1, 1)); key(e, "scale", f, (1, 1, 0.08)); key(e, "scale", f + 1, (1, 1, 0.08)); key(e, "scale", f + 3, (1, 1, 1))

    def eyes_closed(self, f0, f1):
        for e in self.eyes:
            key(e, "scale", f0 - 2, (1, 1, 1)); key(e, "scale", f0, (1, 1, 0.08)); key(e, "scale", f1, (1, 1, 0.08)); key(e, "scale", f1 + 3, (1, 1, 1))

    def look(self, f, side=0.0, up=0.0, dur=4):
        for p in self.pupils:
            p.keyframe_insert("location", frame=f - dur)
            p.location = (0.075, side * 0.07, up * 0.06); p.keyframe_insert("location", frame=f)

    def mouth(self, f, is_open):
        a, b = (self.open, self.smile) if is_open else (self.smile, self.open)
        key(a, "scale", f - 2); key(a, "scale", f, (1, 1, 1))
        key(b, "scale", f - 2); key(b, "scale", f, (0, 0, 0))

    def big_eyes(self, f, dur=14):
        for e in self.eyes:
            key(e, "scale", f - 2, (1, 1, 1)); key(e, "scale", f + 2, (1, 1.25, 1.3)); key(e, "scale", f + dur, (1, 1.25, 1.3)); key(e, "scale", f + dur + 4, (1, 1, 1))


# ------------------------------------------------------------------ world
G = dict(grass=(0.22, 0.78, 0.12), grass2=(0.48, 0.86, 0.33), hill=(0.45, 0.85, 0.10), hill2=(0.10, 0.75, 0.45), far=(0.35, 0.70, 0.95),
         path=(1.0, 0.72, 0.30), bush=(0.14, 0.58, 0.20), bush2=(0.22, 0.68, 0.24), trunk=(0.55, 0.36, 0.18), crown=(0.20, 0.66, 0.28),
         crown2=(0.34, 0.76, 0.30), hay=(0.50, 0.56, 0.90), rock=(0.62, 0.64, 0.70), cap=(0.95, 0.20, 0.22), cloud=(1, 1, 1))


def world():
    w = bpy.data.worlds.new("w"); S.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes["Background"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], ramp.inputs[0])
    ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (0.55, 0.88, 1.0, 1)
    ramp.color_ramp.elements[1].position = 0.6; ramp.color_ramp.elements[1].color = (0.05, 0.42, 1.0, 1)
    lp = nt.nodes.new("ShaderNodeLightPath"); mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "FLOAT"
    mx.inputs[2].default_value = 0.55; mx.inputs[3].default_value = 1.0          # lighting strength / what the camera sees
    nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs[0]); nt.links.new(mx.outputs[0], bg.inputs["Strength"])
    nt.links.new(ramp.outputs[0], bg.inputs["Color"])
    sun = bpy.data.lights.new("sun", "SUN"); sun.energy = 2.7; sun.angle = R(12)
    so = bpy.data.objects.new("sun", sun); COLL.objects.link(so); so.rotation_euler = (R(50), 0, R(-28))
    sphere("ground", 1, mat("grass", G["grass"], rough=0.9), loc=(100, 60, -0.02), scale=(400, 400, 0.001), u=48, v=8)


def bush(x, y, s=1.0, seed=0, parent=None):
    rnd = random.Random(seed); e = empty("bush", (x, y, 0), parent)
    for i in range(7):
        a = i * 0.9; rr = 0.0 if i == 0 else 0.55 * s
        sphere("b", (0.75 if i == 0 else rnd.uniform(0.42, 0.6)) * s, mat("bush" + str(i % 2), G["bush2" if i % 2 else "bush"], rough=0.8), e,
               (math.cos(a) * rr * 1.5, math.sin(a) * rr * 0.6, (0.72 if i == 0 else rnd.uniform(0.3, 0.5)) * s), u=16, v=10)
    return e


def tree(x, y, s=1.0, seed=0, kind=0):
    rnd = random.Random(seed); e = empty("tree", (x, y, 0))
    cyl("trunk", 0.22 * s, 1.8 * s, mat("trunk", G["trunk"], rough=0.8), e, (0, 0, 0.9 * s), r2=0.16 * s, seg=12)
    cc = [(0.10, 0.62, 0.20), (0.45, 0.82, 0.10), (1.0, 0.45, 0.65), (1.0, 0.60, 0.10), (0.15, 0.70, 0.60), (0.95, 0.85, 0.15)][(seed + kind) % 6]
    m = mat("crown%d" % ((seed + kind) % 6), cc, rough=0.8)
    for (dx, dz, r) in ((0, 2.6, 1.15), (-0.75, 2.1, 0.8), (0.75, 2.1, 0.85), (0.1, 3.4, 0.75)):
        sphere("c", r * s, m, e, (dx * s, rnd.uniform(-0.2, 0.2) * s, dz * s), u=16, v=10)
    return e


def flower(x, y, col, s=1.0):
    e = empty("flower", (x, y, 0))
    cyl("st", 0.025 * s, 0.4 * s, mat("leaf", C["leaf"]), e, (0, 0, 0.2 * s), seg=6)
    sphere("c", 0.07 * s, mat("fl_c", (1.0, 0.85, 0.1)), e, (0, 0, 0.42 * s), u=8, v=6)
    for i in range(5):
        a = i * 1.257
        sphere("p", 0.075 * s, mat("fl%d" % (hash(col) % 999), col, rough=0.5), e, (math.cos(a) * 0.1 * s, math.sin(a) * 0.1 * s, 0.42 * s), scale=(1, 1, 0.5), u=8, v=6)
    return e


def cloud(x, y, z, s=1.0):
    e = empty("cloud", (x, y, z)); m = mat("cloud", G["cloud"], rough=1.0, emit=0.35)
    for (dx, dz, r) in ((0, 0, 1.0), (-1.1, -0.15, 0.75), (1.1, -0.2, 0.8), (0.4, 0.45, 0.7), (-0.5, 0.35, 0.6)):
        sphere("c", r * s, m, e, (dx * s, 0, dz * s), scale=(1, 0.6, 0.8), u=16, v=10)
    return e


def mushroom(x, y, s=1.0):
    e = empty("mushroom", (x, y, 0))
    cyl("st", 0.5 * s, 1.5 * s, mat("cream", C["cream"], rough=0.6), e, (0, 0, 0.75 * s), r2=0.36 * s, seg=20)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.6 * s)
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, 0), plane_no=(0, 0, -1), clear_outer=True)
    bmesh.ops.holes_fill(bm, edges=bm.edges)
    cap = obj("cap", bm, mat("cap", G["cap"], rough=0.35), e, (0, 0, 1.4 * s), scale=(1, 1, 0.75))
    for (a, t) in ((0.3, 0.5), (1.6, 0.75), (2.8, 0.45), (4.0, 0.7), (5.2, 0.5), (0.9, 1.15), (3.4, 1.2)):
        d = Vector((math.cos(a) * math.sin(t), math.sin(a) * math.sin(t), math.cos(t)))
        sphere("dot", 0.22 * s, mat("white", C["white"], rough=0.5), e, (d.x * 1.6 * s, d.y * 1.6 * s, 1.4 * s + d.z * 1.2 * s), scale=(1, 1, 0.5), u=12, v=8)
    return e


def haystack(x, y, s=1.0):
    e = empty("hay", (x, y, 0)); m = mat("hay", G["hay"], rough=0.9)
    sphere("h", 1.5 * s, m, e, (0, 0, 0.55 * s), scale=(1.15, 0.9, 1.25), u=24, v=14)
    sphere("h2", 0.8 * s, mat("hay2", (0.62, 0.66, 0.95), rough=0.9), e, (0, 0, 2.15 * s), scale=(1, 0.9, 0.7), u=16, v=10)
    return e


def rock(x, y, s=1.0):
    e = empty("rock", (x, y, 0)); m = mat("rock", G["rock"], rough=0.8)
    sphere("r", 1.4 * s, m, e, (0, 0, 0.6 * s), scale=(1.25, 0.8, 1.0), u=10, v=6).data.polygons.foreach_set("use_smooth", [False] * 0 or [])
    sphere("r2", 0.8 * s, mat("rock2", (0.72, 0.74, 0.80), rough=0.8), e, (1.2 * s, -0.3 * s, 0.35 * s), scale=(1, 0.8, 0.8), u=10, v=6)
    return e


def fence(x, y, n=4):
    e = empty("fence", (x, y, 0)); m = mat("fence", (1, 1, 1), rough=0.6)
    pc = [(1, 0.2, 0.25), (1, 0.6, 0.1), (1, 0.85, 0.1), (0.3, 0.8, 0.25), (0.2, 0.6, 1.0), (0.65, 0.35, 0.95)]
    for i in range(n):
        k = (i + int(abs(x))) % 6
        box("post", (0.16, 0.14, 0.95), mat("picket%d" % k, pc[k], rough=0.5), e, (i * 0.9, 0, 0.47), bevel=0.03)
    for z in (0.35, 0.68):
        box("rail", (n * 0.9 - 0.7, 0.07, 0.12), m, e, ((n - 1) * 0.45, 0, z), bevel=0.02)
    return e


def rainbow(x, y, z=0.0, s=1.0):
    cols = [(1, 0.1, 0.15), (1, 0.5, 0.05), (1, 0.9, 0.1), (0.2, 0.85, 0.2), (0.1, 0.55, 1.0), (0.55, 0.25, 0.95)]
    for i, c in enumerate(cols):
        torus("rainbow", (13 - i * 0.75) * s, 0.4 * s, mat("rb%d" % i, c, rough=0.6, emit=0.55), loc=(x, y, z), rot=(R(90), 0, 0), arc=(0, 180), seg=48)


def sun_disc(x, y, z, s=1.0):
    e = empty("sunface", (x, y, z)); m = mat("sunface", (1.0, 0.88, 0.1), emit=1.0)
    sphere("d", 2.0 * s, m, e, scale=(1, 0.3, 1))
    for i in range(12):
        a = i * math.pi / 6
        cyl("ray", 0.32 * s, 1.1 * s, m, e, (math.cos(a) * 2.9 * s, 0, math.sin(a) * 2.9 * s), rot=(0, R(90) - a, 0), r2=0.0, seg=8)
    key(e, "rotation_euler", 0, (0, 0, 0)); key(e, "rotation_euler", N, (0, N / 240 * math.pi, 0))
    return e


def balloons(x, y, z, seed=0):
    rnd = random.Random(seed); cols = [(1, 0.15, 0.25), (1, 0.8, 0.1), (0.2, 0.6, 1), (0.4, 0.85, 0.25), (0.8, 0.35, 1), (1, 0.5, 0.1)]
    for i in range(3):
        e = empty("balloon", (x + i * 0.9 - 0.9, y, z + (0.5 if i == 1 else 0)))
        sphere("b", 0.5, mat("bal%d" % ((seed + i) % 6), cols[(seed + i) % 6], rough=0.2, spec=0.9), e, scale=(1, 1, 1.2))
        cyl("s", 0.012, 1.6, mat("white", C["white"]), e, (0, 0, -1.35), seg=6)
        ph = rnd.uniform(0, 6)
        for f in range(0, N + 24, 24):
            key(e, "location", f, e.location.z + 0.25 * math.sin(f / 24 * 1.6 + ph), 2)


def small_mushroom(x, y, col, s=1.0):
    e = empty("mush", (x, y, 0))
    cyl("st", 0.09 * s, 0.3 * s, mat("cream", C["cream"]), e, (0, 0, 0.15 * s), seg=10)
    sphere("cap", 0.26 * s, mat("mc%d" % (hash(col) % 999), col, rough=0.35), e, (0, 0, 0.32 * s), scale=(1, 1, 0.6), u=16, v=8)
    for a in (0.4, 2.3, 4.4):
        sphere("d", 0.05 * s, mat("white", C["white"]), e, (math.cos(a) * 0.15 * s, math.sin(a) * 0.15 * s, 0.42 * s), scale=(1, 1, 0.5), u=8, v=6)


def area(x0, seed, hide=None):
    """Scenery around a spot on the road (camera looks from -Y towards +Y)."""
    rnd = random.Random(seed)
    for i in range(3):                                  # rolling hills behind
        hx = x0 + rnd.uniform(-14, 14); hy = 16 + i * 11
        sphere("hill", 1, mat("hill%d" % i, (G["hill"], G["hill2"], G["far"])[i], rough=0.9), loc=(hx, hy, -3 - i),
               scale=(rnd.uniform(14, 20), 10, rnd.uniform(7, 9) + i * 2.5), u=32, v=16)
        sphere("hill", 1, mat("hill%d" % i, G["hill"]), loc=(hx + rnd.choice((-1, 1)) * rnd.uniform(18, 24), hy + 3, -3 - i),
               scale=(rnd.uniform(12, 16), 10, rnd.uniform(5, 7) + i * 2.5), u=32, v=16)
    box("road", (40, 5.2, 0.04), mat("path", G["path"], rough=0.9), loc=(x0, -0.6, 0.0))
    for sd in (1, -1):
        box("edge", (40, 0.18, 0.1), mat("edge", (1.0, 1.0, 1.0), rough=0.9), loc=(x0, -0.6 + sd * 2.6, 0.0))
    spots = [(-5.2, 6.5), (5.6, 7.5), (-7.5, 11), (7.8, 12.5), (0.5, 14), (-3.5, 17), (4, 18)]
    for i, (dx, dy) in enumerate(spots):
        tree(x0 + dx + rnd.uniform(-0.6, 0.6), dy, rnd.uniform(0.9, 1.4), seed + i, i % 2)
    for i in range(9):
        dx = rnd.uniform(-9, 9); dy = rnd.uniform(3.4, 9)
        if abs(dx) < 2.6 and dy < 6:
            continue
        bush(x0 + dx, dy, rnd.uniform(0.5, 0.9), seed + i)
    cols = [(1, 0.15, 0.5), (1, 1, 1), (0.55, 0.25, 1.0), (1.0, 0.5, 0.05), (1.0, 0.1, 0.15)]
    for i in range(60):
        dx = rnd.uniform(-10, 10); dy = rnd.choice((rnd.uniform(-6.5, -3.6), rnd.uniform(2.4, 8)))
        if hide and abs(dx - hide[0]) < 2.6 and abs(dy - hide[1]) < 2.2:
            continue
        flower(x0 + dx, dy, cols[i % 5], rnd.uniform(0.8, 1.3))
    for i in range(26):
        dx = rnd.uniform(-7, 7)
        flower(x0 + dx, rnd.uniform(-6.0, -4.0), cols[i % 5], rnd.uniform(0.9, 1.25))
    for dx in (-5.2, 5.0, -8.0, 8.2):
        bush(x0 + dx + rnd.uniform(-0.5, 0.5), rnd.uniform(-5.6, -4.6), rnd.uniform(0.55, 0.8), seed + int(dx * 3))
    for i in range(4):
        fence(x0 - 9.5 + i * 5.4 + rnd.uniform(0, 1), 2.5 if i % 2 else 2.7, 3)
    for i in range(5):
        cloud(x0 + rnd.uniform(-16, 16), 42 + i * 2, rnd.uniform(15, 30), rnd.uniform(1.6, 3.0))
    rainbow(x0 + rnd.uniform(-2, 2), 30, -1.0, 1.0)
    sun_disc(x0 + rnd.choice((-1, 1)) * 5.0, 34, 21, 1.0)
    balloons(x0 + rnd.choice((-4.5, 4.5)), 9, 6.0, seed)
    balloons(x0 + rnd.choice((-7.5, 7.5)), 14, 8.5, seed + 3)
    mc = [(1.0, 0.15, 0.2), (0.6, 0.3, 0.95), (0.1, 0.6, 1.0), (1.0, 0.55, 0.1), (1.0, 0.35, 0.7)]
    for i in range(12):
        dx = rnd.uniform(-8, 8); dy = rnd.choice((rnd.uniform(-5.6, -3.5), rnd.uniform(2.3, 3.2)))
        if hide and abs(dx - hide[0]) < 2.6 and dy > 0:
            continue
        small_mushroom(x0 + dx, dy, mc[i % 5], rnd.uniform(0.9, 1.5))
    for i in range(3):
        sphere("st", rnd.uniform(0.12, 0.22), mat("rock", G["rock"]), loc=(x0 + rnd.uniform(-8, 8), rnd.choice((-3.6, 2.3)), 0.05), scale=(1, 0.8, 0.6), u=8, v=6)


# ------------------------------------------------------------------ effects, camera
def stars(center, f, n=14, seed=1, spread=2.6, col=(1.0, 0.85, 0.1)):
    rnd = random.Random(seed); m = mat("star%d" % (hash(col) % 99), col, emit=1.2)
    for i in range(n):
        bm = bmesh.new()
        pts = [Vector((math.cos(k * math.pi / 5 + math.pi / 2) * (0.22 if k % 2 == 0 else 0.1), 0.0, math.sin(k * math.pi / 5 + math.pi / 2) * (0.22 if k % 2 == 0 else 0.1))) for k in range(10)]
        c1 = bm.verts.new((0, -0.06, 0)); c2 = bm.verts.new((0, 0.06, 0)); vs = [bm.verts.new(p) for p in pts]
        for k in range(10):
            bm.faces.new((c1, vs[k], vs[(k + 1) % 10])); bm.faces.new((c2, vs[(k + 1) % 10], vs[k]))
        o = obj("star", bm, m, loc=center, smooth=False)
        a = rnd.uniform(0, 2 * math.pi); d = rnd.uniform(0.6, 1.0) * spread
        key(o, "scale", f - 1, (0, 0, 0)); key(o, "location", f, center); key(o, "scale", f + 3, (1.3, 1.3, 1.3))
        key(o, "rotation_euler", f, (0, 0, 0))
        key(o, "location", f + 16, (center[0] + math.cos(a) * d, center[1] - 0.3, center[2] + math.sin(a) * d * 0.9 + 0.4))
        key(o, "rotation_euler", f + 22, (0, rnd.uniform(-3, 3), 0))
        key(o, "scale", f + 14, (1.0, 1.0, 1.0)); key(o, "scale", f + 24, (0, 0, 0))


def question(loc, f0, f1):
    cu = bpy.data.curves.new("q", "FONT"); cu.body = "?"; cu.extrude = 0.08; cu.bevel_depth = 0.03; cu.align_x = "CENTER"; cu.size = 1.3
    o = bpy.data.objects.new("q", cu); COLL.objects.link(o); cu.materials.append(mat("q", (1.0, 0.85, 0.1), emit=0.5))
    o.location = loc; o.rotation_euler = (R(80), 0, 0)
    key(o, "scale", f0 - 1, (0, 0, 0)); key(o, "scale", f0 + 5, (1.25, 1.25, 1.25)); key(o, "scale", f0 + 9, (1, 1, 1))
    for f in range(f0 + 9, f1, 12):
        key(o, "rotation_euler", f, (R(80), 0, R(12))); key(o, "rotation_euler", f + 6, (R(80), 0, R(-12)))
    key(o, "scale", f1 - 4, (1, 1, 1)); key(o, "scale", f1, (0, 0, 0))
    return o


def confetti(center, f, n=70, seed=5, spread=6.0, top=9.0):
    rnd = random.Random(seed)
    cols = [(1, 0.2, 0.3), (1, 0.8, 0.1), (0.2, 0.7, 1), (0.4, 0.9, 0.3), (0.8, 0.4, 1), (1, 0.5, 0.1)]
    for i in range(n):
        o = box("conf", (0.16, 0.02, 0.1), mat("conf%d" % (i % 6), cols[i % 6], emit=0.4))
        x = center[0] + rnd.uniform(-spread, spread); y = center[1] + rnd.uniform(-2.5, 1.0); fs = f + rnd.randint(0, 40)
        key(o, "location", fs - 1, (x, y, top + 4)); key(o, "location", fs, (x, y, top)); key(o, "rotation_euler", fs, (0, 0, 0))
        key(o, "location", fs + rnd.randint(70, 110), (x + rnd.uniform(-1.5, 1.5), y, -0.3)); key(o, "rotation_euler", fs + 100, (rnd.uniform(5, 14), rnd.uniform(5, 14), rnd.uniform(3, 9)))


cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); COLL.objects.link(cam); S.camera = cam
aim = empty("aim"); tr = cam.constraints.new("TRACK_TO"); tr.target = aim; tr.track_axis = "TRACK_NEGATIVE_Z"; tr.up_axis = "UP_Y"
cam.data.lens = 32; cam.data.sensor_fit = "VERTICAL"; cam.data.sensor_height = 36
_first = [True]


def shot(f0, f1, p0, a0, p1=None, a1=None, lens=None):
    """Camera from p0 looking at a0, easing to p1/a1 by f1.  A cut happens at f0."""
    if not _first[0]:
        cam.keyframe_insert("location", frame=f0 - 1); aim.keyframe_insert("location", frame=f0 - 1); cam.data.keyframe_insert("lens", frame=f0 - 1)
    _first[0] = False
    if lens:
        cam.data.lens = lens
    cam.data.keyframe_insert("lens", frame=f0)
    key(cam, "location", f0, p0); key(aim, "location", f0, a0)
    key(cam, "location", f1 - 1, p1 or p0); key(aim, "location", f1 - 1, a1 or a0)
    cam.data.keyframe_insert("lens", frame=f1 - 1)


# ------------------------------------------------------------------ the story
world()
truck = Car("cilek")
T0 = 0.0
area(T0, 1)
tree(T0 - 3.4, 3.6, 1.3, 77, 1); bush(T0 + 3.6, 3.3, 0.9, 5)

# --- intro (0 - 120): the strawberry truck rolls in and starts looking for its friends
truck.place(0, T0 - 9, -0.6, 0, cut=False)
truck.move(0, 40, T0 - 0.3, -0.6, -52)
truck.squash(42); truck.blink(50); truck.mouth(0, False)
shot(0, 96, (T0 + 0.8, -10.0, 1.5), (T0 - 0.5, 0, 2.0), (T0 + 0.4, -7.6, 1.4), (T0 - 0.1, 0, 1.9), lens=30)
truck.look(56, 1); truck.turn(52, 60, -30); truck.look(72, -1); truck.turn(68, 78, -95); truck.blink(82)
truck.look(90, 0); truck.turn(86, 94, -62)
question((T0 + 0.2, -0.6, 3.5), 54, 94)


def seeker(f0, f1):
    """Short cut-away: the truck looks around."""
    truck.place(f0, T0, -0.6, -62)
    truck.look(f0, 0, dur=1)
    shot(f0, f1, (T0 + 0.4, -7.8, 1.4), (T0, 0, 1.9), (T0 + 0.2, -7.2, 1.4), (T0, 0, 1.9), lens=32)
    truck.look(f0 + 10, 1); truck.turn(f0 + 6, f0 + 16, -35); truck.look(f0 + 30, -1); truck.turn(f0 + 26, f0 + 38, -92)
    truck.blink(f0 + 22); question((T0 + 0.2, -0.6, 3.5), f0 + 6, f1 - 2)
    truck.look(f1 - 6, 0); truck.turn(f1 - 10, f1 - 2, -62)


def found(car, f, x0, hx, side=1):
    """Shared ending of a round: the friend is out at (x0 + side*2.4, -0.9); the truck drives in and both hop."""
    truck.place(f, x0 - side * 9.5, -1.4, 0 if side > 0 else 180)
    truck.move(f + 2, f + 34, x0 - side * 1.6, -0.7, -90 + side * 22)
    truck.squash(f + 36); truck.mouth(f + 30, True); truck.look(f + 30, -side * 0.6, dur=2)
    car.look(f + 26, side * 0.8 * (-1), dur=6)
    truck.hop(f + 44, 0.55, 12, 2); car.hop(f + 50, 0.6, 12, 2)
    truck.blink(f + 40); car.blink(f + 46)
    truck.mouth(f + 86, False); truck.look(f + 88, 0)


def round_orange(f0):
    """Behind a big bush: leaves shake, the orange car hops out."""
    x0 = 40.0; car = Car("portakal"); area(x0, 2, hide=(0, 1.2))
    hb = bush(x0, 0.9, 2.0, 11); bush(x0 - 2.6, 1.4, 1.2, 12)
    car.place(0, x0 + 0.2, 3.4, -90, cut=False); car.mouth(0, False)
    seeker(f0, f0 + 56)
    a = f0 + 56
    shot(a, a + 60, (x0 + 0.4, -10.0, 1.5), (x0 + 0.2, 0.5, 2.3), (x0 + 0.6, -8.8, 1.5), (x0 + 0.4, 0.5, 2.3), lens=32)
    for f in range(a + 6, a + 44, 5):                       # the bush rustles
        key(hb, "rotation_euler", f, (0, R(4) * (1 if (f // 5) % 2 else -1), 0)); key(hb, "scale", f, (1.03, 1.0, 0.98) if (f // 5) % 2 else (0.98, 1, 1.03))
    key(hb, "rotation_euler", a + 46, (0, 0, 0)); key(hb, "scale", a + 46, (1, 1, 1))
    # peek: rises behind the bush, eyes over the top
    key(car.b, "location", a + 14, (0, 0, 0)); key(car.b, "location", a + 24, (0, 0, 1.75)); car.look(a + 26, -1); car.look(a + 36, 1)
    car.blink(a + 31); key(car.b, "location", a + 40, (0, 0, 1.75)); key(car.b, "location", a + 46, (0, 0, 0))
    b = a + 60                                              # jump out
    shot(b, b + 112, (x0 + 1.2, -8.8, 1.4), (x0 + 1.2, -1.0, 1.9), (x0 + 0.1, -12.2, 1.6), (x0, -1.0, 2.0), lens=32)
    car.root.keyframe_insert("location", frame=b + 2); car.root.keyframe_insert("rotation_euler", frame=b + 2)
    car.root.location = (x0 + 1.5, -1.7, 0); car.root.rotation_euler = (0, 0, R(-76)); car.pos = (x0 + 1.5, -1.7)
    car.root.keyframe_insert("location", frame=b + 18); car.root.keyframe_insert("rotation_euler", frame=b + 18)
    key(car.b, "location", b + 2, (0, 0, 0)); key(car.b, "location", b + 10, (0, 0, 2.6)); key(car.b, "location", b + 18, (0, 0, 0))
    key(car.b, "rotation_euler", b + 2, (0, 0, 0)); key(car.b, "rotation_euler", b + 10, (0, R(-14), 0)); key(car.b, "rotation_euler", b + 18, (0, 0, 0))
    car.squash(b + 19, 0.2); car.mouth(b + 12, True); car.big_eyes(b + 12, 10); car.look(b + 12, 0)
    stars((x0 + 1.6, -2.0, 2.2), b + 19, seed=3)
    car.blink(b + 34)
    found(car, b + 22, x0, 0.9, side=1)
    return car, b + 112


def round_banana(f0):
    """Behind a haystack: the long banana bus cannot quite hide - its ends stick out."""
    x0 = 80.0; car = Car("muz"); area(x0, 3, hide=(0, 1.2))
    hs = haystack(x0, 0.6, 1.0); haystack(x0 + 4.6, 3.2, 0.6)
    car.place(0, x0 - 0.2, 2.6, 180, cut=False); car.mouth(0, False)
    seeker(f0, f0 + 50)
    a = f0 + 50
    shot(a, a + 64, (x0 - 0.4, -10.4, 1.5), (x0 - 0.4, 0.5, 2.2), (x0 - 1.0, -9.2, 1.5), (x0 - 1.0, 0.4, 2.1), lens=32)
    # slides out to the left, peeks with its face, slides back
    car.move(a + 8, a + 22, x0 - 2.3, 2.6); car.look(a + 24, 0, 0); car.turn(a + 20, a + 28, 235)
    car.blink(a + 32); car.look(a + 38, -1); car.big_eyes(a + 40, 6)
    car.turn(a + 48, a + 52, 180); car.move(a + 50, a + 60, x0 - 0.2, 2.6, back=True)
    b = a + 64
    shot(b, b + 114, (x0 - 1.4, -9.6, 1.4), (x0 - 1.6, -0.5, 1.9), (x0 - 0.1, -12.6, 1.6), (x0, -1.0, 2.0), lens=32)
    car.move(b + 2, b + 20, x0 - 3.6, 2.2, 225)
    car.move(b + 20, b + 40, x0 - 1.7, -1.9, 296)
    car.squash(b + 42, 0.14); car.mouth(b + 30, True); car.big_eyes(b + 30, 10); car.look(b + 30, 0)
    stars((x0 - 1.7, -2.3, 2.0), b + 42, seed=7)
    for f in range(a + 6, a + 26, 5):
        key(hs, "scale", f, (1.03, 1, 0.98) if (f // 5) % 2 else (0.98, 1, 1.03))
    key(hs, "scale", a + 28, (1, 1, 1))
    found(car, b + 24, x0, 0.6, side=-1)
    return car, b + 114


f = 96
c1, f = round_orange(f)
c2, f = round_banana(f)
print("END", f, "of", N)
os.makedirs(os.path.join(HERE, "build"), exist_ok=True)
S.render.filepath = "//kareler/f_"
S.render.use_overwrite = False; S.render.use_placeholder = True
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "build", "meyve.blend"))
print("BUILT")
