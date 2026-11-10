"""Glossy toy-like rescue vehicles with see-through cabins and a driver inside.

Overrides the old face-style vehicles from lib (same names, same part keys), so the
segment scripts only need `from vehicles import *` after `from lib import *`.
All vehicles face +X with their origin on the ground.
"""
import math, bmesh, bpy
from mathutils import Vector
from lib import *
import lib
from people import make_person, mood as p_mood, wave as p_wave


def paint(name, color):
    m = mat(name, color, rough=0.28, spec=0.6)
    p = m.node_tree.nodes["Principled BSDF"]
    if "Coat Weight" in p.inputs:
        p.inputs["Coat Weight"].default_value = 1.0
        p.inputs["Coat Roughness"].default_value = 0.05
    return m


def chrome():
    return mat("chrome", (0.85, 0.86, 0.9), rough=0.12, spec=1.0)


def glass():
    m = mat("glass2", (0.7, 0.88, 1.0), rough=0.02, spec=1.0, alpha=0.25)
    m.show_transparent_back = False
    return m


def dark():
    return mat("interior", (0.12, 0.12, 0.16), rough=0.6)


def _wheels2(v, xs, half_w, r=0.42, w=0.34):
    tire = mat("tire2", (0.07, 0.07, 0.08), rough=0.75, spec=0.2)
    rim = chrome()
    cap = mat("hubcap", (0.95, 0.95, 0.97), rough=0.2, spec=0.8)
    for x in xs:
        for s in (-1, 1):
            wh = empty(f"{v.kind}_wheel", (x, s * half_w, r), v.body)
            cyl("tire", r, w, (0, 0, 0), tire, wh, rot=(math.radians(90), 0, 0), bevel=0.1, verts=28)
            cyl("rim", r * 0.58, w + 0.03, (0, 0, 0), rim, wh, rot=(math.radians(90), 0, 0), bevel=0.03, verts=24)
            cyl("cap", r * 0.25, w + 0.07, (0, 0, 0), cap, wh, rot=(math.radians(90), 0, 0), bevel=0.02, verts=16)
            for k in range(5):
                a = k * 2 * math.pi / 5
                box("bolt", (0.05, w + 0.08, 0.05), (math.cos(a) * r * 0.4, 0, math.sin(a) * r * 0.4), rim, wh, bevel=0.01)
            v.wheels.append(wh)
    v.wheel_r = r


def cab(v, x0, x1, z0, z1, width, frame_m, roof_m, front_tilt=14, back_glass=True):
    """Hollow cabin: roof, pillars, transparent glass, seats, steering wheel."""
    g = glass()
    L = x1 - x0
    zc = (z0 + z1) / 2
    H = z1 - z0
    belt = H * 0.36
    # closed, rounded shell with real window openings (booleans applied at build time)
    shell = box(f"{v.kind}_cabshell", (L, width, H + 0.22), ((x0 + x1) / 2, 0, zc + 0.11), frame_m, v.body, bevel=0.2, segs=5)
    if roof_m is not frame_m:
        shell.data.materials.append(roof_m)
    bm = bmesh.new()
    def cube(cx, cy, cz, sx, sy, sz):
        r = bmesh.ops.create_cube(bm, size=1.0)
        vs = r["verts"]
        bmesh.ops.scale(bm, vec=Vector((sx, sy, sz)), verts=vs)
        bmesh.ops.translate(bm, vec=Vector((cx, cy, cz)), verts=vs)
    xc = (x0 + x1) / 2
    cube(xc, 0, zc - 0.02, L - 0.16, width - 0.16, H - 0.06)          # hollow inside
    wz0, wz1 = z0 + belt, z1 - 0.06
    cube(x1, 0, (wz0 + wz1) / 2, 0.6, width - 0.34, wz1 - wz0)         # windshield
    if L > 1.6:
        for cx, l in ((x0 + L * 0.3, L * 0.38), (x0 + L * 0.73, L * 0.36)):
            cube(cx, 0, (wz0 + wz1) / 2, l, width + 0.6, wz1 - wz0)  # side windows
    else:
        cube(xc + 0.05, 0, (wz0 + wz1) / 2, L - 0.42, width + 0.6, wz1 - wz0)
    if back_glass:
        cube(x0, 0, (wz0 + wz1) / 2, 0.6, width - 0.5, (wz1 - wz0) * 0.8)
    me = bpy.data.meshes.new("cutter")
    bm.to_mesh(me); bm.free()
    cutter = bpy.data.objects.new("cutter", me)
    bpy.context.scene.collection.objects.link(cutter)
    cutter.parent = v.body
    bo = shell.modifiers.new("win", "BOOLEAN")
    bo.operation = "DIFFERENCE"
    bo.solver = "EXACT"
    bo.use_self = True
    bo.use_hole_tolerant = True
    bo.object = cutter
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    newme = bpy.data.meshes.new_from_object(shell.evaluated_get(dg))
    shell.modifiers.clear()
    shell.data = newme
    newme.shade_smooth()
    newme.use_auto_smooth = True
    newme.auto_smooth_angle = math.radians(35)
    bpy.data.objects.remove(cutter)
    # glass panes in the openings
    gz = (wz0 + wz1) / 2
    gh = wz1 - wz0
    box("windshield", (0.03, width - 0.3, gh), (x1 - 0.12, 0, gz), g, v.body, bevel=0.0)
    for sd in (-1, 1):
        box("sideglass", (L - 0.3, 0.03, gh), (xc, sd * (width / 2 - 0.1), gz), g, v.body, bevel=0.0)
        box("handle", (0.16, 0.05, 0.04), (xc + L * 0.12, sd * (width / 2 + 0.02), z0 + belt * 0.75), chrome(), v.body, bevel=0.015)
        box("doorline", (0.025, 0.04, belt * 0.9), (xc + L * 0.3, sd * (width / 2 + 0.0), z0 + belt * 0.5), dark(), v.body, bevel=0.0)
    if back_glass:
        box("backglass", (0.03, width - 0.5, gh * 0.8), (x0 + 0.12, 0, gz), g, v.body, bevel=0.0)
    d = dark()
    box("floor", (L, width - 0.1, 0.06), ((x0 + x1) / 2, 0, z0 + 0.02), d, v.body, bevel=0.0)
    for s in (-1, 1):
        box("seat", (0.35, 0.55, 0.35), (x0 + L * 0.35, s * 0.38, z0 + 0.15), mat("seat", (0.3, 0.32, 0.4), rough=0.7), v.body, bevel=0.08)
        box("seatback", (0.15, 0.55, 0.6), (x0 + L * 0.35 - 0.22, s * 0.38, z0 + 0.45), mat("seat", (0.3, 0.32, 0.4)), v.body, bevel=0.06)
    box("dash", (0.25, width - 0.15, 0.25), (x1 - 0.22, 0, z0 + 0.15), d, v.body, bevel=0.06)
    torus("steer", 0.17, 0.025, (x1 - 0.42, 0.38, z0 + 0.38), d, v.body, rot=(0, math.radians(-60), math.radians(90)))
    return (x0 + L * 0.35, 0.38, z0 + 0.05)  # driver hip position


def front_face(v, x, half_w, z_light, z_grille, z_bump, width, light_r=0.27, grille_w=0.9, grille_h=0.42):
    ch = chrome()
    lens = mat("headlens", (1.0, 0.95, 0.65), rough=0.08, emit=0.6)
    for s in (-1, 1):
        sphere("headlight", light_r, (x - 0.06, s * half_w, z_light), lens, v.body, scale=(0.35, 1, 1))
        torus("headring", light_r, 0.05, (x - 0.05, s * half_w, z_light), ch, v.body, rot=(0, 0, math.radians(90)))
        sphere("foglight", 0.1, (x + 0.02, s * (half_w + 0.08), z_bump + 0.2), mat("foglens", (1.0, 0.35, 0.45), rough=0.1, emit=0.4), v.body, scale=(0.35, 1, 1))
    box("grille_frame", (0.08, grille_w, grille_h), (x, 0, z_grille), ch, v.body, bevel=0.12)
    box("grille_in", (0.09, grille_w - 0.12, grille_h - 0.12), (x + 0.01, 0, z_grille), dark(), v.body, bevel=0.05)
    for k in range(3):
        box("grille_bar", (0.1, grille_w - 0.16, 0.035), (x + 0.02, 0, z_grille - grille_h / 2 + 0.12 + k * (grille_h - 0.24) / 2), ch, v.body, bevel=0.012)
    box("bumper", (0.32, width + 0.08, 0.24), (x + 0.02, 0, z_bump), mat("bumper", (0.62, 0.64, 0.7), rough=0.35, spec=0.6), v.body, bevel=0.11)


def rear_face(v, x, half_w, z_light, z_bump, width):
    tl = mat("taillight", (1.0, 0.12, 0.12), rough=0.1, emit=0.6)
    for s in (-1, 1):
        sphere("taillight", 0.13, (x + 0.04, s * half_w, z_light), tl, v.body, scale=(0.35, 1, 1.3))
    box("rbumper", (0.3, width + 0.06, 0.22), (x - 0.02, 0, z_bump), mat("bumper", (0.62, 0.64, 0.7)), v.body, bevel=0.1)
    box("plate", (0.03, 0.55, 0.16), (x - 0.03, 0, z_bump + 0.22), mat("plate", (0.97, 0.97, 0.97), rough=0.4), v.body, bevel=0.01)


def mirrors(v, x, half_w, z, m):
    for s in (-1, 1):
        cyl("mirstalk", 0.025, 0.25, (x, s * (half_w + 0.1), z - 0.05), m, v.body, rot=(math.radians(90), 0, 0), verts=8)
        box("mirror", (0.08, 0.16, 0.13), (x, s * (half_w + 0.22), z), m, v.body, bevel=0.04)


PERSON_DRIVERS = False


def driver(v, hip, **kw):
    """Seat slot for a character card (or a procedural person when PERSON_DRIVERS)."""
    slot = empty(v.kind + "_seat", (hip[0] + 0.05, hip[1], hip[2] + 0.05), v.body)
    v.seat = slot
    v.driver = None
    if PERSON_DRIVERS:
        P = make_person(v.kind + "_driver", H=1.05, seated=True, **kw)
        P.root.parent = v.body
        P.root.location = (hip[0], hip[1], hip[2] - 0.3 * 1.05 + 0.18)
        v.driver = P
    return v.driver


def light_bar(v, x, z, w=1.3, colors=("red", "blue")):
    lib._lightbar(v, x, z, w=w, colors=colors)


def make_police():
    v = Vehicle("police")
    v.root = empty("police"); v.body = empty("police_body", parent=v.root)
    blue = paint("p_blue", (0.12, 0.33, 0.9))
    white = paint("p_white", (0.96, 0.96, 0.97))
    box("p_low", (3.5, 1.85, 0.8), (0, 0, 0.88), blue, v.body, bevel=0.34, segs=5)
    box("p_hood", (1.15, 1.6, 0.22), (1.15, 0, 1.25), blue, v.body, bevel=0.1, segs=4)
    box("p_trunk", (0.75, 1.6, 0.2), (-1.35, 0, 1.25), blue, v.body, bevel=0.09, segs=4)
    hip = cab(v, -0.95, 0.6, 1.25, 2.15, 1.75, white, white)
    front_face(v, 1.75, 0.55, 1.0, 0.82, 0.55, 1.85)
    rear_face(v, -1.75, 0.62, 1.0, 0.55, 1.85)
    mirrors(v, 0.5, 0.88, 1.45, blue)
    sphere("badge", 0.12, (1.62, 0, 1.33), mat("gold", (1.0, 0.78, 0.2), rough=0.2, spec=0.9), v.body, scale=(0.3, 1, 1.1))
    _wheels2(v, (1.1, -1.1), 0.85)
    light_bar(v, -0.18, 2.3, w=1.3)
    for s, rz in ((-1, 0), (1, 180)):
        text("p_txt", "POLİS", 0.28, (-0.1, s * 0.94, 0.9), white, v.body, rot=(math.radians(90), 0, math.radians(rz)), extrude=0.01, bevel=0.0)
    driver(v, hip, hat="police", shirt=(0.25, 0.45, 0.85), pants=(0.1, 0.15, 0.35), hair="brown", skin="light")
    return v


def make_ambulance():
    v = Vehicle("ambulance")
    v.root = empty("ambulance"); v.body = empty("ambulance_body", parent=v.root)
    white = paint("a_white", (0.97, 0.97, 0.98))
    red = paint("a_red", (0.9, 0.08, 0.08))
    box("a_low", (4.2, 2.0, 0.85), (0, 0, 0.9), white, v.body, bevel=0.32, segs=5)
    box("a_box", (2.5, 2.05, 1.75), (-0.85, 0, 2.15), white, v.body, bevel=0.3, segs=5)
    box("a_hood", (0.7, 1.7, 0.2), (1.65, 0, 1.3), white, v.body, bevel=0.09)
    hip = cab(v, 0.4, 1.35, 1.3, 2.35, 1.9, white, white, front_tilt=10, back_glass=False)
    front_face(v, 2.1, 0.6, 1.0, 0.85, 0.55, 2.0, light_r=0.25, grille_w=0.8)
    rear_face(v, -2.1, 0.7, 1.0, 0.55, 2.0)
    mirrors(v, 1.3, 0.98, 1.6, white)
    for s in (-1, 1):
        box("a_stripe", (4.25, 0.04, 0.2), (0.0, s * 1.01, 1.05), red, v.body, bevel=0.02)
        e = empty("cross", (-0.85, s * 1.035, 2.2), v.body)
        box("crossA", (0.8, 0.04, 0.24), (0, 0, 0), red, e, bevel=0.03)
        box("crossB", (0.24, 0.04, 0.8), (0, 0, 0), red, e, bevel=0.03)
        box("a_win", (0.6, 0.03, 0.35), (-1.6, s * 1.03, 2.5), glass(), v.body, bevel=0.0)
    _wheels2(v, (1.25, -1.3), 0.95)
    light_bar(v, 0.85, 2.55, w=1.4, colors=("red", "red"))
    driver(v, hip, hat="medic", shirt=(0.2, 0.7, 0.55), pants=(0.2, 0.7, 0.55), hair="black", skin="tan")
    return v


def make_firetruck():
    v = Vehicle("fire")
    v.root = empty("fire"); v.body = empty("fire_body", parent=v.root)
    red = paint("f_red", (0.92, 0.08, 0.06))
    silver = chrome()
    yel = paint("f_yel", (1.0, 0.8, 0.1))
    box("f_base", (5.0, 2.1, 0.95), (-0.25, 0, 0.98), red, v.body, bevel=0.3, segs=5)
    box("f_hood", (0.55, 1.8, 0.25), (2.05, 0, 1.5), red, v.body, bevel=0.1)
    hip = cab(v, 0.8, 1.85, 1.45, 2.5, 2.0, red, red, front_tilt=8, back_glass=False)
    box("f_rear", (2.9, 2.0, 0.55), (-1.05, 0, 1.72), red, v.body, bevel=0.2)
    for s in (-1, 1):
        box("f_stripe", (5.05, 0.04, 0.16), (-0.25, s * 1.06, 1.1), yel, v.body, bevel=0.02)
        for k in range(3):
            box("f_locker", (0.8, 0.04, 0.5), (-2.0 + k * 0.95, s * 1.04, 1.7), mat("locker", (0.8, 0.82, 0.86), rough=0.3, spec=0.8), v.body, bevel=0.04)
    front_face(v, 2.25, 0.65, 1.1, 0.9, 0.58, 2.1, light_r=0.26, grille_w=1.0, grille_h=0.5)
    rear_face(v, -2.75, 0.75, 1.0, 0.58, 2.1)
    mirrors(v, 1.75, 1.05, 1.85, red)
    _wheels2(v, (1.35, -0.6, -1.75), 0.98, r=0.46)
    light_bar(v, 1.3, 2.7, w=1.5)
    torus("f_hose", 0.35, 0.09, (-0.3, -1.05, 1.15), mat("hose", (0.95, 0.95, 0.9), rough=0.6), v.body, rot=(math.radians(90), 0, 0))
    piv = empty("ladder_pivot", (-2.2, 0, 2.05), v.body)
    cyl("lad_turret", 0.45, 0.3, (0, 0, -0.05), silver, piv, verts=20)
    lad = empty("ladder_main", (0, 0, 0.15), piv)
    lad2 = empty("ladder_ext", (0, 0, 0.12), lad)
    for L, parent, w in ((3.6, lad, 0.75), (3.4, lad2, 0.6)):
        for s in (-1, 1):
            box("rail", (L, 0.09, 0.12), (L / 2, s * w / 2, 0), silver, parent, bevel=0.03)
        for i in range(int(L / 0.4)):
            cyl("rung", 0.035, w, (0.2 + i * 0.4, 0, 0), silver, parent, rot=(math.radians(90), 0, 0), verts=8)
    bucket = empty("ladder_bucket", (3.45, 0, 0.0), lad2)
    v.parts["bucket"] = bucket
    lvl = empty("bucket_level", (0, 0, 0), bucket)  # counter-rotated to stay upright
    v.parts["bucket_level"] = lvl
    box("bk_floor", (0.9, 1.0, 0.08), (0.3, 0, 0.0), silver, lvl, bevel=0.03)
    for yy in (-0.5, 0.5):
        box("bk_rail", (0.9, 0.06, 0.42), (0.3, yy, 0.23), red, lvl, bevel=0.03)
    box("bk_front", (0.06, 1.0, 0.42), (0.75, 0, 0.23), red, lvl, bevel=0.03)
    box("bk_back", (0.06, 1.0, 0.42), (-0.15, 0, 0.23), red, lvl, bevel=0.03)
    v.parts.update(ladder_pivot=piv, ladder=lad, ladder_ext=lad2)
    noz = empty("nozzle_piv", (0.25, 0.75, 2.0), v.body)
    cyl("noz_base", 0.18, 0.25, (0, 0, 0), silver, noz, verts=16)
    cyl("noz", 0.09, 0.8, (0.35, 0, 0.2), silver, noz, rot=(0, math.radians(70), 0), verts=12)
    v.parts["nozzle"] = noz
    driver(v, hip, hat="fire", shirt=(0.15, 0.17, 0.22), pants=(0.15, 0.17, 0.22), hair="auburn", skin="light", iris="green")
    return v


def make_towtruck():
    v = Vehicle("tow")
    v.root = empty("tow"); v.body = empty("tow_body", parent=v.root)
    org = paint("t_orange", (1.0, 0.5, 0.05))
    gray = mat("tow_gray", (0.38, 0.4, 0.46), rough=0.4, spec=0.6)
    darkm = mat("hookdark", (0.15, 0.15, 0.17), rough=0.3, spec=0.8)
    box("t_base", (4.2, 1.95, 0.85), (0, 0, 0.9), org, v.body, bevel=0.3, segs=5)
    box("t_hood", (0.65, 1.7, 0.25), (1.75, 0, 1.38), org, v.body, bevel=0.1)
    hip = cab(v, 0.35, 1.45, 1.32, 2.4, 1.9, org, org, front_tilt=10)
    box("t_bed", (2.2, 1.8, 0.25), (-0.95, 0, 1.4), gray, v.body, bevel=0.06)
    front_face(v, 2.1, 0.6, 1.0, 0.85, 0.55, 1.95)
    rear_face(v, -2.1, 0.7, 1.0, 0.55, 1.95)
    mirrors(v, 1.35, 0.95, 1.6, org)
    _wheels2(v, (1.2, -1.2), 0.92)
    light_bar(v, 0.85, 2.6, w=1.3, colors=("orange", "yellow"))
    piv = empty("crane_pivot", (-0.6, 0, 1.6), v.body, rot=(0, math.radians(35), 0))
    box("boom", (2.6, 0.32, 0.32), (-1.3, 0, 0), gray, piv, bevel=0.08)
    tip = empty("crane_tip", (-2.55, 0, 0), piv)
    hk = empty("hook_root", (0, 0, 0), tip)
    cable = cyl("cable", 0.04, 1.0, (0, 0, -0.5), darkm, hk, verts=8)
    hook = empty("hook", (0, 0, -1.0), hk)
    torus("hookT", 0.18, 0.05, (0, 0, -0.15), darkm, hook, half="low")
    cyl("hookS", 0.05, 0.2, (0, 0, 0), darkm, hook, verts=8)
    v.parts.update(crane=piv, tip=tip, hook_root=hk, cable=cable, hook=hook)
    hk.rotation_euler = (0, math.radians(-35), 0)
    driver(v, hip, hat="cap", shirt=(0.15, 0.35, 0.6), pants=(0.15, 0.35, 0.6), hair="black", skin="brown")
    return v


def make_helicopter():
    v = Vehicle("heli")
    v.root = empty("heli"); v.body = empty("heli_body", parent=v.root)
    yel = paint("h_yel", (1.0, 0.75, 0.05))
    darkm = mat("heli_dark", (0.2, 0.2, 0.25), rough=0.3, spec=0.6)
    red = paint("h_red", (0.9, 0.1, 0.08))
    sphere("h_body", 1.0, (-0.75, 0, 1.55), yel, v.body, scale=(1.15, 1.0, 0.95), segs=32, rings=18)
    box("h_belly", (1.6, 1.5, 0.45), (0.35, 0, 0.95), yel, v.body, bevel=0.22)
    sphere("h_bubble", 0.95, (0.45, 0, 1.6), glass(), v.body, scale=(1.05, 0.85, 0.85), segs=32, rings=18)
    torus("h_ring", 0.82, 0.07, (-0.05, 0, 1.6), yel, v.body, rot=(0, math.radians(90), 0))
    box("h_seat", (0.3, 0.5, 0.5), (0.0, 0, 1.4), mat("seat", (0.3, 0.32, 0.4)), v.body, bevel=0.06)
    cyl("h_tail", 0.28, 3.2, (-2.9, 0, 1.75), yel, v.body, rot=(0, math.radians(90), 0), r2=0.14)
    box("h_fin", (0.6, 0.1, 0.9), (-4.4, 0, 2.1), red, v.body, bevel=0.08)
    trot = empty("tail_rotor", (-4.4, 0.15, 2.1), v.body)
    for a in (0, 90):
        box("tr_blade", (0.08, 0.04, 1.0), (0, 0, 0), darkm, trot, bevel=0.02, rot=(0, math.radians(a), 0))
    cyl("h_mast", 0.12, 0.5, (-0.4, 0, 2.7), darkm, v.body, verts=12)
    rot = empty("rotor", (-0.4, 0, 2.95), v.body)
    cyl("hub", 0.22, 0.14, (0, 0, 0), red, rot, verts=16)
    for a in (0, 90):
        box("blade", (6.2, 0.32, 0.05), (0, 0, 0), darkm, rot, bevel=0.03, rot=(0, 0, math.radians(a)))
    for s in (-1, 1):
        cyl("skid", 0.07, 3.0, (0, s * 0.85, 0.12), darkm, v.body, rot=(0, math.radians(90), 0), verts=10)
        for x in (-0.6, 0.6):
            cyl("strut", 0.05, 0.8, (x, s * 0.7, 0.5), darkm, v.body, rot=(s * math.radians(-15), 0, 0), verts=8)
        sphere("navlight", 0.08, (-0.75, s * 1.0, 1.55), mat("nav" + str(s), (1, 0.1, 0.1) if s > 0 else (0.1, 1, 0.2), emit=2.0), v.body)
    lm = mat("heli_red_light", C["red"], emit=0, unique=True)
    sphere("h_light", 0.12, (-0.75, 0, 2.55), lm, v.body)
    v.lights.append(lm)
    v.parts.update(rotor=rot, tail_rotor=trot)
    v.seat = empty("heli_seat", (0.25, 0, 1.15), v.body)
    v.driver = None
    return v


def make_bubblecar(color=(0.6, 0.3, 0.9)):
    v = Vehicle("bubble")
    v.root = empty("bubble"); v.body = empty("bubble_body", parent=v.root)
    c = paint("bubble_col", color)
    box("b_low", (2.6, 1.65, 0.7), (0, 0, 0.75), c, v.body, bevel=0.3, segs=5)
    hip = cab(v, -0.8, 0.55, 1.08, 1.95, 1.55, c, c, front_tilt=22)
    front_face(v, 1.3, 0.5, 0.88, 0.72, 0.5, 1.65, light_r=0.22, grille_w=0.6, grille_h=0.3)
    rear_face(v, -1.3, 0.55, 0.85, 0.5, 1.65)
    _wheels2(v, (0.8, -0.8), 0.78, r=0.34, w=0.28)
    driver(v, hip)
    return v


def park_vehicles(st, which=None):
    makers = [make_police, make_ambulance, make_firetruck, make_towtruck, make_helicopter]
    vs = []
    for i, mk in enumerate(makers):
        if which is not None and i not in which:
            vs.append(None)
            continue
        v = mk()
        v.root.location = (DOOR_X[i], STATION_Y + 3.6, 0)
        v.root.rotation_euler = (0, 0, math.radians(-90))
        if v.kind == "heli":
            v.root.scale = (0.8, 0.8, 0.8)
            v.parts["rotor"].scale = (0.5, 0.5, 1)
        vs.append(v)
    return vs


# make lib's own references (e.g. in game/intros) use the new designs too
lib.make_police, lib.make_ambulance, lib.make_firetruck = make_police, make_ambulance, make_firetruck
lib.make_towtruck, lib.make_helicopter, lib.make_bubblecar = make_towtruck, make_helicopter, make_bubblecar


def make_recycler():
    """Green & white recycling truck (Murat's)."""
    v = Vehicle("recycler")
    v.root = empty("recycler"); v.body = empty("recycler_body", parent=v.root)
    white = paint("r_white", (0.96, 0.97, 0.97))
    green = paint("r_green", (0.12, 0.62, 0.28))
    box("r_base", (5.0, 2.1, 0.8), (-0.2, 0, 0.9), green, v.body, bevel=0.3, segs=5)
    box("r_hood", (0.6, 1.8, 0.25), (2.0, 0, 1.4), white, v.body, bevel=0.1)
    hip = cab(v, 0.75, 1.75, 1.3, 2.45, 2.0, white, white, front_tilt=8, back_glass=False)
    box("r_box", (3.0, 2.15, 2.0), (-1.05, 0, 2.15), green, v.body, bevel=0.35, segs=5)
    box("r_rear", (0.4, 2.0, 1.8), (-2.6, 0, 1.95), mat("r_dark", (0.2, 0.3, 0.25), rough=0.5), v.body, bevel=0.15)
    for sd, rz in ((-1, 0), (1, 180)):
        text("r_sym", "♻", 1.2, (-1.05, sd * 1.09, 2.2), white, v.body, rot=(math.radians(90), 0, math.radians(rz)), font=FONT_SYM, extrude=0.02, bevel=0)
        box("r_stripe", (5.05, 0.04, 0.16), (-0.2, sd * 1.06, 1.05), white, v.body, bevel=0.02)
    front_face(v, 2.25, 0.65, 1.05, 0.85, 0.55, 2.1, light_r=0.26, grille_w=1.0, grille_h=0.48)
    rear_face(v, -2.75, 0.75, 1.0, 0.55, 2.1)
    mirrors(v, 1.7, 1.05, 1.8, white)
    _wheels2(v, (1.35, -0.7, -1.8), 0.98, r=0.46)
    light_bar(v, 1.25, 2.68, w=1.4, colors=("orange", "orange"))
    driver(v, hip)
    return v
lib.park_vehicles = park_vehicles
