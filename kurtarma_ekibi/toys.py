"""Toy-style vehicles and world (smooth plastic toys, no faces): original designs for the 'Minik Ustalar' videos.

All vehicles face +X, origin on the ground under the middle. Motion comes from drive_path (smooth path, wheels
turn with the distance, the body leans when braking / accelerating) and small helpers (hop, crane control).
"""
import bpy, math, random
from mathutils import Vector
import lib
from lib import box, cyl, sphere, empty, mat, bake, C

R90 = math.radians(90)


def P(name, col, rough=0.32, spec=0.5, **kw):
    return mat("toy_" + name, col, rough=rough, spec=spec, **kw)


COL = dict(red=(0.93, 0.07, 0.07), yellow=(1.0, 0.74, 0.02), orange=(1.0, 0.38, 0.02), blue=(0.04, 0.36, 0.95),
           green=(0.2, 0.75, 0.16), teal=(0.0, 0.7, 0.72), purple=(0.55, 0.22, 0.9), pink=(1.0, 0.36, 0.62),
           cream=(1.0, 0.9, 0.7), white=(0.96, 0.96, 0.96), wood=(0.93, 0.66, 0.32), wood2=(0.8, 0.5, 0.2),
           dark=(0.05, 0.05, 0.06), gray=(0.6, 0.62, 0.66), glass=(0.3, 0.62, 0.95))


ALL = []


class Toy:
    def __init__(self, name, loc=(0, 0), heading=0.0):
        ALL.append(self)
        self.name = name
        self.root = empty(name, (loc[0], loc[1], 0))
        self.root.rotation_euler.z = math.radians(heading)
        self.body = empty(name + "_body", parent=self.root)       # leans / bounces
        self.wheels = []
        self.r = 0.5
        self.dist = 0.0
        self.track = {}                                            # frame -> (x, y, heading rad)
        self.last = (loc[0], loc[1], math.radians(heading))
        self.first = self.last
        self.busy = []

    def pose(self, f):
        if f in self.track:
            return self.track[f]
        ks = [k for k in self.track if k <= f]
        return self.track[max(ks)] if ks else self.first

    def at(self, f, local):
        x, y, h = self.pose(f)
        c, s = math.cos(h), math.sin(h)
        return Vector((x + local[0] * c - local[1] * s, y + local[0] * s + local[1] * c, local[2]))


def wheel(t, x, y, r=0.5, w=0.42, hub=None, tread=False):
    wh = empty(t.name + "_wheel", (x, y, r), t.root)
    cyl("tire", r, w, (0, 0, 0), P("tire", (0.045, 0.045, 0.05), rough=0.75, spec=0.2), wh, rot=(R90, 0, 0), bevel=r * 0.22, verts=32)
    cyl("hub", r * 0.58, w + 0.05, (0, 0, 0), P("hub", hub or COL["white"]), wh, rot=(R90, 0, 0), bevel=0.04, verts=24)
    cyl("cap", r * 0.2, w + 0.12, (0, 0, 0), P("cap", COL["gray"]), wh, rot=(R90, 0, 0), bevel=0.03, verts=16)
    if tread:
        for k in range(10):
            a = 2 * math.pi * k / 10
            box("lug", (0.16, w * 0.96, 0.12), (math.cos(a) * r, 0, math.sin(a) * r), P("tire", (0.045, 0.045, 0.05)), wh,
                bevel=0.03, rot=(0, -a + R90, 0))
    t.wheels.append(wh)
    t.r = r
    return wh


def lamps(t, x, y, z, r=0.14):
    for s in (-1, 1):
        cyl("lamp", r, 0.08, (x, s * y, z), P("lamp", (1.0, 0.95, 0.7), rough=0.1, emit=1.2), t.body, rot=(0, R90, 0), bevel=0.02)
        cyl("lampring", r * 1.25, 0.05, (x - 0.02, s * y, z), P("white", COL["white"]), t.body, rot=(0, R90, 0), bevel=0.02)


def cab(t, x, z, col, L=1.5, W=1.9, H=1.35):
    """Rounded truck cab with a windscreen and side windows; x = centre, z = floor of the cab."""
    m = P(t.name + "_cab", col)
    g = P("glass", COL["glass"], rough=0.08, spec=0.9)
    box("cab", (L, W, H), (x, 0, z + H / 2), m, t.body, bevel=0.3, segs=5)
    box("wind", (0.1, W * 0.78, H * 0.42), (x + L / 2 - 0.02, 0, z + H * 0.66), g, t.body, bevel=0.1, rot=(0, math.radians(-8), 0))
    for s in (-1, 1):
        box("swin", (L * 0.5, 0.08, H * 0.38), (x + 0.02, s * (W / 2 - 0.02), z + H * 0.66), g, t.body, bevel=0.08)
    box("roof", (L * 0.86, W * 0.86, 0.1), (x, 0, z + H + 0.02), P("white", COL["white"]), t.body, bevel=0.05)


def make_car(name, col, number=None, loc=(0, 0), heading=0.0):
    """Small round runabout."""
    t = Toy(name, loc, heading)
    m = P(name, col)
    box("low", (2.5, 1.5, 0.55), (0, 0, 0.62), m, t.body, bevel=0.27, segs=6)
    sphere("dome", 0.72, (-0.15, 0, 0.92), P("glass", COL["glass"], rough=0.08, spec=0.9), t.body, scale=(1.05, 0.88, 0.8), segs=32, rings=18)
    sphere("domecap", 0.3, (-0.15, 0, 1.44), m, t.body, scale=(1.5, 1.2, 0.22), segs=24, rings=12)
    for s in (-1, 1):
        for x in (0.82, -0.82):
            box("fender", (0.95, 0.3, 0.3), (x, s * 0.72, 0.78), m, t.body, bevel=0.14, segs=4)
    box("bumper", (0.16, 1.5, 0.2), (1.26, 0, 0.45), P("white", COL["white"]), t.body, bevel=0.08)
    box("bumper2", (0.16, 1.5, 0.2), (-1.26, 0, 0.45), P("white", COL["white"]), t.body, bevel=0.08)
    lamps(t, 1.25, 0.48, 0.72, r=0.13)
    for x in (0.82, -0.82):
        for s in (-1, 1):
            wheel(t, x, s * 0.78, r=0.42, w=0.34, hub=COL["yellow"] if col != COL["yellow"] else COL["red"])
    return t


def make_flatbed(name, col, loc=(0, 0), heading=0.0):
    """Long truck with a flat load bed (bed_z = top of the bed, bed_x = middle of the bed)."""
    t = Toy(name, loc, heading)
    m = P(name, col)
    box("chassis", (7.0, 1.7, 0.4), (0, 0, 0.78), P("dark2", (0.16, 0.17, 0.2)), t.body, bevel=0.12)
    cab(t, 2.55, 0.9, col, L=1.6, W=2.1, H=1.45)
    box("nose", (0.5, 2.0, 0.6), (3.45, 0, 1.22), m, t.body, bevel=0.22, segs=4)
    box("bed", (5.3, 2.3, 0.22), (-0.95, 0, 1.12), P("bed", COL["cream"]), t.body, bevel=0.08)
    for s in (-1, 1):
        box("rail", (5.3, 0.14, 0.26), (-0.95, s * 1.1, 1.3), m, t.body, bevel=0.06)
    box("head", (0.16, 2.3, 0.7), (1.62, 0, 1.5), m, t.body, bevel=0.07)
    box("bump", (0.2, 2.2, 0.26), (3.74, 0, 0.72), P("white", COL["white"]), t.body, bevel=0.1)
    lamps(t, 3.72, 0.7, 1.22)
    for x in (2.55, -1.6, -2.9):
        for s in (-1, 1):
            wheel(t, x, s * 1.0, r=0.56, w=0.44, hub=COL["yellow"])
    t.bed_z, t.bed_x = 1.23, -0.95
    return t


def make_crane(name, col, loc=(0, 0), heading=0.0, boom=8.2):
    """Crane truck: turret turns, boom lifts, the cable and hook hang straight down (see crane_bake)."""
    t = Toy(name, loc, heading)
    m = P(name, col)
    m2 = P(name + "_2", COL["yellow"])
    box("chassis", (5.6, 1.9, 0.5), (0, 0, 0.85), P("dark2", (0.16, 0.17, 0.2)), t.body, bevel=0.14)
    cab(t, 1.95, 1.0, col, L=1.5, W=2.1, H=1.4)
    box("nose", (0.45, 2.0, 0.6), (2.82, 0, 1.3), m, t.body, bevel=0.22, segs=4)
    box("deck", (3.7, 2.2, 0.3), (-0.9, 0, 1.25), m, t.body, bevel=0.12)
    box("bump", (0.2, 2.2, 0.26), (3.08, 0, 0.76), P("white", COL["white"]), t.body, bevel=0.1)
    lamps(t, 3.06, 0.7, 1.3)
    for x in (1.95, -0.6, -1.9):
        for s in (-1, 1):
            wheel(t, x, s * 1.02, r=0.6, w=0.46, hub=COL["red"])
    crane_gear(t, -1.0, 1.4, boom)
    return t


def crane_gear(t, px, dz, boom=8.2, col=None):
    """Turret + boom + cable + hook on a vehicle: px = pivot along the vehicle, dz = height of the platform."""
    name = t.name
    m2 = P(name + "_2", col or COL["yellow"])
    t.pivot = Vector((px, 0, dz + 0.8))
    t.turret = empty(name + "_turret", (px, 0, dz), t.body)
    cyl("ring", 0.85, 0.3, (0, 0, 0.1), P("gray", COL["gray"]), t.turret, bevel=0.06, verts=32)
    box("house", (1.5, 1.3, 0.9), (-0.25, 0, 0.7), m2, t.turret, bevel=0.25, segs=4)
    box("hwin", (0.08, 0.9, 0.4), (0.5, 0, 0.82), P("glass", COL["glass"], rough=0.08, spec=0.9), t.turret, bevel=0.06)
    t.boom = empty(name + "_boom", (0, 0, 0.8), t.turret)
    box("boom1", (boom * 0.58, 0.5, 0.5), (boom * 0.29 - 0.2, 0, 0), m2, t.boom, bevel=0.12)
    box("boom2", (boom * 0.5, 0.36, 0.36), (boom * 0.75 - 0.1, 0, 0), P("white", COL["white"]), t.boom, bevel=0.09)
    cyl("tipw", 0.26, 0.42, (boom, 0, 0), P("red", COL["red"]), t.boom, rot=(R90, 0, 0), bevel=0.05)
    cyl("pin", 0.3, 0.9, (0, 0, 0), P("gray", COL["gray"]), t.boom, rot=(R90, 0, 0), bevel=0.05)
    t.L = boom
    # cable (unit length, hangs down from its origin) and hook: free objects, baked in world space
    t.cable = empty(name + "_cable")
    cyl("cab", 0.035, 1.0, (0, 0, -0.5), P("cable", (0.12, 0.12, 0.14)), t.cable, verts=8)
    t.hook = empty(name + "_hook")
    box("block", (0.36, 0.3, 0.44), (0, 0, 0.3), P("red", COL["red"]), t.hook, bevel=0.1)
    lib.torus("hk", 0.16, 0.05, (0, 0, 0.02), P("gray", COL["gray"]), t.hook)
    t.ctl = []
    return t


HUBS = dict(car=(1.0, 0.74, 0.02), tow=(0.96, 0.96, 0.96), dump=(0.96, 0.96, 0.96), crane=(0.93, 0.07, 0.07), flat=(1.0, 0.74, 0.02))


def toy_wheel(t, loc, r, w, hub):
    """Clean toy wheel whose turning is easy to see: chunky tread blocks and five bolts on the hub."""
    wh = empty(t.name + "_wheel", loc, t.root)
    tire = P("tire", (0.045, 0.045, 0.05), rough=0.75, spec=0.2)
    cyl("tire", r * 0.93, w, (0, 0, 0), tire, wh, rot=(R90, 0, 0), bevel=r * 0.16, verts=28)
    n = 9
    for k in range(n):
        a = 2 * math.pi * k / n
        box("lug", (r * 0.34, w * 0.98, r * 0.16), (math.cos(a) * r * 0.93, 0, math.sin(a) * r * 0.93), tire, wh, bevel=0.03, rot=(0, -a + R90, 0), segs=2)
    cyl("hub", r * 0.56, w + 0.06, (0, 0, 0), P("hub_" + t.name, hub), wh, rot=(R90, 0, 0), bevel=0.04, verts=24)
    cyl("cap", r * 0.17, w + 0.14, (0, 0, 0), P("cap", COL["gray"]), wh, rot=(R90, 0, 0), bevel=0.03, verts=12)
    for k in range(5):
        a = 2 * math.pi * k / 5
        cyl("bolt", r * 0.075, w + 0.11, (math.cos(a) * r * 0.36, 0, math.sin(a) * r * 0.36), P("cap", COL["gray"]), wh, rot=(R90, 0, 0), verts=8)
    t.wheels.append(wh)
    return wh


def load_toy(model, name=None, loc=(0, 0), heading=0.0):
    """A Meshy-designed vehicle prepared by meshy_vehicle.py (toys3d/<model>.blend). The body is the Meshy model;
    its wheels are replaced by clean turning toy wheels of the same size, with a dark axle block behind them."""
    import os, json
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "toys3d")
    t = Toy(name or model, loc, heading)
    with bpy.data.libraries.load(os.path.join(d, model + ".blend"), link=False) as (src, dst):
        dst.collections = list(src.collections[:1])
    col = dst.collections[0]
    bpy.context.scene.collection.children.link(col)
    meta = json.load(open(os.path.join(d, model + ".json")))
    ws = []
    for o in list(col.objects):
        if "_wheel" in o.name:
            ys = [v.co.y for v in o.data.vertices]
            m = min(meta["wheels"], key=lambda w: abs(w["x"] - o.location.x))
            ws.append((o.location.x, o.location.y, o.location.z, m["r"], max(ys) - min(ys)))
            bpy.data.objects.remove(o)
        else:
            o.parent = t.body
    dark = P("axle", (0.1, 0.1, 0.12), rough=0.8, spec=0.1)
    for x, y, z, r, w in ws:
        toy_wheel(t, (x, y, z), r * 1.04, min(w, r * 1.1), HUBS.get(model, COL["white"]))
        if y > 0:
            cyl("axle", r * 0.8, 2 * y, (x, 0, z), dark, t.body, rot=(R90, 0, 0), verts=20)
    t.r = sum(w[3] for w in ws) / max(1, len(ws)) * 1.04
    t.meta = meta
    return t


def crane_keys(t, seq):
    """seq: (frame, yaw_deg, pitch_deg, cable_length[, rel]). rel=True: yaw is relative to the truck's heading
    (boom stowed while driving), otherwise yaw is a world direction. Eased between keys."""
    t.ctl = sorted(tuple(k) + ((False,) if len(k) == 4 else ()) for k in list(t.ctl) + list(seq))


def crane_state(t, f):
    ks = t.ctl
    hd = math.degrees(t.pose(f)[2])
    def ab(k):
        return (k[1] + hd if k[4] else k[1], k[2], k[3])
    if f <= ks[0][0]:
        return ab(ks[0])
    for a, b in zip(ks, ks[1:]):
        if a[0] <= f <= b[0]:
            u = (f - a[0]) / max(1, b[0] - a[0])
            u = u * u * (3 - 2 * u)
            A, B = ab(a), ab(b)
            dy = (B[0] - A[0] + 180) % 360 - 180
            return (A[0] + dy * u, A[1] + (B[1] - A[1]) * u, A[2] + (B[2] - A[2]) * u)
    return ab(ks[-1])


def crane_tip(t, f):
    yaw, pitch, cab_ = crane_state(t, f)
    p = t.at(f, t.pivot); p.z = t.pivot.z
    y, ph = math.radians(yaw), math.radians(pitch)
    tip = p + Vector((math.cos(ph) * math.cos(y), math.cos(ph) * math.sin(y), math.sin(ph))) * t.L
    return tip, tip - Vector((0, 0, cab_))


def crane_aim(t, f, target, hook_z):
    """Yaw / pitch / cable length that put the hook over target (x, y) at height hook_z, for the crane parked at f."""
    p = t.at(f, t.pivot)
    d = Vector((target[0] - p.x, target[1] - p.y))
    r = min(d.length, t.L * 0.985)
    pitch = math.degrees(math.acos(r / t.L))
    tipz = t.pivot.z + t.L * math.sin(math.radians(pitch))
    return math.degrees(math.atan2(d.y, d.x)), pitch, tipz - hook_z


def crane_bake(t, N):
    frames = list(range(N + 1))
    yaw, pit, cl, cs, hk = [], [], [], [], []
    for f in frames:
        y, p, c = crane_state(t, f)
        h = t.pose(f)[2]
        yaw.append((0, 0, math.radians(y) - h)); pit.append((0, -math.radians(p), 0))
        tip, hook = crane_tip(t, f)
        cl.append(tuple(tip)); cs.append((1, 1, max(0.05, c))); hk.append(tuple(hook))
    bake(t.turret, "rotation_euler", frames, yaw)
    bake(t.boom, "rotation_euler", frames, pit)
    bake(t.cable, "location", frames, cl)
    bake(t.cable, "scale", frames, cs)
    bake(t.hook, "location", frames, hk)


# ---------------------------------------------------------------- driving

def _spline(pts, n=24):
    P_ = [Vector((p[0], p[1])) for p in pts]
    if len(P_) == 2:
        return [P_[0].lerp(P_[1], k / n) for k in range(n + 1)]
    Q = [P_[0] * 2 - P_[1]] + P_ + [P_[-1] * 2 - P_[-2]]
    out = []
    for i in range(1, len(Q) - 2):
        p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
        for k in range(n):
            u = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
    out.append(P_[-1])
    return out


def _trap(u, r=0.25):
    v = 1.0 / (1.0 - r)
    if u < r:
        return v * u * u / (2 * r)
    if u > 1 - r:
        return 1 - v * (1 - u) ** 2 / (2 * r)
    return v * (u - r / 2)


def drive_path(t, f0, f1, pts, reverse=False, lean=1.0):
    """Drive along a smooth path through pts between f0 and f1 (starts and stops softly)."""
    if t.track and max(t.track) > f0:
        print("RETIME", t.name, "drive at", f0, "starts before the previous one ends at", max(t.track))
    path = _spline([t.last[:2]] + list(pts))
    acc = [0.0]
    for a, b in zip(path, path[1:]):
        acc.append(acc[-1] + (b - a).length)
    total = acc[-1]
    frames = list(range(f0, f1 + 1))
    loc, rot, wr, tl, tr = [], [], [], [], []
    hprev = t.last[2]
    sprev = 0.0; vprev = 0.0
    for f in frames:
        s = _trap((f - f0) / max(1, f1 - f0)) * total
        k = max(1, min(len(acc) - 1, next((i for i, a in enumerate(acc) if a >= s), len(acc) - 1)))
        u = (s - acc[k - 1]) / max(1e-6, acc[k] - acc[k - 1])
        p = path[k - 1].lerp(path[k], u)
        d = path[k] - path[k - 1]
        h = math.atan2(d.y, d.x) + (math.pi if reverse else 0.0)
        h = hprev + (h - hprev + math.pi) % (2 * math.pi) - math.pi
        if f - f0 < 4 and abs(h - hprev) > 0.5:
            h = hprev
        hprev = h
        v = s - sprev; a = v - vprev; sprev = s; vprev = v
        t.dist += -v if reverse else v
        loc.append((p.x, p.y, 0)); rot.append((0, 0, h))
        wr.append((0, t.dist / t.r, 0))
        sg = -1 if reverse else 1
        tr.append((0, max(-0.07, min(0.07, -a * 1.6 * lean * sg)), 0))
        tl.append((0, 0, 0.012 * min(1.0, v * 8) * math.sin(f * 0.9)))
        t.track[f] = (p.x, p.y, h)
    tr = [tuple(sum(x[i] for x in tr[max(0, k - 3):k + 4]) / len(tr[max(0, k - 3):k + 4]) for i in range(3)) for k in range(len(tr))]
    bake(t.root, "location", frames, loc)
    bake(t.root, "rotation_euler", frames, rot)
    for w in t.wheels:
        bake(w, "rotation_euler", frames, wr)
    bake(t.body, "rotation_euler", frames, tr)
    bake(t.body, "location", frames, tl)
    t.last = (loc[-1][0], loc[-1][1], hprev)
    return f1


def park(t):
    """Call once after creating a toy (before any drive) so pose() works from frame 0."""
    t.first = t.last
    t.track[0] = t.last


def hop(t, f0, n=2, h=0.3, period=11):
    """Happy little jumps on the springs (squash before and after)."""
    frames = list(range(f0 - 3, f0 + n * period + 5))
    vals = []
    for f in frames:
        k = f - f0
        if k < 0:
            z = -0.05 * (1 + k / 3)
        elif k >= n * period:
            z = -0.05 * max(0.0, 1 - (k - n * period) / 4)
        else:
            u = (k % period) / period
            z = h * 4 * u * (1 - u)
        vals.append((0, 0, z))
    bake(t.body, "location", frames, vals)
    bake(t.body, "rotation_euler", frames, [(0, -0.05 * math.sin(math.pi * max(0, min(1, (f - f0) / (n * period)))) *
                                             math.sin((f - f0) * 2 * math.pi / period), 0) for f in frames])


def nod(t, f0, deg=4.0, dur=14):
    """Brake dip: the nose goes down and comes back."""
    frames = list(range(f0, f0 + dur + 1))
    bake(t.body, "rotation_euler", frames, [(0, math.radians(deg) * math.sin(math.pi * (f - f0) / dur) ** 2 *
                                             math.cos(1.5 * math.pi * (f - f0) / dur) ** 2 + 0.0, 0) for f in frames])


# ---------------------------------------------------------------- world

def tree(x, y, s=1.0, kind=0, col=None):
    root = empty("tree", (x, y, 0))
    cyl("trunk", 0.16 * s, 1.3 * s, (0, 0, 0.65 * s), P("trunk", (0.62, 0.4, 0.2), rough=0.6), root, verts=12)
    g = P("leaf%d" % (kind % 3), col or [(0.18, 0.72, 0.2), (0.35, 0.8, 0.18), (0.1, 0.62, 0.3)][kind % 3], rough=0.5)
    if kind % 2 == 0:
        sphere("crown", 0.95 * s, (0, 0, 1.9 * s), g, root, scale=(1, 1, 0.9), segs=20, rings=12)
        sphere("crown2", 0.6 * s, (0.5 * s, 0.2 * s, 2.5 * s), g, root, segs=16, rings=10)
    else:
        for k in range(3):
            lib.cone("crown", (1.0 - k * 0.24) * s, 1.1 * s, (0, 0, (1.5 + k * 0.6) * s), g, root, verts=16)
    return root


def cloud(x, y, z, s=1.0):
    m = P("cloud", (1, 1, 1), rough=0.9, emit=0.5, spec=0.0)
    root = empty("cloud", (x, y, z))
    for dx, r in ((-1.4, 1.0), (0, 1.5), (1.5, 1.1), (0.7, 0.9)):
        sphere("c", r * s, (dx * s, 0, (r - 1) * 0.3 * s), m, root, scale=(1, 0.7, 0.75), segs=20, rings=12)


def hangar(x, y, col, w=4.2, d=6.0, h=3.4):
    """Round-topped garage (door faces -Y)."""
    root = empty("hangar", (x, y, 0))
    c = cyl("shell", h, d, (0, d / 2, 0), P("hang_" + str(col), col), root, rot=(R90, 0, 0), verts=40)
    c.scale = (w / 2 / h, 1, 1)
    c2 = cyl("mouth", h * 0.84, 0.3, (0, -0.02, 0), P("hang_in", (0.16, 0.14, 0.2), rough=0.9), root, rot=(R90, 0, 0), verts=40)
    c2.scale = (w / 2 / h * 0.98, 1, 1)
    box("lip", (w + 0.5, 0.5, 0.16), (0, -0.3, 0.06), P("cream", COL["cream"]), root, bevel=0.06)
    return root


def pad(x0, x1, y0, y1, kind="road"):
    """A paved (or dirt) area beside the road where vehicles may drive and park."""
    if kind == "road":
        top = mat("road", (0.22, 0.22, 0.26), rough=0.7, spec=0.2); edge = P("cream", COL["cream"], rough=0.6)
    else:
        top = P("dirt", (0.86, 0.68, 0.42), rough=0.9, spec=0.05); edge = P("dirt2", (0.72, 0.52, 0.3), rough=0.9, spec=0.05)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    box("road_pad_edge", (x1 - x0 + 0.6, y1 - y0 + 0.6, 0.05), (cx, cy, -0.005), edge, bevel=0.02)
    box("road_pad", (x1 - x0, y1 - y0, 0.05), (cx, cy, 0.006), top, bevel=0.02)


def world(river_x=12.0, river_w=4.8, road_w=4.6):
    """Green toy land: a road along X, a river along Y with a missing bridge, hangars to the west."""
    g = mat("ground", (0.3, 0.72, 0.2), rough=0.85, spec=0.1)
    x0, x1 = river_x - river_w / 2, river_x + river_w / 2
    box("ground_w", (140, 240, 2), (x0 - 70, 0, -1), g, bevel=0.25)
    box("ground_e", (140, 240, 2), (x1 + 70, 0, -1), g, bevel=0.25)
    box("riverbed", (river_w + 2, 240, 0.2), (river_x, 0, -1.2), P("sand", (0.95, 0.83, 0.55), rough=0.8), bevel=0)
    box("deco_water", (river_w + 1, 240, 0.1), (river_x, 0, -0.5), mat("water", (0.05, 0.6, 1.0), rough=0.08, spec=0.9, emit=0.15), bevel=0)
    for s, xx in ((-1, x0), (1, x1)):
        box("deco_bank", (0.5, 240, 0.9), (xx + s * 0.2, 0, -0.42), P("sand", (0.95, 0.83, 0.55), rough=0.8), bevel=0.2, rot=(0, s * math.radians(-18), 0))
    rd = mat("road", (0.22, 0.22, 0.26), rough=0.7, spec=0.2)
    ed = P("cream", COL["cream"], rough=0.6)
    for a, b in ((-110, x0 + 0.05), (x1 - 0.05, 128)):
        box("road", (b - a, road_w + 0.6, 0.06), ((a + b) / 2, 0, 0.0), ed, bevel=0.02)
        box("road_top", (b - a, road_w, 0.06), ((a + b) / 2, 0, 0.012), rd, bevel=0.02)
        n = int((b - a) / 3)
        for k in range(n):
            box("dash", (1.1, 0.14, 0.02), (a + 1.5 + k * 3, 0, 0.045), P("white", COL["white"]), bevel=0)
    # broken bridge stubs
    for xx in (x0 - 0.15, x1 + 0.15):
        for s in (-1, 1):
            cyl("post", 0.2, 1.0, (xx, s * (road_w / 2 + 0.35), 0.5), P("red", COL["red"]), verts=16, bevel=0.05)
            sphere("postcap", 0.26, (xx, s * (road_w / 2 + 0.35), 1.05), P("white", COL["white"]))
    # hills far away
    r = random.Random(4)
    for k in range(26):
        a = -95 + k * 9.5
        s = r.uniform(9, 16)
        sphere("hill", s, (a, r.uniform(34, 50), -s * 0.45), mat("hill%d" % (k % 2), [(0.3, 0.74, 0.2), (0.42, 0.84, 0.26)][k % 2], rough=0.9, spec=0.05),
               scale=(1.6, 1, 0.75), segs=28, rings=14)
    for k, (x, y, z, s) in enumerate(((-18, 30, 13, 1.6), (4, 38, 16, 2.0), (24, 30, 12, 1.4), (-40, 36, 15, 1.8), (40, 40, 17, 2.0), (58, 32, 13, 1.5), (78, 38, 16, 1.9), (98, 31, 13, 1.5), (-62, 32, 14, 1.6))):
        cloud(x, y, z, s)


def bridge_deck(L=5.6, W=3.0):
    """Wooden bridge deck (origin: middle, top surface at z = 0)."""
    root = empty("bridge")
    for s in (-1, 1):
        box("beam", (L, 0.3, 0.26), (0, s * (W / 2 - 0.4), -0.2), P("wood2", COL["wood2"], rough=0.6), root, bevel=0.06)
    n = 12
    for k in range(n):
        box("plank", (L / n - 0.04, W, 0.1), (-L / 2 + (k + 0.5) * L / n, 0, -0.05), P("wood" + str(k % 2), COL["wood"] if k % 2 else (0.98, 0.74, 0.4), rough=0.6), root, bevel=0.035)
    for s in (-1, 1):
        box("kerb", (L - 1.0, 0.16, 0.16), (0, s * (W / 2 - 0.08), 0.08), P("red", COL["red"]), root, bevel=0.06)
    cyl("eye", 0.14, 0.08, (0, 0, 0.03), P("gray", COL["gray"]), root, bevel=0.02)
    return root


# ---------------------------------------------------------------- more helpers for the long video

def path_len(t, pts):
    path = _spline([t.last[:2]] + list(pts))
    return sum((b - a).length for a, b in zip(path, path[1:]))


def go(t, f0, pts, speed=5.0, reverse=False, lean=1.0):
    """Drive through pts starting at f0 at about `speed` metres per second. Returns the arrival frame."""
    n = max(12, int(round(path_len(t, pts) / speed * lib.FPS / 0.75)))
    return drive_path(t, f0, f0 + n, pts, reverse=reverse, lean=lean)


STOW = (0.0, 16.0, 1.2, True)


def crane_job(t, f0, src, src_z, dst, dst_z, lift=2.2, pace=1.0):
    """Keys for: aim at src, lower the hook, lift, swing to dst, lower, release, stow. The crane must be parked.
    Returns (attach frame, touch-down frame, end frame)."""
    d = [int(x * pace) for x in (34, 20, 26, 54, 38, 12, 40)]
    y0, p0, c0 = crane_aim(t, f0, src, src_z)
    y1, p1, c1 = crane_aim(t, f0, dst, dst_z)
    fa = f0 + d[0] + d[1]; fl = fa + d[2]; fs = fl + d[3]; fd = fs + d[4]; fr = fd + d[5]; fe = fr + d[6]
    crane_keys(t, [(f0,) + STOW, (f0 + d[0], y0, p0, 1.6), (fa, y0, p0, c0), (fl, y0, min(80, p0 + 5), c0 - lift),
                   (fs, y1, p1, max(1.0, c1 - lift - 1.5)), (fd, y1, p1, c1), (fr, y1, p1, c1), (fe,) + STOW])
    return fa, fd, fe


def hang_bake(t, obj, N, jobs, before, dz=0.05, sway=0.05):
    """obj rides on the hook between each (attach, down, after_loc, after_rotz) in jobs; before(f) -> (loc, rotz)."""
    frames = list(range(N + 1)); L, R = [], []
    jobs = sorted(jobs)
    for f in frames:
        cur = None; done = None
        for j in jobs:
            if j[0] <= f <= j[1]:
                cur = j
            if f > j[1]:
                done = j
        if cur:
            hk = crane_tip(t, f)[1]
            prev = [j for j in jobs if j[1] < cur[0]]
            r0 = prev[-1][3] if prev else before(cur[0])[1]
            u = (f - cur[0]) / max(1, cur[1] - cur[0]); u = u * u * (3 - 2 * u)
            sw = sway * math.sin((f - cur[0]) * 0.33) * max(0.0, min(1.0, (f - cur[0]) / 12, (cur[1] - f) / 14))
            L.append((hk.x, hk.y, hk.z - dz)); R.append((sw * 0.5, sw, r0 + (cur[3] - r0) * u))
        elif done:
            if callable(done[2]):
                p, r = done[2](f); L.append(tuple(p)); R.append((0, 0, r))
            else:
                L.append(tuple(done[2])); R.append((0, 0, done[3]))
        else:
            p, r = before(f); L.append(tuple(p)); R.append((0, 0, r))
    bake(obj, "location", frames, L); bake(obj, "rotation_euler", frames, R)


def split(ob, name, test, origin, parent):
    """Cut the faces whose vertices all pass test(co) out of ob into a new object with the given origin."""
    import bmesh
    me = ob.data
    bpy.context.view_layer.objects.active = ob
    for o in bpy.context.selected_objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="DESELECT"); bpy.ops.object.mode_set(mode="OBJECT")
    ok = [test(v.co) for v in me.vertices]
    for p in me.polygons:
        p.select = all(ok[i] for i in p.vertices)
    before = set(bpy.data.objects)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.separate(type="SELECTED"); bpy.ops.object.mode_set(mode="OBJECT")
    new = (set(bpy.data.objects) - before).pop()
    from mathutils import Matrix
    new.data.transform(Matrix.Translation(-Vector(origin)))
    new.parent = parent; new.location = origin; new.name = name
    return new


def dump_gear(t):
    """Make the dump truck's bucket tip around its rear hinge; a sand load can lie in it."""
    body = next(o for o in t.body.children if o.type == "MESH" and "_body" in o.name)
    t.bucket = split(body, t.name + "_bucket", lambda c: (c.z > 1.5 and c.x < 1.02) or (c.z > 3.33 and c.x < 2.15), (-2.1, 0, 1.45), t.body)
    t.sand = sphere(t.name + "_sand", 1.0, (1.1, 0, 0.95), P("sandpile", (0.98, 0.8, 0.42), rough=0.85, spec=0.1), t.bucket, scale=(1.75, 1.0, 0.75), segs=32, rings=16)
    t.sand.scale = (0.001, 0.001, 0.001)
    return t


def tip(t, f0, f1, deg=48, hold=40):
    """Raise the bucket (f0..f1), hold, lower again. Returns the end frame."""
    a = -math.radians(deg)
    lib.keys(t.bucket, "rotation_euler", [(f0, (0, 0, 0)), (f1, (0, a, 0)), (f1 + hold, (0, a, 0)), (f1 + hold + (f1 - f0), (0, 0, 0))])
    return f1 + hold + (f1 - f0)


def spin_wheels(t, f0, f1, speed=9.0, which=None):
    """Wheels spinning on the spot (stuck in the mud)."""
    frames = list(range(f0, f1 + 1)); d0 = t.dist; vals = []
    for f in frames:
        e = min(1.0, (f - f0) / 8, (f1 - f) / 8)
        t.dist += speed * max(0.0, e) / lib.FPS
        vals.append((0, t.dist / t.r, 0))
    for w in (which if which is not None else t.wheels):
        bake(w, "rotation_euler", frames, vals)


def rope(name, pa, pb, f0, f1, r=0.035):
    """A taut rope between two moving points pa(f), pb(f) (visible only between f0 and f1)."""
    root = empty(name)
    cyl("rp", r, 1.0, (0, 0, 0.5), P("rope", (0.95, 0.85, 0.3), rough=0.7), root, verts=8)
    frames = list(range(f0, f1 + 1)); L, R, S = [], [], []
    for f in frames:
        a, b = Vector(pa(f)), Vector(pb(f)); d = b - a
        L.append(tuple(a)); S.append((1, 1, max(0.01, d.length)))
        R.append(tuple(d.to_track_quat("Z", "Y").to_euler()))
    bake(root, "location", frames, L); bake(root, "rotation_euler", frames, R); bake(root, "scale", frames, S)
    lib.keys(root, "scale", [(f0 - 1, (0, 0, 0))]) if f0 > 0 else None
    lib.key(root, "scale", f1 + 1, (0, 0, 0))
    return root


def body_keys(t, seq):
    """seq: (frame, dz, pitch_deg, roll_deg) for the sprung body (sinking, leaning)."""
    lib.keys(t.body, "location", [(f, (0, 0, dz)) for f, dz, p, r in seq])
    lib.keys(t.body, "rotation_euler", [(f, (math.radians(r), math.radians(p), 0)) for f, dz, p, r in seq])


def beacon(t, loc, f0, f1, col=(1.0, 0.45, 0.0)):
    """A flashing light glow on a vehicle."""
    m = mat(t.name + "_beacon", col, rough=0.2, emit=0.0, unique=True)
    sphere("beacon", 0.2, loc, m, t.body, scale=(1, 1, 0.75))
    lib.flash(m, f0, f1, period=10, on=6.0, off=0.2)


def place(t, f, x, y, heading):
    """Jump to a new spot at frame f (use at a camera cut)."""
    h = math.radians(heading)
    px, py, ph = t.pose(f - 1)
    for k in [k for k in t.track if k > f]:                      # an earlier drive must not reach past the jump
        del t.track[k]
    ad = t.root.animation_data
    for fc in (ad.action.fcurves if ad and ad.action else ()):
        for kp in [kp for kp in fc.keyframe_points if kp.co.x > f]:
            fc.keyframe_points.remove(kp)
    bake(t.root, "location", [f - 1, f], [(px, py, 0), (x, y, 0)])
    bake(t.root, "rotation_euler", [f - 1, f], [(0, 0, ph), (0, 0, h)])
    t.track[f - 1] = (px, py, ph); t.track[f] = (x, y, h)
    t.last = (x, y, h)


def burst(center, f0, n=14, col=(0.4, 0.25, 0.12), r=0.12, spread=1.6, height=1.4, dur=16, seed=1, name="blob"):
    """Little blobs thrown up from a point (mud splashes, sand)."""
    rnd = random.Random(seed)
    m = P(name, col, rough=0.7, spec=0.2)
    for i in range(n):
        o = sphere(name, r * rnd.uniform(0.6, 1.3), center, m, segs=10, rings=6)
        a = rnd.uniform(0, 2 * math.pi); d = rnd.uniform(0.4, 1.0) * spread; h = rnd.uniform(0.5, 1.0) * height
        fs = f0 + rnd.randint(0, 5)
        frames = list(range(fs, fs + dur + 1)); L = []
        for f in frames:
            u = (f - fs) / dur
            L.append((center[0] + math.cos(a) * d * u, center[1] + math.sin(a) * d * u, center[2] + 4 * h * u * (1 - u)))
        bake(o, "location", frames, L)
        lib.keys(o, "scale", [(fs - 1, (0, 0, 0)), (fs, (1, 1, 1)), (fs + dur - 2, (1, 1, 1)), (fs + dur, (0, 0, 0))])


def ball(r=0.42):
    root = empty("ball")
    sphere("ballb", r, (0, 0, 0), P("ball_y", (1.0, 0.8, 0.05)), root, segs=24, rings=14)
    lib.torus("band", r * 0.98, r * 0.16, (0, 0, 0), P("ball_b", (0.1, 0.4, 1.0)), root)
    lib.torus("band2", r * 0.98, r * 0.16, (0, 0, 0), P("ball_r", (0.95, 0.1, 0.1)), root, rot=(0, R90, 0))
    root.location.z = r
    root["r"] = r
    return root


def roll(b, pts, hop=0.0):
    """pts: (frame, x, y) list; the ball rolls between them (slows down at the end of each leg)."""
    r = b["r"]; ang = 0.0
    for (f0, x0, y0), (f1, x1, y1) in zip(pts, pts[1:]):
        frames = list(range(f0, f1 + 1)); L, R = [], []
        d = math.hypot(x1 - x0, y1 - y0); th = math.atan2(y1 - y0, x1 - x0)
        for f in frames:
            u = (f - f0) / max(1, f1 - f0); e = 1 - (1 - u) ** 2
            z = r + hop * abs(math.sin(u * math.pi * 3)) * (1 - u)
            L.append((x0 + (x1 - x0) * e, y0 + (y1 - y0) * e, z))
            R.append((-math.sin(th) * (ang + d * e / r), math.cos(th) * (ang + d * e / r), 0))
        ang += d / r
        bake(b, "location", frames, L); bake(b, "rotation_euler", frames, R)


def overlaps(N, margin=0.25):
    """Frames where the footprints (length x width boxes, grown by margin) of two vehicles intersect.
    Returns [(name_a, name_b, first_frame, last_frame, deepest overlap in m)]."""
    def box(t, f):
        x, y, h = t.pose(f)
        return x, y, math.cos(h), math.sin(h), t.meta["length"] / 2 + margin / 2, t.meta["width"] / 2 + margin / 2

    def depth(a, b):
        d = (b[0] - a[0], b[1] - a[1])
        best = 1e9
        for ux, uy in ((a[2], a[3]), (-a[3], a[2]), (b[2], b[3]), (-b[3], b[2])):
            ra = a[4] * abs(ux * a[2] + uy * a[3]) + a[5] * abs(-ux * a[3] + uy * a[2])
            rb = b[4] * abs(ux * b[2] + uy * b[3]) + b[5] * abs(-ux * b[3] + uy * b[2])
            best = min(best, ra + rb - abs(d[0] * ux + d[1] * uy))
            if best <= 0:
                return 0.0
        return best

    ts = [t for t in ALL if hasattr(t, "meta")]
    out = []
    for i, a in enumerate(ts):
        for b in ts[i + 1:]:
            run = None
            for f in range(1, N + 2):
                dp = depth(box(a, f), box(b, f)) if f <= N else 0.0
                if dp > 0:
                    run = [f, f, dp] if run is None else [run[0], f, max(run[2], dp)]
                elif run:
                    out.append((a.name, b.name, run[0], run[1], round(run[2], 2))); run = None
    return out
