"""Shared set-up for the 'Minik Ustalar' toy-vehicle video: world, base with five hangars, the five vehicles, cameras."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import lib, toys as T
from lib import camera, cut, sfx, bake

RX = 12.0
LO = "--lo" in sys.argv
DRY = "--dry" in sys.argv
SURF = []
SCATTER = []
HX = dict(car=-44.0, tow=-37.0, dump=-30.0, crane=-23.0, flat=-16.0)
HY = dict(car=11.0, tow=11.5, dump=13.5, crane=16.0, flat=14.0)
HCOL = dict(car=T.COL["red"], tow=T.COL["purple"], dump=T.COL["yellow"], crane=T.COL["orange"], flat=T.COL["blue"])


def setup(N, bridge=True, clear=(), pads=(), dirt=()):
    """clear: (x0, x1, y0, y1) boxes kept free of scenery (camera positions, work sites).
    pads / dirt: paved / dirt areas beside the road where the vehicles may drive and park."""
    import scenery as SC
    lib.DOF_FSTOP = 16
    s = lib.reset(N, res=(640, 360) if LO else (1280, 720), samples=3 if LO else 6)
    lib.world(top=(0.1, 0.45, 1.0), horizon=(0.7, 0.9, 1.0), light=0.75)
    lib.sun(energy=3.0, rot=(math.radians(52), 0, math.radians(-35)), angle=14)
    s.eevee.use_soft_shadows = True
    s.eevee.shadow_cascade_size = "1024"
    s.eevee.use_gtao = False
    T.world(RX, road_w=4.6)
    SURF[:] = [(-110, 128, -2.3, 2.3)] + list(pads) + list(dirt) + [(x - 2.3, x + 2.3, 0, 20) for x in HX.values()]
    for q in pads:
        T.pad(*q)
    for q in dirt:
        T.pad(*q, kind="dirt")
    if DRY:
        deck = T.bridge_deck(L=5.6, W=3.8); deck.location = (RX, 0, 0.03) if bridge else (0, 0, -30)
        return s, deck
    SC.countryside(N)
    hard = [(a - 1.5, b + 1.5, c - 1.5, d + 1.5) for a, b, c, d in list(pads) + list(dirt)]
    hard += [(-49, -11, 0, 24), (RX - 4.5, RX + 4.5, -200, 200), (-200, 200, -3.0, 3.0)]
    small = [q for q in clear if (q[1] - q[0]) * (q[3] - q[2]) < 300]       # work sites: nothing at all
    big = [q for q in clear if q not in small]                              # camera country: only low things

    def inside(qs, x, y, m):
        return any(a - m <= x <= b + m and c - m <= y <= d + m for a, b, c, d in qs)

    def free(x, y, m=0.0, low=False):
        if inside(hard + small, x, y, m) or (not low and inside(big, x, y, m)):
            return False
        return all((x - fx) ** 2 + (y - fy) ** 2 > (fr + m) ** 2 for fx, fy, fr in SC.FEATURES)

    SC.OK = lambda x, y, m=0.0: not inside(hard + small + big, x, y, m)
    SC.life(N)
    before = set(bpy.data.objects)
    r = random.Random(7)
    k = 0
    for i in range(420):
        x = r.uniform(-100, 128); y = r.choice((-1, 1)) * r.uniform(9, 30)
        if y < 0:
            y = -r.uniform(5, 50)
        if not free(x, y, 1.6):
            continue
        T.tree(x, y, r.uniform(1.0, 1.5), k); k += 1
    r = random.Random(11)
    for i in range(2600):
        x = r.uniform(-100, 128); y = r.uniform(-34, 27)
        if not free(x, y, 0.3, low=True):
            continue
        kind = r.random()
        if kind < 0.78:
            SC.flower(x, y, i)
        elif kind < 0.92:
            SC.bush(x, y, r.uniform(0.7, 1.1)) if free(x, y, 1.2) else SC.bush(x, y, r.uniform(0.35, 0.5))
        else:
            SC.rock(x, y, r.uniform(0.6, 1.1))
    SCATTER[:] = [o.name for o in set(bpy.data.objects) - before]
    for n, x in HX.items():
        T.hangar(x, 9.0, HCOL[n], w=5.6, d=12.5, h=5.6)
        lib.box("apron", (4.6, 9.4, 0.06), (x, 4.5, 0.0), lib.mat("road", (0.22, 0.22, 0.26)), bevel=0.02)
    deck = T.bridge_deck(L=5.6, W=3.8)
    deck.location = (RX, 0, 0.03) if bridge else (0, 0, -30)
    return s, deck


def fleet(where=None):
    """Load the five vehicles. where: name -> (x, y, heading deg); default = at home in the hangars."""
    where = where or {}
    V = {}
    for n in ("car", "tow", "dump", "crane", "flat"):
        x, y, h = where.get(n, (HX[n], HY[n], -90))
        V[n] = T.load_toy(n, n, loc=(x, y), heading=h)
    car = V["car"]
    for sd in (-1, 1):
        lib.sphere("farlamp", 0.13, (1.21, sd * 0.42, 0.66), T.P("lamp", (1.0, 0.95, 0.7), rough=0.1, emit=1.2), car.body, scale=(0.45, 1, 1))
        lib.sphere("farring", 0.16, (1.19, sd * 0.42, 0.66), T.P("white", T.COL["white"]), car.body, scale=(0.35, 1, 1))
    T.crane_gear(V["crane"], -1.3, 1.25, boom=8.4)
    T.crane_keys(V["crane"], [(0,) + T.STOW])
    V["flat"].bed_z, V["flat"].bed_x = 1.8, -1.3
    T.dump_gear(V["dump"])
    V["tow"].hook = (-1.72, 0, 1.5)
    return V


def exit_pts(n):
    """Way out of the hangar onto the road, heading east."""
    x = HX[n]
    return [(x, 4.5), (x + 5.0, 0.2), (x + 9.0, 0)]


class Cams:
    def __init__(self):
        self.n = 0

    def shot(self, f0, f1, p0, t0, p1=None, t1=None, lens=35):
        self.n += 1
        c = camera("cam%02d" % self.n, [(f0, p0, t0), (f1, p1 or p0, t1 or t0)], lens)
        cut(f0, c)
        return c

    def follow(self, f0, f1, toy, off, look=(0, 0, 0.8), lens=35, smooth=14):
        self.n += 1
        name = "cam%02d" % self.n
        xs = [toy.pose(f) for f in range(f0, f1 + 1)]
        ks = []
        for k, f in enumerate(range(f0, f1 + 1)):
            w = xs[max(0, k - smooth):k + smooth + 1]
            x = sum(p[0] for p in w) / len(w); y = sum(p[1] for p in w) / len(w)
            ks.append((f, (x + off[0], y + off[1], off[2]), (x + look[0], y + look[1], look[2])))
        c = camera(name, ks[:1], lens)
        tgt = bpy.data.objects[name + "_tgt"]
        bake(c, "location", [k[0] for k in ks], [k[1] for k in ks])
        bake(tgt, "location", [k[0] for k in ks], [k[2] for k in ks])
        cut(f0, c)
        return c


def party(center, f, big=True):
    lib.confetti(center, f, n=70 if big else 40, spread=5.0, height=5.0)
    lib.stars_burst((center[0], center[1], center[2] - 0.8), f, n=8, radius=2.4)
    sfx(f, "yay"); sfx(f + 14, "tada")


def tidy():
    """Take the scattered flowers / bushes / rocks / trees away from right in front of the cameras, then join what is
    left into a few meshes (thousands of tiny objects render slowly)."""
    sc = bpy.context.scene
    cams = [o for o in bpy.data.objects if o.type == "CAMERA"]
    pts = set()
    for f in range(1, sc.frame_end + 1, 6):
        sc.frame_set(f)
        c = sc.camera
        if c:
            p = c.matrix_world.translation
            pts.add((round(p.x, 0), round(p.y, 0)))
    sc.frame_set(1)
    objs = [bpy.data.objects[n] for n in SCATTER if n in bpy.data.objects]
    gone = 0
    def near(o, d):
        x, y = o.matrix_world.translation.x, o.matrix_world.translation.y
        return any((x - a) ** 2 + (y - b) ** 2 < d * d for a, b in pts)
    kill = set()
    for o in objs:
        if o.parent is None and near(o, 5.5 if o.type == "EMPTY" else 3.5):
            kill.add(o.name); kill.update(ch.name for ch in o.children_recursive); gone += 1
    for n in kill:
        bpy.data.objects.remove(bpy.data.objects[n])
    objs = [bpy.data.objects[n] for n in SCATTER if n in bpy.data.objects]
    ms = [o for o in objs if o.type == "MESH"]
    empties = [o.name for o in objs if o.type == "EMPTY"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in ms:
        if o.parent:
            mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
        o.select_set(True)
    if ms:
        bpy.context.view_layer.objects.active = ms[0]
        bpy.ops.object.join()
        ms[0].name = "scatter"
    nm = len(ms)
    for n in empties:
        bpy.data.objects.remove(bpy.data.objects[n])
    print("TIDY removed", gone, "joined", nm)


def done(seg):
    hits = T.overlaps(bpy.context.scene.frame_end)
    for h in hits:
        print("OVERLAP", seg, *h)
    print("OVERLAPS", seg, len(hits))
    for t in T.ALL:                                               # nobody drives on the grass
        run = None
        for f in range(1, bpy.context.scene.frame_end + 2):
            x, y, _ = t.pose(f)
            off = f <= bpy.context.scene.frame_end and not any(a - 0.7 <= x <= b + 0.7 and c - 0.7 <= y <= d + 0.7 for a, b, c, d in SURF)
            if off:
                run = [f, f, x, y] if run is None else [run[0], f, run[2], run[3]]
            elif run:
                print("OFFROAD", seg, t.name, run[0], run[1], round(run[2], 1), round(run[3], 1)); run = None
    if DRY:
        return
    tidy()
    lib.render(seg)
    print("BUILT", seg)
