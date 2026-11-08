"""Cute stylised 3D people (big head, big eyes) built from primitives + simple pose animation.

Everyone faces +X. Pivots (empties) allow posing: shoulders, elbows, hips, knees, head.
"""
import math, random
from mathutils import Vector
from lib import (empty, sphere, cyl, box, torus, cone, mat, keys, key, bake, C, FPS, ease)

SKIN = {"light": (1.0, 0.78, 0.64), "tan": (0.88, 0.62, 0.45), "brown": (0.6, 0.38, 0.24)}
HAIR = {"brown": (0.28, 0.14, 0.06), "black": (0.05, 0.04, 0.04), "blond": (0.95, 0.72, 0.3),
        "red": (0.85, 0.3, 0.08), "auburn": (0.5, 0.2, 0.08)}
IRIS = {"brown": (0.35, 0.18, 0.06), "blue": (0.15, 0.45, 0.85), "green": (0.2, 0.6, 0.3), "hazel": (0.45, 0.35, 0.12)}


class Person:
    def __init__(self):
        self.p = {}
        self.eyes = []
        self.happy = self.sad = self.oh = None


def capsule(name, r, length, m, parent, loc=(0, 0, 0)):
    """Vertical capsule hanging downward from loc (top) by length."""
    o = empty(name, loc, parent)
    cyl(name + "c", r, length, (0, 0, -length / 2), m, o, verts=16)
    sphere(name + "a", r, (0, 0, 0), m, o, segs=16, rings=10)
    sphere(name + "b", r, (0, 0, -length), m, o, segs=16, rings=10)
    return o


def make_person(name, H=1.2, skin="light", hair="brown", hair_style="short", iris="brown",
                shirt=(0.2, 0.6, 1.0), pants=(0.2, 0.25, 0.45), shoes=(0.9, 0.2, 0.2),
                hat=None, dress=False, bow=(1.0, 0.35, 0.6), seated=False):
    P = Person()
    P.H = H
    sk = mat("skin_" + skin, SKIN[skin], rough=0.55, spec=0.35)
    hm = mat("hair_" + hair, HAIR[hair], rough=0.45, spec=0.5)
    sh = mat(f"cloth{shirt}", shirt, rough=0.7, spec=0.2)
    pa = mat(f"cloth{pants}", pants, rough=0.75, spec=0.2)
    so = mat(f"shoe{shoes}", shoes, rough=0.35, spec=0.5)
    root = empty(name)
    P.root = root
    leg = 0.30 * H
    torso = 0.27 * H
    hr = 0.205 * H  # head radius
    tw = 0.12 * H  # torso half width
    body = empty(name + "_body", (0, 0, 0), root)
    P.body = body
    hips = empty(name + "_hips", (0, 0, leg), body)
    P.p["hips"] = hips
    # legs
    for side, s in (("l", 1), ("r", -1)):
        hp = empty(f"{name}_{side}hip", (0, s * 0.055 * H, 0), hips)
        capsule(f"{name}_{side}thigh", 0.05 * H, leg * 0.48, pa if not dress else sk, hp)
        kn = empty(f"{name}_{side}knee", (0, 0, -leg * 0.5), hp)
        capsule(f"{name}_{side}shin", 0.045 * H, leg * 0.42, sk if dress else pa, kn)
        sphere(f"{name}_{side}shoe", 0.07 * H, (0.035 * H, 0, -leg * 0.46), so, kn, scale=(1.5, 0.95, 0.75))
        P.p[side + "hip"] = hp
        P.p[side + "knee"] = kn
    # torso
    tor = empty(name + "_torso", (0, 0, 0), hips)
    P.p["torso"] = tor
    if dress:
        cone(name + "_dress", 0.2 * H, torso * 1.05, (0, 0, torso * 0.45), sh, tor, verts=24).scale = (0.85, 1, 1)
        sphere(name + "_chest", tw * 0.95, (0, 0, torso * 0.75), sh, tor, scale=(0.8, 1, 0.9))
    else:
        sphere(name + "_belly", tw, (0, 0, torso * 0.45), sh, tor, scale=(0.82, 1.0, 1.25))
        sphere(name + "_seat", tw * 0.95, (0, 0, torso * 0.05), pa, tor, scale=(0.8, 1.0, 0.55))
    # arms
    for side, s in (("l", 1), ("r", -1)):
        shp = empty(f"{name}_{side}sh", (0, s * (tw + 0.02 * H), torso * 0.85), tor)
        capsule(f"{name}_{side}uarm", 0.042 * H, 0.14 * H, sh, shp)
        el = empty(f"{name}_{side}el", (0, 0, -0.15 * H), shp)
        capsule(f"{name}_{side}farm", 0.038 * H, 0.12 * H, sk, el)
        sphere(f"{name}_{side}hand", 0.05 * H, (0, 0, -0.135 * H), sk, el)
        shp.rotation_euler.x = s * math.radians(8)
        P.p[side + "sh"] = shp
        P.p[side + "el"] = el
    # head
    neck = empty(name + "_neck", (0, 0, torso * 0.98), tor)
    cyl(name + "_neckc", 0.04 * H, 0.06 * H, (0, 0, 0.02 * H), sk, neck, verts=12)
    head = empty(name + "_head", (0, 0, 0.05 * H + hr * 0.9), neck)
    P.p["head"] = head
    sphere(name + "_skull", hr, (0, 0, 0), sk, head, scale=(0.95, 1.0, 0.97), segs=32, rings=18)
    sphere(name + "_jaw", hr * 0.78, (hr * 0.12, 0, -hr * 0.3), sk, head, scale=(1, 1.05, 0.85), segs=24, rings=14)
    for s in (1, -1):
        sphere(name + "_ear", hr * 0.2, (-hr * 0.05, s * hr * 0.97, -hr * 0.08), sk, head, scale=(0.6, 0.4, 1))
        sphere(name + "_cheek", hr * 0.16, (hr * 0.8, s * hr * 0.5, -hr * 0.32), mat("cheek", (1.0, 0.5, 0.55), rough=0.6, alpha=0.55), head, scale=(0.4, 1, 0.7))
    sphere(name + "_nose", hr * 0.11, (hr * 0.98, 0, -hr * 0.18), mat("nose_" + skin, tuple(c * 0.92 for c in SKIN[skin]), rough=0.5), head, scale=(0.8, 1, 0.8))
    # eyes with coloured iris
    white = mat("eyewhite", C["white"], rough=0.15)
    irm = mat("iris_" + iris, IRIS[iris], rough=0.15, spec=0.6)
    pup = mat("pupil", C["dark"], rough=0.1)
    for s in (1, -1):
        e = empty(f"{name}_eye{s}", (hr * 0.78, s * hr * 0.34, -0.02 * hr), head)
        sphere("sclera", hr * 0.31, (0, 0, 0), white, e, scale=(0.5, 0.82, 1.0))
        sphere("iris", hr * 0.24, (hr * 0.1, 0, -hr * 0.02), irm, e, scale=(0.35, 0.82, 1.0))
        sphere("pup", hr * 0.13, (hr * 0.16, 0, -hr * 0.02), pup, e, scale=(0.3, 1, 1))
        sphere("hl", hr * 0.065, (hr * 0.19, -hr * 0.07, hr * 0.1), white, e)
        sphere("hl2", hr * 0.03, (hr * 0.18, hr * 0.05, -hr * 0.08), white, e)
        P.eyes.append(e)
        br = empty(f"{name}_brow{s}", (hr * 0.86, s * hr * 0.34, hr * 0.38), head)
        box("brow", (0.04 * hr, hr * 0.3, hr * 0.06), (0, 0, 0), hm, br, bevel=0.01)
        P.p[f"brow{s}"] = br
    mm = mat("lips", (0.75, 0.25, 0.28), rough=0.4)
    P.happy = torus(name + "_smile", hr * 0.24, hr * 0.035, (hr * 0.9, 0, -hr * 0.42), mm, head, rot=(0, 0, math.radians(90)), half="low")
    P.sad = torus(name + "_frown", hr * 0.15, hr * 0.035, (hr * 0.9, 0, -hr * 0.52), mm, head, rot=(0, 0, math.radians(90)), half="high")
    P.oh = sphere(name + "_oh", hr * 0.09, (hr * 0.93, 0, -hr * 0.45), mat("mouthin", (0.35, 0.05, 0.08), rough=0.4), head, scale=(0.4, 1, 1.2))
    P.sad.scale = (0.001,) * 3
    P.oh.scale = (0.001,) * 3
    # hair
    if hair_style in ("short", "pigtails", "bun", "spiky"):
        sphere(name + "_hairtop", hr * 1.05, (-hr * 0.12, 0, hr * 0.14), hm, head, scale=(1.0, 1.04, 0.95), segs=28, rings=16)
        sphere(name + "_fringe", hr * 0.62, (hr * 0.45, 0, hr * 0.62), hm, head, scale=(0.75, 1.35, 0.5))
        if hair_style == "spiky":
            for k in range(5):
                cone(name + "_spike", hr * 0.22, hr * 0.5, (-hr * 0.2 + k * 0.05 * hr, (k - 2) * hr * 0.28, hr * 1.0), hm, head, rot=(math.radians((k - 2) * 15), math.radians(-20), 0), verts=10)
    if hair_style == "pigtails":
        bm = mat(f"bow{bow}", bow, rough=0.35)
        for s in (1, -1):
            sphere(name + "_tail", hr * 0.42, (-hr * 0.35, s * hr * 1.08, -hr * 0.15), hm, head, scale=(0.9, 0.8, 1.25))
            for b in (1, -1):
                sphere(name + "_bow", hr * 0.13, (-hr * 0.2, s * hr * 0.9 + b * hr * 0.1, hr * 0.25), bm, head, scale=(0.6, 1, 0.7))
    if hair_style == "bun":
        sphere(name + "_bun", hr * 0.42, (-hr * 0.55, 0, hr * 0.85), hm, head)
    # hats
    if hat == "police":
        hc = mat("police_cap", (0.08, 0.12, 0.3), rough=0.4)
        cyl(name + "_cap", hr * 1.02, hr * 0.38, (-hr * 0.02, 0, hr * 0.78), hc, head, verts=28, r2=hr * 1.12)
        box(name + "_visor", (hr * 0.5, hr * 1.3, hr * 0.06), (hr * 0.9, 0, hr * 0.6), mat("visor", (0.02, 0.02, 0.03), rough=0.2), head, bevel=0.02, rot=(0, math.radians(-12), 0))
        sphere(name + "_capbadge", hr * 0.12, (hr * 1.02, 0, hr * 0.82), mat("gold", (1.0, 0.78, 0.2), rough=0.2, spec=0.9), head, scale=(0.3, 1, 1))
    elif hat == "fire":
        hc = mat("fire_helmet", (0.95, 0.75, 0.05), rough=0.25)
        sphere(name + "_helm", hr * 1.12, (-hr * 0.05, 0, hr * 0.25), hc, head, scale=(1, 1, 0.85))
        cyl(name + "_brim", hr * 1.35, hr * 0.06, (-hr * 0.1, 0, hr * 0.1), hc, head, verts=28)
        box(name + "_shield", (hr * 0.08, hr * 0.5, hr * 0.4), (hr * 1.0, 0, hr * 0.6), mat("fire_red", (0.92, 0.07, 0.05)), head, bevel=0.03)
    elif hat == "pilot":
        hc = mat("pilot_helmet", (0.95, 0.95, 0.97), rough=0.25)
        sphere(name + "_helm", hr * 1.12, (-hr * 0.05, 0, hr * 0.2), hc, head, scale=(1, 1, 0.92))
        sphere(name + "_goggle", hr * 0.5, (hr * 0.65, 0, hr * 0.68), mat("goggle", (0.2, 0.5, 0.8), rough=0.05, spec=0.9), head, scale=(0.4, 1.4, 0.55))
    elif hat == "cap":
        hc = mat("mech_cap", (1.0, 0.45, 0.03), rough=0.5)
        sphere(name + "_cap", hr * 1.06, (-hr * 0.05, 0, hr * 0.35), hc, head, scale=(1, 1, 0.75))
        box(name + "_visor", (hr * 0.6, hr * 1.0, hr * 0.06), (hr * 0.95, 0, hr * 0.42), hc, head, bevel=0.02, rot=(0, math.radians(-8), 0))
    elif hat == "medic":
        hc = mat("medic_cap", (0.95, 0.95, 0.95), rough=0.5)
        cyl(name + "_mcap", hr * 0.95, hr * 0.3, (-hr * 0.05, 0, hr * 0.88), hc, head, verts=24, r2=hr * 0.85)
        box(name + "_mcross1", (hr * 0.04, hr * 0.32, hr * 0.1), (hr * 0.88, 0, hr * 0.9), mat("amb_red", C["red"]), head, bevel=0.01)
        box(name + "_mcross2", (hr * 0.04, hr * 0.1, hr * 0.28), (hr * 0.88, 0, hr * 0.9), mat("amb_red", C["red"]), head, bevel=0.01)
    if seated:
        sit(P)
    return P


# ----------------------------------------------------------------------------- posing

def rot(P, part, f, xyz):
    o = P.p[part]
    key(o, "rotation_euler", f, tuple(math.radians(a) for a in xyz))


def sit(P):
    for s in ("l", "r"):
        P.p[s + "hip"].rotation_euler = (0, math.radians(-85), 0)
        P.p[s + "knee"].rotation_euler = (0, math.radians(85), 0)
    for s, sg in (("l", 1), ("r", -1)):
        P.p[s + "sh"].rotation_euler = (sg * math.radians(10), math.radians(-35), 0)
        P.p[s + "el"].rotation_euler = (0, math.radians(-45), 0)


def mood(P, f, m):
    """m in happy|sad|oh"""
    for name, o in (("happy", P.happy), ("sad", P.sad), ("oh", P.oh)):
        on = name == m
        cur = (1, 1, 1) if on else (0.001,) * 3
        keys(o, "scale", [(f, tuple(o.scale)), (f + 4, cur)])
        o.scale = cur
    ang = {"happy": 0, "sad": 18, "oh": -12}[m]
    for s in (1, -1):
        b = P.p[f"brow{s}"]
        keys(b, "rotation_euler", [(f + 4, (s * math.radians(ang) * -1, 0, 0))])
        keys(b, "location", [(f + 4, (b.location.x, b.location.y, P.H * 0.19 * (0.33 + (0.06 if m == "oh" else 0))))])


def blink(P, frames):
    for f in frames:
        for e in P.eyes:
            keys(e, "scale", [(f, (1, 1, 1)), (f + 2, (1, 1, 0.08)), (f + 5, (1, 1, 1))])


def auto_blink(P, f0, f1, seed=1):
    r = random.Random(seed)
    f = f0 + r.randint(10, 50)
    fs = []
    while f < f1 - 6:
        fs.append(f)
        f += r.randint(60, 110)
    blink(P, fs)


def arms_down(P, f):
    rot(P, "lsh", f, (8, 0, 0)); rot(P, "rsh", f, (-8, 0, 0))
    rot(P, "lel", f, (0, 0, 0)); rot(P, "rel", f, (0, 0, 0))


def wave(P, f0, f1, side="r", seated=False):
    s = 1 if side == "l" else -1
    shp, elp = side + "sh", side + "el"
    base_y = -35 if seated else 0
    rot(P, shp, f0, (s * 8, base_y, 0))
    rot(P, shp, f0 + 6, (s * 145, 0, 0))
    f = f0 + 6
    i = 0
    while f < f1 - 6:
        rot(P, elp, f, (s * (25 if i % 2 == 0 else -15), 0, 0))
        f += 6
        i += 1
    rot(P, elp, f1 - 6, (0, -45 if seated else 0, 0))
    rot(P, shp, f1, (s * 10, base_y, 0))


def cheer(P, f0, n=3, h=None, period=14):
    h = P.H * 0.35 if h is None else h
    rot(P, "lsh", f0, (8, 0, 0)); rot(P, "rsh", f0, (-8, 0, 0))
    rot(P, "lsh", f0 + 5, (160, 0, 0)); rot(P, "rsh", f0 + 5, (-160, 0, 0))
    z0 = P.root.location.z
    for i in range(n):
        f = f0 + 4 + i * period
        P.root.location.z = z0
        P.root.keyframe_insert("location", index=2, frame=f)
        P.root.location.z = z0 + h
        P.root.keyframe_insert("location", index=2, frame=f + period // 2)
    P.root.location.z = z0
    P.root.keyframe_insert("location", index=2, frame=f0 + 4 + n * period)
    rot(P, "lsh", f0 + 6 + n * period, (160, 0, 0)); rot(P, "rsh", f0 + 6 + n * period, (-160, 0, 0))
    rot(P, "lsh", f0 + 14 + n * period, (8, 0, 0)); rot(P, "rsh", f0 + 14 + n * period, (-8, 0, 0))


def sad_pose(P, f0, f1):
    rot(P, "head", f0, (0, 14, 0)); rot(P, "head", f1, (0, 14, 0))
    rot(P, "head", f1 + 8, (0, 0, 0))
    rot(P, "lsh", f0, (8, -40, 0)); rot(P, "rsh", f0, (-8, -40, 0))
    rot(P, "lel", f0, (0, -100, 0)); rot(P, "rel", f0, (0, -100, 0))
    rot(P, "lsh", f1, (8, -40, 0)); rot(P, "rsh", f1, (-8, -40, 0))
    rot(P, "lel", f1, (0, -100, 0)); rot(P, "rel", f1, (0, -100, 0))
    arms_down(P, f1 + 8)


def point(P, f0, f1, up=30, side="r"):
    s = 1 if side == "l" else -1
    rot(P, side + "sh", f0, (s * 8, 0, 0))
    rot(P, side + "sh", f0 + 8, (s * 20, -(90 + up), 0))
    rot(P, side + "sh", f1, (s * 20, -(90 + up), 0))
    rot(P, side + "sh", f1 + 8, (s * 8, 0, 0))


def look(P, f, yaw=0, pitch=0):
    rot(P, "head", f, (0, pitch, yaw))


def walk(P, f0, f1, step=10):
    """Leg/arm swing (root motion is animated separately)."""
    frames = list(range(f0, f1 + 1, 2))
    for side, ph in (("l", 0), ("r", math.pi)):
        a = [(0, math.radians(28) * math.sin(2 * math.pi * (f - f0) / (2 * step) + ph), 0) for f in frames]
        bake(P.p[side + "hip"], "rotation_euler", frames, a)
        k = [(0, max(0, math.radians(35) * math.sin(2 * math.pi * (f - f0) / (2 * step) + ph + 1.2)), 0) for f in frames]
        bake(P.p[side + "knee"], "rotation_euler", frames, k)
    for side, ph, s in (("l", math.pi, 1), ("r", 0, -1)):
        a = [(s * math.radians(8), math.radians(25) * math.sin(2 * math.pi * (f - f0) / (2 * step) + ph), 0) for f in frames]
        bake(P.p[side + "sh"], "rotation_euler", frames, a)
