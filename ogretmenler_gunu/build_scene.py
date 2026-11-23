# -*- coding: utf-8 -*-
"""
Kiddie TV - "Canım Öğretmen Kutlu Olsun" 3D klip sahnesi (Blender 5.2)

Kullanım (sahneyi sıfırdan kurar ve .blend olarak kaydeder):
    blender -b --factory-startup -P build_scene.py -- [--out ogretmenler_gunu.blend]

Tüm karakterler (tren, renkli arabalar, güneş, kalp) ve mekanlar (okul bahçesi,
sınıf) bu script içinde prosedürel olarak modellenir. Animasyonlar şarkının
kelime ve vuruş zamanlarına (assets/words.json, assets/beats.json) bağlıdır.
"""
import bpy, bmesh, math, json, os, sys, random
from mathutils import Vector, Matrix, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = os.path.join(HERE, "ogretmenler_gunu.blend")
if "--out" in argv:
    OUT = os.path.abspath(argv[argv.index("--out") + 1])

FPS = 30
DUR = 74.0
FRAME_END = int(DUR * FPS)          # 2220
RNG = random.Random(24112026)
WARN = []                            # hata filtresi için uyarılar


def F(t):
    return int(round(t * FPS)) + 1


WORDS = json.load(open(os.path.join(ASSETS, "words.json"), encoding="utf-8"))
BEATS = json.load(open(os.path.join(ASSETS, "beats.json")))

# Satır başları (kıta) ve "Canım öğretmenim" (nakarat) zamanları
LINES = []
for i, w in enumerate(WORDS):
    if w[0] in ("Öğretmenler", "Kalbin", "Sevgin", "Her"):
        LINES.append(w[1])
REFRAINS = [(w[1], WORDS[i + 1][2]) for i, w in enumerate(WORDS) if w[0] == "Canım"]
assert len(LINES) == 8 and len(REFRAINS) == 8, (LINES, REFRAINS)


def in_refrain(t, pad=0.3):
    return any(a - pad <= t <= b + pad for a, b in REFRAINS)


# ----------------------------------------------------------------------------
# Temizlik ve sahne ayarları
# ----------------------------------------------------------------------------
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.curves):
    for d in list(coll):
        coll.remove(d)

scene = bpy.context.scene
scene.name = "Sahne3D"
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = FRAME_END
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.render.engine = "BLENDER_EEVEE"
try:
    scene.eevee.taa_render_samples = 32
    scene.eevee.use_shadows = True
except Exception:
    pass
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
COLL = scene.collection

INTERP = ["BEZIER"]
FCURVES = set()


def interp(kind):
    INTERP[0] = kind


def _fcurve(idb, path, index):
    ad = idb.animation_data_create()
    if ad.action is None:
        ad.action = bpy.data.actions.new(idb.name + "_anim")
    fc = ad.action.fcurve_ensure_for_datablock(idb, path, index=index)
    FCURVES.add(fc)
    return fc


def kf(idb, path, frame, values):
    """Anahtar kareyi doğrudan F-Curve'e yazar (geçiş tipi INTERP[0])."""
    vals = values if isinstance(values, (tuple, list)) or hasattr(values, "__len__") else [values]
    single = not (isinstance(values, (tuple, list)) or hasattr(values, "__len__"))
    for i, v in enumerate(vals):
        fc = _fcurve(idb, path, -1 if False else (0 if single else i))
        k = fc.keyframe_points.insert(frame, float(v), options={"FAST"})
        k.interpolation = INTERP[0]

# ----------------------------------------------------------------------------
# Yardımcılar: renk, malzeme, mesh, nesne
# ----------------------------------------------------------------------------

def hexc(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


MATS = {}


def mat(name, hexcol, rough=0.45, emit=0.0, spec=0.35):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    b = m.node_tree.nodes.get("Principled BSDF")
    col = hexc(hexcol)
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    try:
        b.inputs["Specular IOR Level"].default_value = spec
    except Exception:
        pass
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1)
        b.inputs["Emission Strength"].default_value = emit
    m.diffuse_color = (*col, 1)
    MATS[name] = m
    return m


def bsdf(m):
    return m.node_tree.nodes.get("Principled BSDF")


MESHES = {}


def _finish(bm, name, smooth=True):
    if smooth:
        for f in bm.faces:
            f.smooth = True
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(None)
    return me


def box_mesh(dx, dy, dz, bev=0.0):
    key = ("box", round(dx, 3), round(dy, 3), round(dz, 3), round(bev, 3))
    if key in MESHES:
        return MESHES[key]
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= dx; v.co.y *= dy; v.co.z *= dz
    if bev > 0:
        bev = min(bev, 0.49 * min(dx, dy, dz))
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bev, segments=4, profile=0.5, affect="EDGES")
    me = _finish(bm, "box", smooth=bev > 0)
    MESHES[key] = me
    return me


def sphere_mesh():
    if "sphere" in MESHES:
        return MESHES["sphere"]
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=0.5)
    MESHES["sphere"] = _finish(bm, "sphere")
    return MESHES["sphere"]


def cyl_mesh(r=0.5, depth=1.0, r2=None, seg=32, bev=0.04):
    key = ("cyl", r, depth, r2, seg, bev)
    if key in MESHES:
        return MESHES[key]
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                          radius1=r, radius2=r if r2 is None else r2, depth=depth)
    if bev > 0:
        rim = [e for e in bm.edges if not e.is_manifold or
               (len(e.link_faces) == 2 and abs(e.link_faces[0].normal.dot(e.link_faces[1].normal)) < 0.5)]
        bmesh.ops.bevel(bm, geom=rim, offset=bev, segments=3, profile=0.5, affect="EDGES")
    MESHES[key] = _finish(bm, "cyl")
    return MESHES[key]


def torus_mesh(R, r, half=False, seg=48, rseg=12):
    key = ("torus", R, r, half, seg)
    if key in MESHES:
        return MESHES[key]
    bm = bmesh.new()
    rings = []
    n = seg // 2 + 1 if half else seg
    for i in range(n):
        a = (math.pi * i / (n - 1)) if half else 2 * math.pi * i / seg
        c = Vector((math.cos(a) * R, math.sin(a) * R, 0))
        d = Vector((math.cos(a), math.sin(a), 0))
        ring = []
        for j in range(rseg):
            b = 2 * math.pi * j / rseg
            ring.append(bm.verts.new(c + d * (math.cos(b) * r) + Vector((0, 0, math.sin(b) * r))))
        rings.append(ring)
    for i in range(n if not half else n - 1):
        r0, r1 = rings[i], rings[(i + 1) % n]
        for j in range(rseg):
            bm.faces.new((r0[j], r0[(j + 1) % rseg], r1[(j + 1) % rseg], r1[j]))
    if half:
        for ring in (rings[0], rings[-1]):
            bm.faces.new(ring)
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    MESHES[key] = _finish(bm, "torus")
    return MESHES[key]


def star_mesh(R=0.5, r=0.22, depth=0.08):
    key = ("star", R, r, depth)
    if key in MESHES:
        return MESHES[key]
    bm = bmesh.new()
    pts = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5
        rr = R if i % 2 == 0 else r
        pts.append(bm.verts.new((math.cos(a) * rr, math.sin(a) * rr, 0)))
    f = bm.faces.new(pts)
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]:
        v.co.z += depth
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    MESHES[key] = _finish(bm, "star", smooth=False)
    return MESHES[key]


def prism_mesh(length, width, height):
    key = ("prism", length, width, height)
    if key in MESHES:
        return MESHES[key]
    bm = bmesh.new()
    a = [bm.verts.new((-length / 2, -width / 2, 0)), bm.verts.new((-length / 2, width / 2, 0)),
         bm.verts.new((-length / 2, 0, height))]
    b = [bm.verts.new((length / 2, -width / 2, 0)), bm.verts.new((length / 2, width / 2, 0)),
         bm.verts.new((length / 2, 0, height))]
    bm.faces.new(a); bm.faces.new(b[::-1])
    for i in range(3):
        j = (i + 1) % 3
        bm.faces.new((a[i], b[i], b[j], a[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    MESHES[key] = _finish(bm, "prism", smooth=False)
    return MESHES[key]


def tri_flag_mesh():
    if "flag" in MESHES:
        return MESHES["flag"]
    bm = bmesh.new()
    v = [bm.verts.new((-0.45, 0, 0)), bm.verts.new((0.45, 0, 0)), bm.verts.new((0, 0, -0.9))]
    bm.faces.new(v)
    MESHES["flag"] = _finish(bm, "flag", smooth=False)
    return MESHES["flag"]


def plane_mesh(dx, dy):
    key = ("plane", dx, dy)
    if key in MESHES:
        return MESHES[key]
    bm = bmesh.new()
    v = [bm.verts.new((sx * dx / 2, sy * dy / 2, 0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    bm.faces.new(v)
    MESHES[key] = _finish(bm, "plane", smooth=False)
    return MESHES[key]


def heart_mesh(name, depth=0.36, rings=9):
    """Şişkin (yastık gibi) kalp: dış hattan merkeze doğru halkalar, ön/arka kubbe.
    XY düzleminde, kalınlık Z yönünde; alt uç orijinde."""
    n = 96
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append(Vector((x / 17.0, y / 17.0, 0)))
    miny = min(p.y for p in pts)
    for p in pts:
        p.y -= miny
    c = Vector((0, 0.62 * max(p.y for p in pts), 0))
    bm = bmesh.new()
    outline = [bm.verts.new(p) for p in pts]
    for side in (1, -1):
        prev = outline
        for k in range(1, rings + 1):
            th = (math.pi / 2) * k / (rings + 1)
            sc = math.cos(th)
            ring = [bm.verts.new(c + (p - c) * sc + Vector((0, 0, side * depth * math.sin(th)))) for p in pts]
            for i in range(n):
                j = (i + 1) % n
                q = (prev[i], prev[j], ring[j], ring[i])
                bm.faces.new(q if side == 1 else q[::-1])
            prev = ring
        tip = bm.verts.new(c + Vector((0, 0, side * depth)))
        for i in range(n):
            j = (i + 1) % n
            tri = (prev[i], prev[j], tip)
            bm.faces.new(tri if side == 1 else tri[::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _finish(bm, name)


HEART_DATA = None


def heart_data():
    global HEART_DATA
    if HEART_DATA is None:
        HEART_DATA = heart_mesh("kalp")
    return HEART_DATA


FONT = None


def font():
    global FONT
    if FONT is None:
        FONT = bpy.data.fonts.load(os.path.join(ASSETS, "Baloo2-ExtraBold.ttf"))
    return FONT


def text_data(name, body, size=1.0, extrude=0.08, bevel=0.02):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = font()
    cu.size = size
    cu.extrude = extrude
    cu.bevel_depth = bevel
    cu.bevel_resolution = 2
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.space_line = 0.85
    return cu


def obj(name, data=None, loc=(0, 0, 0), rot=(0, 0, 0), scl=1.0, m=None, parent=None):
    o = bpy.data.objects.new(name, data)
    COLL.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    o.scale = (scl, scl, scl) if isinstance(scl, (int, float)) else scl
    if parent is not None:
        o.parent = parent
    if m is not None and data is not None:
        if len(o.material_slots) == 0:
            data.materials.append(None)
        o.material_slots[0].link = "OBJECT"
        o.material_slots[0].material = m
    if data is None:
        o.empty_display_size = 0.5
    return o


def empty(name, loc=(0, 0, 0), rot=(0, 0, 0), parent=None):
    return obj(name, None, loc, rot, 1.0, None, parent)


def box(name, dims, loc, m, bev=0.06, parent=None, rot=(0, 0, 0)):
    return obj(name, box_mesh(*dims, bev), loc, rot, 1.0, m, parent)


def ball(name, loc, scl, m, parent=None, rot=(0, 0, 0)):
    return obj(name, sphere_mesh(), loc, rot, scl, m, parent)


def key(o, path, frame, value=None, index=-1):
    if value is not None:
        if index >= 0:
            getattr(o, path)[index] = value
        else:
            setattr(o, path, value)
    cur = getattr(o, path)
    if index >= 0:
        fc = _fcurve(o, path, index)
        k = fc.keyframe_points.insert(frame, float(cur[index]), options={"FAST"})
        k.interpolation = INTERP[0]
    elif hasattr(cur, "__len__"):
        kf(o, path, frame, tuple(cur))
    else:
        kf(o, path, frame, cur)


def key_scale(o, frame, s):
    o.scale = (s, s, s) if isinstance(s, (int, float)) else s
    kf(o, "scale", frame, tuple(o.scale))


def pop_in(o, t, final=1.0, dur=0.3):
    """Nesneyi t anında 0'dan 'final' ölçeğe zıplatarak getirir."""
    f = F(t)
    key_scale(o, 1, 0.0)
    key_scale(o, max(2, f - 1), 0.0)
    key_scale(o, f + int(dur * FPS * 0.6), final * 1.25)
    key_scale(o, f + int(dur * FPS), final)


def pop_out(o, t, cur=1.0, dur=0.2):
    f = F(t)
    key_scale(o, f - int(dur * FPS), cur)
    key_scale(o, f, 0.0)


# Renkler
C = dict(red="#FF4B4B", blue="#3D8BFF", yellow="#FFD233", green="#3CC86A", orange="#FF9A2E",
         purple="#9B5CFF", pink="#FF6FB5", cyan="#2FD3E0", white="#FFFFFF", black="#1A1A24",
         cream="#FFF4DC", brown="#8B5A3C", grass="#6DD45A", road="#6B6F7A", peach="#FFD5A8")

M_WHITE = mat("Beyaz", C["white"], 0.3)
M_EYE = mat("GozBeyaz", C["white"], 0.15, spec=0.6)
M_PUPIL = mat("GozBebek", C["black"], 0.1, spec=0.8)
M_SHINE = mat("GozParlak", C["white"], 0.1, emit=2.0)
M_MOUTH = mat("Agiz", "#5A1E2E", 0.35)
M_CHEEK = mat("Yanak", "#FF8FB1", 0.5)
M_TIRE = mat("Lastik", "#2B2B33", 0.7)
M_HUB = mat("Jant", "#E8E8F0", 0.25)
M_GLASS = mat("Cam", "#4FA9E8", 0.08, emit=0.05)
M_LAMP = mat("Far", "#FFF2A8", 0.2, emit=3.0)

# ----------------------------------------------------------------------------
# Karakter: yüz (göz + ağız + yanak), bir "yüz" boşluğuna bağlı, +X yönüne bakar
# ----------------------------------------------------------------------------
BLINKERS = []
SMILE_ROT = Matrix(((0, 0, -1), (1, 0, 0), (0, -1, 0))).to_euler()


def face(parent, loc, size=1.0, name="yuz", eye_gap=0.27, mouth_drop=0.42, cheeks=True):
    fe = empty(name, loc, parent=parent)
    s = size
    eyes = empty(name + "_gozler", (0, 0, 0), parent=fe)
    for sy in (-1, 1):
        y = sy * eye_gap * s
        ball(name + "_goz", (0.0, y, 0), (0.16 * s, 0.24 * s, 0.30 * s), M_EYE, eyes)
        ball(name + "_bebek", (0.09 * s, y - sy * 0.02 * s, -0.01 * s), (0.09 * s, 0.17 * s, 0.2 * s), M_PUPIL, eyes)
        ball(name + "_parlak", (0.125 * s, y - sy * 0.05 * s, 0.05 * s), (0.03 * s, 0.05 * s, 0.05 * s), M_SHINE, eyes)
    BLINKERS.append(eyes)
    # gülümseyen ağız: yarım torus, +X'e bakan düzlemde, aşağı kavisli
    # yarım torus XY düzleminde (+Y yarısı); SMILE_ROT ile YZ düzlemine, kavis aşağı bakacak şekilde döner
    obj(name + "_agiz", torus_mesh(0.5, 0.11, half=True), (0.02 * s, 0, -mouth_drop * s),
        SMILE_ROT, 0.36 * s, M_MOUTH, fe)
    if cheeks:
        for sy in (-1, 1):
            ball(name + "_yanak", (-0.02 * s, sy * 0.48 * s, -0.33 * s), (0.06 * s, 0.14 * s, 0.09 * s), M_CHEEK, fe)
    return fe


# ----------------------------------------------------------------------------
# Karakter: renkli araba. Kök (konum/yön) -> zıplatıcı (hop/squash) -> parçalar
# Araba +X yönüne bakar.
# ----------------------------------------------------------------------------

def make_car(name, color, loc=(0, 0, 0), heading=0.0):
    m = mat("Araba_" + color, C[color], 0.35)
    root = empty(name, loc, (0, 0, heading))
    hop = empty(name + "_zipla", (0, 0, 0), parent=root)
    box(name + "_govde", (2.3, 1.36, 0.72), (0, 0, 0.72), m, 0.28, hop)
    box(name + "_kabin", (1.25, 1.2, 0.78), (-0.28, 0, 1.38), m, 0.3, hop)
    box(name + "_tavan", (1.05, 1.0, 0.1), (-0.32, 0, 1.8), M_WHITE, 0.05, hop)
    # ön cam = yüz
    box(name + "_oncam", (0.06, 1.0, 0.56), (0.34, 0, 1.4), M_GLASS, 0.03, hop)
    face(hop, (0.39, 0, 1.43), 0.85, name + "_yuz", eye_gap=0.25, mouth_drop=0.0, cheeks=False)
    # tampon üzerinde gülümseme ve yanaklar
    smile = obj(name + "_gulus", torus_mesh(0.5, 0.11, half=True), (1.17, 0, 0.74),
                SMILE_ROT, 0.34, M_MOUTH, hop)
    for sy in (-1, 1):
        ball(name + "_yanak", (1.1, sy * 0.42, 0.62), (0.05, 0.13, 0.09), M_CHEEK, hop)
        ball(name + "_far", (1.1, sy * 0.47, 0.88), (0.08, 0.18, 0.15), M_LAMP, hop)
    # yan camlar
    for sy in (-1, 1):
        box(name + "_yancam", (0.75, 0.04, 0.42), (-0.32, sy * 0.6, 1.42), M_GLASS, 0.02, hop)
    # anten ve ponpon
    obj(name + "_anten", cyl_mesh(0.03, 0.7, bev=0.0), (-0.7, 0.3, 2.1), (0, 0, 0), 1.0, M_PUPIL, hop)
    ball(name + "_ponpon", (-0.7, 0.3, 2.5), 0.2, mat("Ponpon", C["yellow"], 0.4), hop)
    wheels = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            w = obj(name + "_teker", cyl_mesh(0.34, 0.3, bev=0.06), (sx * 0.72, sy * 0.66, 0.34),
                    (math.radians(90), 0, 0), 1.0, M_TIRE, hop)
            obj(name + "_jant", cyl_mesh(0.16, 0.06, bev=0.02), (0, 0, sy * -0.16), (0, 0, 0), 1.0, M_HUB, w)
            wheels.append(w)
    return dict(root=root, hop=hop, wheels=wheels, r=0.34, name=name)


# ----------------------------------------------------------------------------
# Karakter: tren (lokomotif + 3 vagon). +X yönüne bakar.
# ----------------------------------------------------------------------------
TRAIN_Z = 0.22  # ray üstü


def make_train():
    root = empty("Tren", (0, 10, TRAIN_Z))
    mr = mat("Tren_Kirmizi", C["red"], 0.3)
    mb = mat("Tren_Mavi", C["blue"], 0.3)
    my = mat("Tren_Sari", C["yellow"], 0.3)
    md = mat("Tren_Koyu", "#2C3E73", 0.4)
    wheels = []

    def wheel(par, x, r, mm):
        for sy in (-1, 1):
            w = obj("Tren_teker", cyl_mesh(r, 0.28, bev=0.05), (x, sy * 1.05, r), (math.radians(90), 0, 0), 1.0, mm, par)
            obj("Tren_jant", cyl_mesh(r * 0.45, 0.06, bev=0.02), (0, 0, sy * -0.15), (0, 0, 0), 1.0, my, w)
            wheels.append((w, r))

    loco = empty("Lokomotif", (0, 0, 0), parent=root)
    box("Lok_sasi", (5.4, 2.0, 0.5), (0, 0, 0.85), md, 0.12, loco)
    boiler = obj("Lok_kazan", cyl_mesh(0.95, 3.2, bev=0.12), (0.95, 0, 2.0), (0, math.radians(90), 0), 1.0, mr, loco)
    for x in (0.2, 1.3, 2.3):
        obj("Lok_bant", cyl_mesh(0.99, 0.14, bev=0.03), (x, 0, 2.0), (0, math.radians(90), 0), 1.0, my, loco)
    obj("Lok_yuzdisk", cyl_mesh(0.92, 0.16, bev=0.06), (2.62, 0, 2.0), (0, math.radians(90), 0), 1.0,
        mat("Tren_Yuz", "#FFF0DA", 0.5, emit=0.22), loco)
    face(loco, (2.72, 0, 2.18), 1.05, "Tren_yuz", eye_gap=0.3, mouth_drop=0.45)
    box("Lok_kabin", (1.9, 2.1, 2.2), (-1.55, 0, 2.15), mr, 0.18, loco)
    box("Lok_cati", (2.4, 2.5, 0.26), (-1.55, 0, 3.35), my, 0.1, loco)
    for sy in (-1, 1):
        box("Lok_pencere", (1.0, 0.06, 0.8), (-1.55, sy * 1.06, 2.55), M_GLASS, 0.05, loco)
    obj("Lok_baca", cyl_mesh(0.32, 1.1, bev=0.06), (1.85, 0, 3.3), (0, 0, 0), 1.0, md, loco)
    obj("Lok_baca_agiz", cyl_mesh(0.5, 0.3, r2=0.38, bev=0.05), (1.85, 0, 3.9), (math.radians(180), 0, 0), 1.0, md, loco)
    ball("Lok_kubbe", (0.55, 0, 2.95), 0.75, my, loco)
    box("Lok_tampon", (0.45, 2.1, 0.5), (2.85, 0, 0.85), my, 0.15, loco)
    for x in (-1.6, -0.1, 1.4):
        wheel(loco, x, 0.55, mb)
    puff_origin = (1.85, 0, 4.1)

    wagons = []
    wcols = [("green", "Yesil"), ("purple", "Mor"), ("orange", "Turuncu")]
    for i, (cname, tag) in enumerate(wcols):
        wg = empty("Vagon_" + tag, (-5.7 - i * 4.7, 0, 0), parent=root)
        mw = mat("Vagon_" + tag, C[cname], 0.35)
        box("Vagon_taban", (4.1, 2.1, 0.45), (0, 0, 1.0), mw, 0.12, wg)
        for sy in (-1, 1):
            box("Vagon_kenar", (4.1, 0.14, 0.55), (0, sy * 1.0, 1.45), mw, 0.06, wg)
        for sx in (-1, 1):
            box("Vagon_kenar", (0.14, 2.1, 0.55), (sx * 1.98, 0, 1.45), mw, 0.06, wg)
        box("Vagon_baglanti", (0.9, 0.25, 0.18), (2.45, 0, 0.95), md, 0.05, wg)
        for x in (-1.2, 1.2):
            wheel(wg, x, 0.45, mb)
        wagons.append(wg)
    return dict(root=root, wheels=wheels, wagons=wagons, puff=puff_origin, loco=loco)


# ----------------------------------------------------------------------------
# MEKAN 1: Okul bahçesi (z=0 zemin). Okul ön cephesi y=23, ray y=10, yol y=3
# ----------------------------------------------------------------------------
world = bpy.data.worlds.new("Gokyuzu")
scene.world = world
try:
    world.use_nodes = True
except Exception:
    pass
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (*hexc("#8FD3FF"), 1)
bg.inputs["Strength"].default_value = 1.0

M_GRASS = mat("Cimen", C["grass"], 0.85)
obj("Zemin", box_mesh(600, 600, 1.0, 0), (0, 0, -0.5), m=M_GRASS)
M_ROAD = mat("Yol", C["road"], 0.8)
obj("Yol", box_mesh(400, 4.2, 0.06, 0), (0, 3, 0.0), m=M_ROAD)
dash = obj("Yol_cizgi", box_mesh(1.6, 0.22, 0.02, 0), (-200, 3, 0.035), m=M_WHITE)
am = dash.modifiers.new("dizi", "ARRAY"); am.use_relative_offset = False; am.use_constant_offset = True
am.constant_offset_displace = (4.0, 0, 0); am.count = 100
M_RAIL = mat("Ray", "#9AA0AC", 0.3, spec=0.8)
M_SLEEPER = mat("Travers", "#8A5A3B", 0.8)
for sy in (-1, 1):
    obj("Ray", box_mesh(400, 0.16, 0.16, 0), (0, 10 + sy * 1.05, 0.14), m=M_RAIL)
sl = obj("Travers", box_mesh(0.45, 2.9, 0.1, 0), (-200, 10, 0.05), m=M_SLEEPER)
am = sl.modifiers.new("dizi", "ARRAY"); am.use_relative_offset = False; am.use_constant_offset = True
am.constant_offset_displace = (1.4, 0, 0); am.count = 286

# İstasyon peronu
obj("Peron", box_mesh(26, 3.6, 0.7, 0.1), (0, 13.6, 0.35), m=mat("Peron", "#D9D2C5", 0.7))

# Okul binası
M_SCHOOL = mat("Okul", C["peach"], 0.7)
obj("Okul", box_mesh(26, 10, 8.4, 0.25), (0, 28, 4.2), m=M_SCHOOL)
obj("Okul_cati", prism_mesh(27.4, 11.2, 4.2), (0, 28, 8.4), m=mat("Cati", "#E8505B", 0.6))
M_FRAME = mat("Cerceve", C["white"], 0.5)
for row, z in enumerate((2.3, 5.9)):
    for x in (-10.5, -7.0, -3.5, 3.5, 7.0, 10.5):
        obj("Pencere_cerceve", box_mesh(2.5, 0.3, 2.3, 0.08), (x, 22.95, z), m=M_FRAME)
        obj("Pencere", box_mesh(2.1, 0.32, 1.9, 0.04), (x, 22.9, z), m=M_GLASS)
obj("Kapi", box_mesh(3.0, 0.4, 4.2, 0.2), (0, 22.9, 2.1), m=mat("Kapi", "#9C5B34", 0.6))
obj("Tabela", box_mesh(9.0, 0.35, 1.5, 0.2), (0, 22.82, 6.0), m=mat("Tabela", C["blue"], 0.4))
sign = obj("Tabela_yazi", text_data("tabela", "OKULUMUZ", 1.05, 0.06, 0.015), (0, 22.6, 6.0),
           (math.radians(90), 0, 0), 1.0, mat("TabelaYazi", C["yellow"], 0.4, emit=0.3))
# Çatıda kalp amblemi
obj("Okul_kalp", heart_data(), (0, 22.55, 8.6), (math.radians(90), 0, 0), 1.2, mat("Kalp", C["red"], 0.3))

# Ağaçlar
M_TRUNK = mat("Govde", "#9A6B47", 0.8)
M_LEAF = [mat("Yaprak1", "#3FBF5F", 0.7), mat("Yaprak2", "#5AD16E", 0.7), mat("Yaprak3", "#2FA85A", 0.7)]
tree_spots = []
for i in range(70):
    for _ in range(50):
        x = RNG.uniform(-80, 80); y = RNG.uniform(-30, 70)
        if -1 < y < 15.5:            # yol, ray, peron
            continue
        if -16 < x < 16 and 15 < y < 36:   # okul
            continue
        if -14 < x < 14 and -30 < y < -1:  # kamera bölgesi
            continue
        if all((x - a) ** 2 + (y - b) ** 2 > 16 for a, b in tree_spots):
            tree_spots.append((x, y)); break
for (x, y) in tree_spots:
    s = RNG.uniform(0.8, 1.35)
    t = empty("Agac", (x, y, 0))
    t.scale = (s, s, s)
    obj("Agac_govde", cyl_mesh(0.32, 2.4, bev=0.05), (0, 0, 1.2), m=M_TRUNK, parent=t)
    lm = RNG.choice(M_LEAF)
    ball("Agac_yaprak", (0, 0, 3.2), 2.6, lm, t)
    ball("Agac_yaprak", (0.7, 0.3, 2.6), 1.8, lm, t)
    ball("Agac_yaprak", (-0.6, -0.2, 2.7), 1.7, lm, t)

# Çiçek tarhı (okul önü)
FLOWER_COLS = ["red", "yellow", "pink", "purple", "orange", "white"]


def make_flower(name, loc, s=1.0, parent=None, col=None):
    fl = empty(name, loc, parent=parent)
    fl.scale = (s, s, s)
    obj(name + "_sap", cyl_mesh(0.04, 0.8, bev=0.0), (0, 0, 0.4), m=mat("Sap", "#2E9E4F", 0.7), parent=fl)
    pc = mat("Cicek_" + (col or "red"), C[col or "red"], 0.5)
    for k in range(5):
        a = 2 * math.pi * k / 5
        ball(name + "_yaprak", (math.cos(a) * 0.17, math.sin(a) * 0.17, 0.85), (0.17, 0.17, 0.08), pc, fl)
    ball(name + "_orta", (0, 0, 0.87), (0.12, 0.12, 0.08), mat("Cicek_orta", C["yellow"], 0.5), fl)
    return fl


for i in range(46):
    x = RNG.uniform(-12.5, 12.5)
    if -2.2 < x < 2.2:
        continue
    make_flower("Cicek", (x, RNG.uniform(19.5, 21.8), 0), RNG.uniform(0.9, 1.3), col=RNG.choice(FLOWER_COLS))

# Bulutlar (yavaşça kayar)
M_CLOUD = mat("Bulut", C["white"], 0.9, emit=0.15)
interp("LINEAR")
for i in range(9):
    cx, cy, cz = RNG.uniform(-60, 50), RNG.uniform(50, 110), RNG.uniform(20, 34)
    cl = empty("Bulut", (cx, cy, cz))
    for k in range(5):
        ball("Bulut_top", (k * 2.0 - 4, RNG.uniform(-0.6, 0.6), RNG.uniform(-0.3, 1.0) + (1.2 if k == 2 else 0)),
             RNG.uniform(3.2, 4.4), M_CLOUD, cl)
    key(cl, "location", 1, (cx, cy, cz))
    key(cl, "location", FRAME_END, (cx + 12, cy, cz))
interp("BEZIER")

# Güneş karakteri (Sevgin bize hep bir ışık olsun)
M_SUN = mat("Gunes", "#FFC83D", 0.5, emit=1.2)
sun_root = empty("Gunes", (15, 72, -14))
ball("Gunes_top", (0, 0, 0), 8.0, M_SUN, sun_root)
sface = empty("Gunes_yuz_kok", (0, -3.9, 0), (0, 0, math.radians(-90)), parent=sun_root)
face(sface, (0, 0, 0.3), 3.2, "Gunes_yuz", eye_gap=0.3, mouth_drop=0.45)
rays = empty("Gunes_isinlar", (0, 0, 0), parent=sun_root)
M_RAY = mat("Isin", "#FFB21E", 0.5, emit=1.0)
for k in range(12):
    a = 2 * math.pi * k / 12
    obj("Isin", cyl_mesh(0.9, 2.6, r2=0.0, seg=16, bev=0.0), (math.cos(a) * 5.8, 0.6, math.sin(a) * 5.8),
        (0, -a + math.radians(90), 0), 1.0, M_RAY, rays)
    # koni Z ekseni boyunca; Y ekseni etrafında dönerek XZ düzleminde dışa bakar

# Gökkuşağı (2. turda büyür)
rainbow = empty("Gokkusagi", (8, 62, -1.0), (math.radians(90), 0, 0))
for k, hx in enumerate(["#FF4B4B", "#FF9A2E", "#FFD233", "#3CC86A", "#3D8BFF", "#5B5BFF", "#9B5CFF"]):
    obj("Gokkusagi_bant", torus_mesh(36 - k * 1.5, 0.78, half=True, seg=72), (0, 0, 0), m=mat("GK%d" % k, hx, 0.5, emit=0.9),
        parent=rainbow)

# ----------------------------------------------------------------------------
# MEKAN 2: Sınıf (yerin altında, z=-200; bahçe kameralarından görünmez)
# ----------------------------------------------------------------------------
CX, CY, CZ = 0.0, 0.0, -200.0


def cl(x, y, z):
    return (CX + x, CY + y, CZ + z)


obj("Sinif_zemin", box_mesh(32, 24, 0.3, 0), cl(0, -2, -0.15), m=mat("Parke", "#E8C59A", 0.6))
obj("Sinif_arka_duvar", box_mesh(32, 0.5, 13, 0), cl(0, 9.2, 6.5), m=mat("Duvar_mavi", "#BFE3FF", 0.8))
obj("Sinif_sol_duvar", box_mesh(0.5, 24, 13, 0), cl(-15.5, -2, 6.5), m=mat("Duvar_sari", "#FFF0B5", 0.8))
obj("Sinif_sag_duvar", box_mesh(0.5, 24, 13, 0), cl(15.5, -2, 6.5), m=mat("Duvar_sari", "#FFF0B5", 0.8))
obj("Sinif_tavan", box_mesh(32, 24, 0.3, 0), cl(0, -2, 13.1), m=mat("Tavan", "#FFFFFF", 0.9))
obj("Supurgelik", box_mesh(31, 0.2, 0.6, 0), cl(0, 8.9, 0.3), m=mat("Supurgelik", "#7FB8E6", 0.6))
M_WIN = mat("Sinif_pencere", "#CFEFFF", 0.1, emit=1.0)
for y in (3.0, -4.0):
    obj("Sinif_pencere_cerceve", box_mesh(0.3, 4.8, 4.8, 0.08), cl(-15.2, y, 6.2), m=M_FRAME)
    obj("Sinif_pencere", box_mesh(0.32, 4.2, 4.2, 0.0), cl(-15.15, y, 6.2), m=M_WIN)
# Kara tahta
obj("Tahta_cerceve", box_mesh(15.4, 0.3, 6.0, 0.12), cl(0, 8.85, 5.4), m=mat("Tahta_ahsap", "#A06A3E", 0.6))
obj("Tahta", box_mesh(14.6, 0.32, 5.2, 0.02), cl(0, 8.75, 5.4), m=mat("Kara_tahta", "#2E5E4E", 0.85))
obj("Tebesir_rafi", box_mesh(14.6, 0.5, 0.15, 0.04), cl(0, 8.5, 2.75), m=mat("Tahta_ahsap", "#A06A3E", 0.6))
BOARD_Y = 8.75 - 0.16 - 0.02
M_CHALK = mat("Tebesir", "#FFFFFF", 0.9, emit=0.35)
board_t1 = obj("Tahta_yazi1", text_data("tahta1", "Canım Öğretmenim", 1.05, 0.03, 0.0), cl(0, BOARD_Y, 6.85),
               (math.radians(90), 0, 0), 1.0, M_CHALK)
board_heart = obj("Tahta_kalp", heart_data(), cl(0, BOARD_Y - 0.25, 3.35), (math.radians(90), 0, 0), 1.25,
                  mat("Kalp_parlak", C["red"], 0.25, emit=0.0))
M_STAR = mat("Yildiz", C["yellow"], 0.4, emit=0.8)
board_stars = []
for (x, z, s) in ((-5.8, 4.4, 0.9), (5.8, 4.4, 0.9), (-4.2, 3.4, 0.55), (4.2, 3.4, 0.55)):
    st = obj("Tahta_yildiz", star_mesh(), cl(x, BOARD_Y - 0.05, z), (math.radians(90), 0, 0), s, M_STAR)
    board_stars.append(st)
board_t2 = obj("Tahta_yazi2", text_data("tahta2", "Öğretmenler Gününüz\nKutlu Olsun!", 1.15, 0.04, 0.0),
               cl(0, BOARD_Y - 0.05, 5.55), (math.radians(90), 0, 0), 1.0, mat("Final_yazi", "#FFE066", 0.5, emit=1.0))
# Öğretmen masası
M_WOOD = mat("Masa", "#B57B4A", 0.6)
obj("Masa_ust", box_mesh(5.0, 2.6, 0.28, 0.08), cl(11.0, 4.5, 2.6), m=M_WOOD)
for sx in (-1, 1):
    for sy in (-1, 1):
        obj("Masa_ayak", box_mesh(0.3, 0.3, 2.5, 0.05), cl(11.0 + sx * 2.1, 4.5 + sy * 1.0, 1.25), m=M_WOOD)
ball("Elma", cl(9.4, 4.0, 3.02), 0.5, mat("Elma", "#E83A3A", 0.3))
ball("Elma_yaprak", cl(9.5, 4.0, 3.32), (0.18, 0.08, 0.06), mat("Elma_yaprak", "#3CC86A", 0.5))
vase = obj("Vazo", cyl_mesh(0.35, 0.9, r2=0.45, bev=0.05), cl(12.5, 4.6, 3.2), m=mat("Vazo", C["cyan"], 0.25))
bouquet = empty("Buket", cl(12.5, 4.6, 3.3))
for k in range(7):
    a = 2 * math.pi * k / 7
    rr = 0.0 if k == 0 else 0.32
    fl = make_flower("Buket_cicek", (math.cos(a) * rr, math.sin(a) * rr, 0.1), 1.35, bouquet, FLOWER_COLS[k % 6])
    fl.rotation_euler = (math.sin(a) * 0.35 * (rr > 0), -math.cos(a) * 0.35 * (rr > 0), 0)
gifts = []
GIFT_COLS = [("pink", "yellow"), ("blue", "white"), ("green", "red"), ("purple", "yellow")]
for k, (gx, gs) in enumerate([(9.6, 0.7), (10.5, 0.85), (11.5, 0.6), (10.0, 0.55)]):
    gy = 4.9 if k < 3 else 3.9
    g = empty("Hediye", cl(gx, gy, 2.74))
    a, b = GIFT_COLS[k]
    obj("Hediye_kutu", box_mesh(gs, gs, gs, 0.06), (0, 0, gs / 2), m=mat("Hediye_" + a, C[a], 0.4), parent=g)
    mb_ = mat("Kurdele_" + b, C[b], 0.3)
    obj("Kurdele", box_mesh(gs + 0.02, 0.14, gs + 0.02, 0.02), (0, 0, gs / 2), m=mb_, parent=g)
    obj("Kurdele", box_mesh(0.14, gs + 0.02, gs + 0.02, 0.02), (0, 0, gs / 2), m=mb_, parent=g)
    ball("Fiyonk", (0.12, 0, gs + 0.08), (0.22, 0.12, 0.14), mb_, g)
    ball("Fiyonk", (-0.12, 0, gs + 0.08), (0.22, 0.12, 0.14), mb_, g)
    gifts.append(g)
# Bayrak süs (2. turda eklenir)
bunting = []
for k in range(20):
    x = -14 + k * (28 / 19)
    z = 11.6 - 0.9 * (1 - ((x / 14) ** 2))
    fl = obj("Susleme", tri_flag_mesh(), cl(x, 8.85, z), (0, 0, 0), 0.8,
             mat("Susleme_" + FLOWER_COLS[k % 5], C[["red", "yellow", "blue", "green", "pink"][k % 5]], 0.6))
    bunting.append(fl)
obj("Susleme_ip", cyl_mesh(0.03, 28.5, bev=0.0), cl(0, 8.86, 11.25), (0, math.radians(90), 0), 1.0, M_PUPIL)

# Işıklar
sun = bpy.data.lights.new("Gunes_isigi", "SUN")
sun.energy = 3.6
sun.angle = math.radians(8)
sun.color = hexc("#FFF6E5")
sun_obj = obj("Gunes_isigi", sun, (0, 0, 50), (math.radians(48), 0, math.radians(-28)))
area = bpy.data.lights.new("Sinif_isigi", "AREA")
area.shape = "RECTANGLE"; area.size = 26; area.size_y = 18
area.energy = 2600
area.color = hexc("#FFF8EC")
obj("Sinif_isigi", area, cl(0, -1, 12.6))
fill = bpy.data.lights.new("Sinif_on_isik", "AREA")
fill.shape = "RECTANGLE"; fill.size = 24; fill.size_y = 10
fill.energy = 1200
obj("Sinif_on_isik", fill, cl(0, -13, 6), (math.radians(90), 0, 0))
win_l = bpy.data.lights.new("Sinif_pencere_isigi", "AREA")
win_l.size = 10; win_l.energy = 700; win_l.color = hexc("#E6F6FF")
obj("Sinif_pencere_isigi", win_l, cl(-14.5, 0, 6.2), (0, math.radians(90), 0))

# ----------------------------------------------------------------------------
# Karakterleri yerleştir
# ----------------------------------------------------------------------------
train = make_train()
YARD_COLS = ["red", "blue", "yellow", "green", "purple", "orange"]
yard_cars = [make_car("BahceAraba%d" % i, c, (36 + i * 4.5, 3, 0), math.pi) for i, c in enumerate(YARD_COLS)]
CLASS_COLS = ["orange", "pink", "blue", "yellow", "green"]
CLASS_X = [-5.5, -2.75, 0.0, 2.75, 5.5]
class_cars = [make_car("SinifAraba%d" % i, c, cl(CLASS_X[i], 3.0, 0), math.radians(-90))
              for i, c in enumerate(CLASS_COLS)]
for c_ in class_cars:
    c_["root"].scale = (1.25, 1.25, 1.25)

# Vagon yükleri
wg_gift, wg_heart, wg_flow = train["wagons"]
for k, (dx, dy, s) in enumerate([(-1.0, -0.4, 0.8), (0.3, 0.3, 1.0), (1.2, -0.3, 0.7)]):
    g = empty("Vagon_hediye", (dx, dy, 1.22), parent=wg_gift)
    a, b = GIFT_COLS[k]
    obj("Hediye_kutu", box_mesh(s, s, s, 0.06), (0, 0, s / 2), m=mat("Hediye_" + a, C[a], 0.4), parent=g)
    mb_ = mat("Kurdele_" + b, C[b], 0.3)
    obj("Kurdele", box_mesh(s + 0.02, 0.14, s + 0.02, 0.02), (0, 0, s / 2), m=mb_, parent=g)
    obj("Kurdele", box_mesh(0.14, s + 0.02, s + 0.02, 0.02), (0, 0, s / 2), m=mb_, parent=g)
for k in range(9):
    make_flower("Vagon_cicek", (-1.5 + (k % 3) * 1.4 + RNG.uniform(-0.2, 0.2), -0.6 + (k // 3) * 0.6, 1.2),
                1.3, wg_flow, FLOWER_COLS[k % 6])
# Büyüyen kalp (vagon 2) - ayrı kök, vagonu takip edebilmesi için vagona bağlı
heart_root = empty("Buyuyen_kalp", (0, 0, 1.22), parent=wg_heart)
big_heart = obj("Buyuyen_kalp_govde", heart_data(), (0, 0, 0), (math.radians(90), 0, 0), 1.0,
                mat("Kalp_balon", C["red"], 0.2, emit=0.15), heart_root)
face(heart_root, (0, -0.42, 0.95), 0.55, "Kalp_yuz", eye_gap=0.3, mouth_drop=0.45).rotation_euler = (0, 0, math.radians(-90))

# 3D başlık (S2)
title = obj("Baslik", text_data("baslik", "Öğretmenler Günü", 3.4, 0.5, 0.08), (0, 14, 14.5),
            (math.radians(76), 0, 0), 1.0, None)
for k, cn in enumerate(["red", "orange", "yellow", "green", "blue", "purple", "pink"]):
    title.data.materials.append(mat("Baslik_" + cn, C[cn], 0.3, emit=0.4))
idx = 0
for i, ch in enumerate(title.data.body):
    if ch != " ":
        title.data.body_format[i].material_index = idx % 7
        idx += 1

# ----------------------------------------------------------------------------
# Hareketler
# ----------------------------------------------------------------------------

def ease_out(u):
    u = max(0.0, min(1.0, u)); return 1 - (1 - u) ** 2


def ease_in_out(u):
    u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)


def train_x(t):
    if t < 8.6:
        return -62 + 62 * ease_out(t / 8.6)
    if t < 54.1:
        return 0.0
    if t < 60.0:
        return 30 * ease_in_out((t - 54.1) / 5.9)
    return 30.0


# Tren: konum + teker dönüşü (her 3 karede bir anahtar, doğrusal)
interp("LINEAR")
for f in list(range(1, FRAME_END + 1, 3)) + [FRAME_END]:
    t = (f - 1) / FPS
    moving = t < 8.7 or 54.0 < t < 60.1 or f in (1, FRAME_END)
    if not moving and f % 30 != 1:
        continue
    x = train_x(t)
    key(train["root"], "location", f, (x, 10, TRAIN_Z))
    for (w, r) in train["wheels"]:
        key(w, "rotation_euler", f, (math.radians(90), (x + 62) / r, 0), index=-1)

# Buhar bulutları
M_PUFF = mat("Buhar", "#FFFFFF", 0.9, emit=0.25)
puffs = []
NP, PER = 8, 2.0
for k in range(NP):
    p = ball("Buhar", train["puff"], 0.6, M_PUFF, train["loco"])
    p.scale = (0, 0, 0)
    puffs.append(p)
WHISTLES = [0.4, 37.6, 54.1]
for k, p in enumerate(puffs):
    c = 0
    while True:
        t0 = c * PER + k * PER / NP
        if t0 > DUR:
            break
        big = any(w <= t0 <= w + 1.2 for w in WHISTLES)
        s1 = 2.4 if big else 1.5
        f0, f1, f2 = F(t0), F(t0 + PER * 0.92), F(t0 + PER * 0.97)
        x0, y0, z0 = train["puff"]
        key(p, "location", f0, (x0, y0, z0))
        key_scale(p, f0, 0.35)
        key(p, "location", f1, (x0 - 2.6 + RNG.uniform(-0.3, 0.3), RNG.uniform(-0.5, 0.5), z0 + 3.4))
        key_scale(p, f1, s1)
        key_scale(p, f2, 0.0)
        c += 1
interp("BEZIER")


# Arabalar: sürüş (L1)
def drive(car, keys):
    """keys: [(t, x, y, heading_deg)] - doğrusal anahtar, tekerler mesafeye göre döner"""
    interp("LINEAR")
    dist = 0.0
    prev = None
    for (t, x, y, h) in keys:
        if prev is not None:
            dist += math.hypot(x - prev[0], y - prev[1])
        prev = (x, y)
        f = F(t)
        key(car["root"], "location", f, (x, y, car["root"].location.z))
        for w in car["wheels"]:
            key(w, "rotation_euler", f, (math.radians(90), dist / car["r"], 0))
    interp("BEZIER")


ARRIVE = {}
LINEUP_X = [-6.5 + 2.6 * i for i in range(6)]
X0 = [36 + 4.5 * i for i in range(6)]
for i, car in enumerate(yard_cars):
    x0 = X0[i]
    t0, t1 = 4.4, 7.6 + 0.18 * i
    ks = []
    n = 14
    for j in range(n + 1):
        u = j / n
        t = t0 + (t1 - t0) * u
        ks.append((t, x0 + (LINEUP_X[i] - x0) * ease_out(u), 3.0, 0))
    ks.insert(0, (0.0, x0, 3.0, 0))
    drive(car, ks)
    ARRIVE[i] = t1
    r = car["root"]
    key(r, "rotation_euler", 1, (0, 0, math.pi))
    key(r, "rotation_euler", F(t1), (0, 0, math.pi))
    key(r, "rotation_euler", F(t1 + 0.4), (0, 0, math.radians(270)))

# Sıra kontrolü (hata filtresi): arabalar birbirine girmesin
for f in range(F(4.4), F(8.5)):
    t = (f - 1) / FPS
    xs = []
    for i in range(6):
        x0 = X0[i]; t1 = 7.6 + 0.18 * i
        u = (t - 4.4) / (t1 - 4.4)
        xs.append(x0 + (LINEUP_X[i] - x0) * ease_out(u))
    for i in range(5):
        if xs[i + 1] - xs[i] < 2.45:
            WARN.append("Araba %d ve %d çok yakın: t=%.2f aralık=%.2f" % (i, i + 1, t, xs[i + 1] - xs[i]))
            break

# Zıplama (vuruşlara bağlı)
PARTY = [(29.2, 37.4), (63.4, 74.0)]


def is_party(t):
    return any(a <= t <= b for a, b in PARTY)


def hop_car(car, start_t, every_beat_fn, amp=0.45, spin_fn=None):
    hop = car["hop"]
    bi = 0
    spin_total = 0.0
    for i in range(len(BEATS) - 1):
        b, nb = BEATS[i], BEATS[i + 1]
        if b < start_t:
            continue
        every = every_beat_fn(b)
        if not every and bi % 2 == 1:
            bi += 1
            continue
        bi += 1
        span = (nb - b) if every else min(2 * (nb - b), (BEATS[i + 2] - b) if i + 2 < len(BEATS) else 2 * (nb - b))
        fb, fm, fe = F(b), F(b + span * 0.45), F(b + span * 0.92)
        if fe <= fm or fm <= fb:
            continue
        key(hop, "location", fb, (0, 0, 0))
        key_scale(hop, fb, (1.12, 1.12, 0.84))
        key(hop, "location", fm, (0, 0, amp))
        key_scale(hop, fm, (0.94, 0.94, 1.1))
        key(hop, "location", fe, (0, 0, 0))
        key_scale(hop, fe, (1.0, 1.0, 1.0))
        if spin_fn and spin_fn(b, i):
            key(hop, "rotation_euler", fb, (0, 0, spin_total))
            spin_total += 2 * math.pi
            key(hop, "rotation_euler", fe, (0, 0, spin_total))


for i, car in enumerate(yard_cars):
    hop_car(car, ARRIVE[i] + 0.45, lambda b: is_party(b) or in_refrain(b),
            amp=0.5, spin_fn=lambda b, i_, ph=i: is_party(b) and (i_ + ph) % 4 == 0)
for i, car in enumerate(class_cars):
    hop_car(car, 0.0, lambda b: in_refrain(b, 0.5) or b > 68.0,
            amp=0.55, spin_fn=lambda b, i_, ph=i: b > 68.0 and (i_ + ph) % 4 == 0)

# Göz kırpma
for eyes in BLINKERS:
    t = RNG.uniform(0.5, 3.0)
    while t < DUR - 0.3:
        f = F(t)
        key_scale(eyes, f - 1, 1.0)
        key_scale(eyes, f + 1, (1.0, 1.0, 0.1))
        key_scale(eyes, f + 3, 1.0)
        t += RNG.uniform(2.5, 4.5)

# Başlık: S2'de zıplayarak gelir, 5.0 sn'de kaybolur
pop_in(title, 2.75, 1.0, 0.45)
key(title, "location", F(3.4), (0, 14, 14.5))
key(title, "location", F(4.2), (0, 14, 15.3))
key(title, "location", F(4.95), (0, 14, 14.5))
key_scale(title, F(4.95), 1.0)
key_scale(title, F(5.0), 0.0)

# Büyüyen kalp: kelime kelime şişer, sonra gökyüzüne uçar
interp("BEZIER")
hr = heart_root
key_scale(hr, 1, 0.75)
key_scale(hr, F(13.2), 0.75)
steps = [w for w in WORDS if 13.0 < w[1] < 17.0]   # Kalbin her gün mutlulukla dolsun!
sizes = [1.05, 1.35, 1.65, 2.0, 2.5]
for (w, s) in zip(steps, sizes):
    f = F(w[1])
    key_scale(hr, f, s * 0.92)
    key_scale(hr, f + 4, s * 1.08)
    key_scale(hr, f + 8, s)
# kalp vagondan ayrılıp yükselir (vagon x=-10.4 sabit, tren duruyor)
key(hr, "location", F(16.9), (0, 0, 1.22))
key(hr, "location", F(21.0), (2.0, 1.0, 9.0))
key(hr, "location", F(26.0), (5.0, 2.0, 19.0))
key(hr, "location", F(34.0), (7.0, 4.0, 30.0))
key_scale(hr, F(34.0), 2.5)
key_scale(hr, F(36.0), 0.0)
for k, t in enumerate([17.5, 19.0, 20.5, 22.0, 23.5, 25.0, 27.0, 29.0, 31.0]):
    key(hr, "rotation_euler", F(t), (0, 0, math.radians(8 if k % 2 else -8)))

# Güneş doğar, "ışık" kelimesinde parlar
interp("BEZIER")
key(sun_root, "location", F(20.9), (15, 72, -14))
key(sun_root, "location", F(24.4), (15, 72, 30))
isik = [w for w in WORDS if w[0].startswith("ışık")]
eb = bsdf(M_SUN).inputs["Emission Strength"]
eb.default_value = 1.2; eb.keyframe_insert("default_value", frame=1)
for w in isik:
    f = F(w[1])
    eb.default_value = 1.2; eb.keyframe_insert("default_value", frame=f - 2)
    eb.default_value = 4.0; eb.keyframe_insert("default_value", frame=f + 3)
    eb.default_value = 1.4; eb.keyframe_insert("default_value", frame=f + 20)
key(sun, "energy", 1, 3.6)
key(sun, "energy", F(isik[0][1]) - 2, 3.6)
key(sun, "energy", F(isik[0][1]) + 3, 5.5)
key(sun, "energy", F(isik[0][1]) + 30, 4.0)
interp("LINEAR")
key(rays, "rotation_euler", 1, (0, 0, 0))
key(rays, "rotation_euler", FRAME_END, (0, math.radians(-360 * 4), 0))
interp("BEZIER")

# Gökkuşağı (54.1)
key_scale(rainbow, 1, 0.0)
key_scale(rainbow, F(54.0), 0.0)
key_scale(rainbow, F(56.2), 1.04)
key_scale(rainbow, F(56.8), 1.0)

# Balonlar (bahçe): 29.3 ve 63.6'da yükselir
M_STRING = mat("Ip", "#F5F5F5", 0.8)
balloons = []
BAL_COLS = ["red", "yellow", "blue", "green", "pink", "purple", "orange", "cyan"]
for k in range(26):
    b = empty("Balon", (0, 0, -5))
    bc = BAL_COLS[k % 8]
    ball("Balon_top", (0, 0, 2.6), (1.05, 1.05, 1.3), mat("Balon_" + bc, C[bc], 0.15, spec=0.7), b)
    obj("Balon_dugum", cyl_mesh(0.14, 0.2, r2=0.04, bev=0.0), (0, 0, 1.9), (math.radians(180), 0, 0), 1.0,
        mat("Balon_" + bc, C[bc], 0.15), b)
    obj("Balon_ip", cyl_mesh(0.015, 1.8, bev=0.0), (0, 0, 0.9), m=M_STRING, parent=b)
    balloons.append(b)
for (T0, region) in ((29.32, (-10, 10, -1, 7)), (63.58, (-10, 12, -1, 7))):
    for k, b in enumerate(balloons):
        t0 = T0 + RNG.uniform(0, 1.6)
        x, y = RNG.uniform(region[0], region[1]), RNG.uniform(region[2], region[3])
        if abs(y - 3) < 1.6 and min(abs(x - lx) for lx in LINEUP_X) < 1.3:
            y += 2.5
        f0 = F(t0)
        interp("CONSTANT")
        key(b, "location", f0 - 1, (x, y, -6))
        key_scale(b, f0 - 1, 0.0)
        interp("BEZIER")
        key(b, "location", f0, (x, y, 0.0))
        key_scale(b, f0, 0.3)
        key_scale(b, f0 + 6, 1.0)
        interp("LINEAR")
        sway = RNG.uniform(1.0, 2.5)
        for j in range(1, 9):
            tt = t0 + j * 1.0
            key(b, "location", F(tt), (x + math.sin(j * 1.3 + k) * sway, y + j * 0.5, j * j * 0.35 + j * 1.2))
        interp("BEZIER")
interp("CONSTANT")
for b in balloons:
    key_scale(b, 1, 0.0)
interp("BEZIER")

# Konfeti (bahçe ve sınıf)
CONF_COLS = ["red", "yellow", "blue", "green", "pink", "purple", "orange", "cyan"]
CONF_M = [mat("Konfeti_" + c, C[c], 0.4, emit=0.3) for c in CONF_COLS]


def confetti(n, windows, prefix):
    pieces = []
    for k in range(n):
        p = obj(prefix, plane_mesh(0.32, 0.18), (0, 0, -50), m=CONF_M[k % len(CONF_M)])
        pieces.append(p)
    for (T0, T1, cx, cy, cz, sx, sy, top, bottom) in windows:
        for k, p in enumerate(pieces):
            t0 = T0 + RNG.uniform(0, T1 - T0)
            x, y = cx + RNG.uniform(-sx, sx), cy + RNG.uniform(-sy, sy)
            fall = RNG.uniform(3.0, 4.2)
            f0, f1 = F(t0), F(t0 + fall)
            interp("CONSTANT")
            key(p, "location", f0 - 1, (x, y, cz - 50))
            interp("LINEAR")
            key(p, "location", f0, (x, y, cz + top))
            r0 = Euler((RNG.uniform(0, 6), RNG.uniform(0, 6), RNG.uniform(0, 6)))
            key(p, "rotation_euler", f0, r0)
            for j in (1, 2, 3):
                tt = t0 + fall * j / 3
                key(p, "location", F(tt), (x + math.sin(j * 2 + k) * 0.8, y + math.cos(j + k) * 0.6,
                                         cz + top - (top - bottom) * j / 3))
            key(p, "rotation_euler", f1, (r0.x + RNG.uniform(6, 14), r0.y + RNG.uniform(4, 10), r0.z + 3))
            interp("CONSTANT")
            key(p, "location", f1 + 1, (x, y, cz - 50))
    interp("BEZIER")
    return pieces


confetti(170, [(31.0, 34.5, 0, 3, 0, 11, 5, 13, 0.02), (64.6, 68.5, 0, 3, 0, 12, 5, 13, 0.02)], "Konfeti")
confetti(90, [(68.2, 71.2, CX, CY + 2, CZ, 13, 5, 12.5, 0.02)], "Sinif_konfeti")

# Sınıfta yağan çiçekler (final)
flower_rain = []
for k in range(28):
    fl = make_flower("Yagan_cicek", (0, 0, -300), 1.15, col=FLOWER_COLS[k % 6])
    t0 = 68.5 + RNG.uniform(0, 3.0)
    side = -1 if k % 2 else 1
    x, y = CX + side * RNG.uniform(7.8, 13), CY + RNG.uniform(-1, 7)
    f0 = F(t0); fall = RNG.uniform(2.6, 3.6)
    interp("CONSTANT"); key(fl, "location", 1, (0, 0, -300)); key(fl, "location", f0 - 1, (0, 0, -300))
    interp("LINEAR")
    key(fl, "location", f0, (x, y, CZ + 12.5))
    key(fl, "rotation_euler", f0, (RNG.uniform(-1, 1), RNG.uniform(-1, 1), 0))
    key(fl, "location", F(t0 + fall), (x + RNG.uniform(-1, 1), y, CZ + 0.05))
    key(fl, "rotation_euler", F(t0 + fall), (0, 0, RNG.uniform(0, 6)))
    interp("BEZIER")

# Sınıf: tahta kalbi her vuruşta atar (nakaratta daha güçlü)
interp("BEZIER")
for i, b in enumerate(BEATS):
    if b > 68.0:
        break
    strong = in_refrain(b, 0.2)
    if not strong and i % 2:
        continue
    s = 1.25 * (1.3 if strong else 1.12)
    key_scale(board_heart, F(b), s)
    key_scale(board_heart, F(b) + 6, 1.25)
emk = bsdf(MATS["Kalp_parlak"]).inputs["Emission Strength"]
bsdf(MATS["Kalp_parlak"]).inputs["Emission Color"].default_value = (*hexc(C["red"]), 1)
emk.default_value = 0.0; emk.keyframe_insert("default_value", frame=1)
for a, b in REFRAINS:
    emk.default_value = 0.0; emk.keyframe_insert("default_value", frame=F(a) - 3)
    emk.default_value = 1.6; emk.keyframe_insert("default_value", frame=F(a) + 3)
    emk.default_value = 1.6; emk.keyframe_insert("default_value", frame=F(b))
    emk.default_value = 0.0; emk.keyframe_insert("default_value", frame=F(b) + 10)
# yıldızlar dönerek parlar
for st in board_stars:
    interp("LINEAR")
    key(st, "rotation_euler", 1, (math.radians(90), 0, 0))
    key(st, "rotation_euler", FRAME_END, (math.radians(90), math.radians(720), 0))
    interp("BEZIER")

# Final tahtası
pop_out(board_t1, 68.15, 1.0, 0.2)
pop_out(board_heart, 68.15, 1.25, 0.2)
pop_in(board_t2, 68.2, 1.0, 0.45)
for st in board_stars[:2]:
    key_scale(st, F(68.2), 0.9)
    key(st, "location", F(68.2), st.location.copy())
    key(st, "location", F(68.6), (st.location.x * 1.2, st.location.y, CZ + 6.9))

# 2. tur: bayrak süsleri, hediyeler, buket
for k, fl in enumerate(bunting):
    pop_in(fl, 38.4 + k * 0.08, 0.8, 0.3)
for g, w in zip(gifts, [w for w in WORDS if 38.0 < w[1] < 42.0]):
    pop_in(g, w[1], 1.0, 0.35)
key_scale(bouquet, 1, 0.0)
key_scale(bouquet, F(41.1), 0.0)
key_scale(bouquet, F(42.0), 1.1)
key_scale(bouquet, F(42.4), 1.0)

# 2. tur: sınıfta uçan kalpler (46.9)
heart_mats = [mat("Ucan_kalp_k", C["red"], 0.25, emit=0.2), mat("Ucan_kalp_p", C["pink"], 0.25, emit=0.2),
              mat("Ucan_kalp_m", C["purple"], 0.25, emit=0.2)]
for k in range(24):
    h = obj("Ucan_kalp", heart_data(), cl(0, 0, -5), (math.radians(90), 0, 0), 0.0, heart_mats[k % 3])
    t0 = 46.9 + RNG.uniform(0, 2.6)
    x, y = RNG.uniform(-13, 13), RNG.uniform(-3, 7)
    ztop = RNG.uniform(8.6, 11.6)
    s = RNG.uniform(0.45, 0.8)
    f0 = F(t0)
    key_scale(h, 1, 0.0)
    key_scale(h, f0 - 1, 0.0)
    key(h, "location", f0 - 1, cl(x, y, 0.3))
    key_scale(h, f0 + 6, s)
    key(h, "location", F(t0 + 3.2), cl(x + RNG.uniform(-0.8, 0.8), y, ztop))
    t = t0 + 3.2
    k2 = 0
    while t < DUR:
        t += 1.1
        k2 += 1
        key(h, "location", F(min(t, DUR)), cl(x + math.sin(k2 + k) * 0.3, y, ztop + (0.25 if k2 % 2 else -0.25)))

# ----------------------------------------------------------------------------
# Kamera (tek kamera; çekim geçişleri ardışık iki karede anahtarla yapılır)
# ----------------------------------------------------------------------------
cam_data = bpy.data.cameras.new("Kamera")
cam_data.lens = 30
cam_data.clip_start = 0.1
cam_data.clip_end = 900
cam = obj("Kamera", cam_data)
scene.camera = cam


def look(loc, target):
    d = Vector(target) - Vector(loc)
    return d.to_track_quat("-Z", "Y").to_euler("XYZ")


def car_x(i, t):
    x0 = X0[i]; t1 = 7.6 + 0.18 * i
    if t <= 4.4:
        return x0
    return x0 + (LINEUP_X[i] - x0) * ease_out((t - 4.4) / (t1 - 4.4))


def lerp(a, b, u):
    return tuple(a[i] + (b[i] - a[i]) * u for i in range(len(a)))


def orbit(center, radius, a0, a1, z, tz=None):
    def fn(u):
        a = math.radians(a0 + (a1 - a0) * u)
        loc = (center[0] + math.cos(a) * radius, center[1] + math.sin(a) * radius, z)
        return loc, (center[0], center[1], tz if tz is not None else center[2])
    return fn


def lin(l0, l1, t0, t1=None):
    t1 = t1 or t0

    def fn(u):
        return lerp(l0, l1, u), lerp(t0, t1, u)
    return fn


def anchor(dx0, dz0, dx1, dz1, ty=6.0, tz=2.0, d0=-13.0, d1=-11.5):
    """Nakarat çekimi: arabalar alt söz bandının üstünde, tahta tamamen kadrajda kalır."""
    return lin(cl(dx0, d0, dz0), cl(dx1, d1, dz1), cl(dx0 * 0.3, ty, tz), cl(dx1 * 0.3, ty, tz))


def track_train(u, t0, t1):
    t = t0 + (t1 - t0) * u
    x = train_x(t)
    return (x - 7.5, -1.0, 2.6), (x + 1.0, 10, 3.2)


SHOTS = [
    # (başlangıç, fonksiyon(u)->(konum, hedef), lens, ease)
    (0.0, lambda u: ((-30 + 1.5 * u, 5.6 - 0.3 * u, 1.2 + 0.4 * u), (train_x(2.6 * u) + 2.6, 10, 2.3)), 28, False),
    (2.6, lin((-11, -20, 12), (-6, -18, 10), (0, 16, 10), (0, 16, 9.5)), 26, True),
    (5.0, lambda u: ((-6 + 3 * u, -9.5, 3.2), (lerp((-4, 6, 2.2), (-1, 6, 2.2), u))), 30, True),
    (7.0, lin((-1.5, -5.6, 1.1), (0.6, -5.0, 1.2), (0.5, 3, 1.1), (0.0, 3, 1.1)), 30, True),
    (8.9, anchor(0, 3.5, 0, 3.6), 26, True),                                 # A1
    (13.2, lin((-16.5, 0.5, 3.2), (-14.8, 0.0, 3.6), (-10.4, 10, 3.0), (-10.4, 10, 4.6)), 30, True),
    (15.78, lin((-7.6, -2.6, 0.55), (-6.6, -3.0, 0.5), (-10.4, 10, 4.6), (-10.0, 10, 5.4)), 22, True),
    (17.3, anchor(-4.0, 3.5, -3.0, 3.5), 26, True),                          # A2
    (20.2, lin((0, -17, 3.6), (0, -15, 4.6), (0, 15, 8.5), (2, 15, 10)), 26, True),
    (21.7, lin((1.5, -12.5, 1.1), (2.5, -11.5, 1.5), (6, 30, 13), (8, 30, 16)), 22, True),
    (24.0, lin((2.4, -3.4, 1.9), (-1.2, -3.6, 2.0), (0.8, 3, 1.3), (-0.8, 3, 1.3)), 38, True),
    (25.8, anchor(1.0, 3.0, 0.5, 3.0), 26, True),                    # A3
    (29.27, lin((0, -12, 2.0), (0, -15.5, 9.0), (0, 4, 2.0), (0, 5, 6.5)), 28, True),
    (31.36, orbit((0, 3, 1.2), 10, -125, -60, 3.4), 30, True),
    (34.2, anchor(4.0, 3.5, 3.0, 3.5), 26, True),                            # A4
    (37.4, lin((7.6, 6.2, 2.0), (6.4, 6.8, 2.3), (2.6, 10, 2.2), (2.6, 10, 2.4)), 34, True),
    (38.6, lin(cl(6.4, -3.2, 3.8), cl(7.6, -2.0, 3.5), cl(10.8, 4.4, 3.0), cl(10.8, 4.4, 3.1)), 32, True),
    (42.6, anchor(0, 4.5, 0, 4.5), 26, True),                        # A5
    (46.8, lin(cl(-2, -6.5, 0.9), cl(-1, -6.0, 1.1), cl(0, 5, 6.0), cl(0, 5, 7.8)), 22, True),
    (49.36, lin(cl(-10, -9, 5.0), cl(-8, -10, 5.6), cl(0, 3, 5.2), cl(0, 3, 5.6)), 24, True),
    (50.9, anchor(-3.0, 3.0, -2.0, 3.0), 26, True),                  # A6
    (54.08, lin((0, -25, 3.0), (0, -23, 5.0), (8, 30, 15), (8, 30, 17)), 22, True),
    (56.7, lambda u: track_train(u, 56.7, 59.25), 26, False),
    (59.25, anchor(3.0, 4.0, 2.0, 4.0), 26, True),                           # A7
    (63.45, lin((4, -13, 2.4), (2, -16.5, 10), (2, 4, 2.0), (2, 6, 7.0)), 28, True),
    (65.8, orbit((0, 3, 1.2), 10, -55, -120, 3.0), 30, True),
    (68.1, lin(cl(0, -10.5, 3.6), cl(0, -4.2, 5.0), cl(0, 8.5, 5.0), cl(0, 8.5, 5.4)), 30, True),   # FINAL
]
SHOT_T = [s[0] for s in SHOTS] + [DUR]
interp("BEZIER")
prev_rot = Euler((math.radians(90), 0, 0))
for i, (t0, fn, lens, ease) in enumerate(SHOTS):
    t1 = SHOT_T[i + 1]
    fa, fb = F(t0), F(t1) - 1
    if i == len(SHOTS) - 1:
        fb = FRAME_END
    nkeys = 2 if ease else max(2, int((t1 - t0) * 4) + 1)
    for j in range(nkeys):
        u = j / (nkeys - 1)
        f = int(round(fa + (fb - fa) * u))
        loc, tgt = fn(u)
        rot = look(loc, tgt)
        rot.make_compatible(prev_rot)
        prev_rot = rot
        cam.location = loc
        cam.rotation_euler = rot
        interp("BEZIER" if ease else "LINEAR")
        key(cam, "location", f)
        key(cam, "rotation_euler", f)
        key(cam_data, "lens", f, float(lens))
    # çekim içi ease dışı anahtarların sonrasındaki geçiş ani olmalı: kesme sonraki çekimin
    # ilk anahtarı fb+1 karesinde olduğundan ara kare oluşmaz.
interp("BEZIER")
for m_ in scene.timeline_markers:
    scene.timeline_markers.remove(m_)
for i, s in enumerate(SHOTS):
    scene.timeline_markers.new("Cekim_%02d" % (i + 1), frame=F(s[0]))

for fc in FCURVES:
    fc.update()

# Kamera: çekim içi yumuşak giriş/çıkış, kesmede komşu çekimden etkilenmeyen düz tutamaçlar
for idb in (cam, cam_data):
    ad_ = idb.animation_data
    for fc in ad_.action.layers[0].strips[0].channelbag(ad_.action_slot).fcurves:
        kps = list(fc.keyframe_points)
        for i, kp in enumerate(kps):
            if kp.interpolation != "BEZIER":
                continue
            x, y = kp.co
            dl = (x - kps[i - 1].co[0]) if i > 0 else 10.0
            dr = (kps[i + 1].co[0] - x) if i + 1 < len(kps) else 10.0
            kp.handle_left_type = "FREE"
            kp.handle_right_type = "FREE"
            kp.handle_left = (x - max(dl, 0.01) / 3.0, y)
            kp.handle_right = (x + max(dr, 0.01) / 3.0, y)

# ----------------------------------------------------------------------------
# Ses + sözler: "Montaj" sahnesi (3D sahne + karaoke + şarkı) -> MP4
# ----------------------------------------------------------------------------
snd_path = os.path.join(ASSETS, "sarki.m4a")
kjson = os.path.join(ASSETS, "karaoke", "karaoke.json")
mont = bpy.data.scenes.get("Montaj") or bpy.data.scenes.new("Montaj")
mont.render.fps = FPS
mont.frame_start = 1
mont.frame_end = FRAME_END
mont.render.resolution_x = 1920
mont.render.resolution_y = 1080
mont.render.resolution_percentage = 100
mont.view_settings.view_transform = "Standard"
se = mont.sequence_editor_create()
strips = se.strips
for s_ in list(strips):
    strips.remove(s_)
sc_strip = strips.new_scene("Sahne3D", scene, 1, 1)
sc_strip.frame_final_duration = FRAME_END
snd = strips.new_sound("Sarki", snd_path, 3, 1)
if os.path.exists(kjson):
    for k, e in enumerate(json.load(open(kjson, encoding="utf-8"))):
        st = strips.new_image("soz_%03d" % k, os.path.join(ASSETS, "karaoke", e["file"]), 2, e["f0"])
        st.frame_final_end = e["f1"]
        st.blend_type = "ALPHA_OVER"
else:
    WARN.append("Karaoke görselleri bulunamadı (assets/karaoke/karaoke.json)")
# 3D sahneye de şarkıyı ekle (önizleme/zamanlama için)
se3 = scene.sequence_editor_create()
st3 = se3.strips
for s_ in list(st3):
    st3.remove(s_)
st3.new_sound("Sarki", snd_path, 1, 1)
scene.sync_mode = "AUDIO_SYNC"

# Çıktı ayarı: MP4 (H.264 + AAC)
r = mont.render
try:
    r.image_settings.media_type = "VIDEO"
except Exception:
    pass
r.image_settings.file_format = "FFMPEG"
r.ffmpeg.format = "MPEG4"
r.ffmpeg.codec = "H264"
r.ffmpeg.constant_rate_factor = "HIGH"
r.ffmpeg.ffmpeg_preset = "GOOD"
r.ffmpeg.audio_codec = "AAC"
r.ffmpeg.audio_bitrate = 192
r.ffmpeg.audio_channels = "STEREO"
r.filepath = "//render/Ogretmenler_Gunu_"
scene.render.filepath = "//render/kareler/kare_"

# dosya açıldığında "Montaj" sahnesi etkin olsun (F12 / Ctrl+F12 doğrudan son videoyu üretir)
for win in bpy.context.window_manager.windows:
    win.scene = mont
# yollar göreli olsun ki klasör başka bilgisayara taşınabilsin
bpy.ops.wm.save_as_mainfile(filepath=OUT, relative_remap=True)
try:
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_mainfile()
except Exception as e:
    WARN.append("Göreli yol: %s" % e)

print("NESNE SAYISI:", len(bpy.data.objects))
print("KAYDEDILDI:", OUT)
for w in WARN:
    print("UYARI:", w)
