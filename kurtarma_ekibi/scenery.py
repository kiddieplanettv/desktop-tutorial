"""Toy countryside for the 'Minik Ustalar' videos: houses, barn, silo, windmills, farm animals, fences, haystacks,
flowers, bushes, rocks, lamp posts, mountains. Everything is built from simple rounded shapes (plastic toy look)."""
import bpy, math, random
import lib
from lib import box, cyl, sphere, empty, cone
from toys import P, COL, R90, cloud as T_cloud

FEATURES = []        # (x, y, radius): places that trees and flowers must keep away from


def _root(name, x, y, rot=0.0, r=3.0):
    o = empty(name, (x, y, 0))
    o.rotation_euler.z = math.radians(rot)
    FEATURES.append((x, y, r))
    return o


def _cycle(o, path):
    for fc in o.animation_data.action.fcurves:
        if fc.data_path == path:
            fc.modifiers.new("CYCLES")


def house(x, y, rot=-90, wall=COL["cream"], roof=COL["red"], w=4.2, d=3.6, h=2.6):
    """Cottage; the door looks along local +X."""
    o = _root("house", x, y, rot, 3.6)
    box("wall", (d, w, h), (0, 0, h / 2), P("wall%s" % (wall,), wall, rough=0.55), o, bevel=0.2, segs=4)
    r = cone("roof", 1.0, 1.9, (0, 0, h + 0.9), P("roof%s" % (roof,), roof, rough=0.5), o, verts=4, rot=(0, 0, math.radians(45)))
    r.scale = (d * 0.86, w * 0.86, 1)
    box("door", (0.12, 0.9, 1.5), (d / 2, 0, 0.75), P("door", COL["blue"]), o, bevel=0.06)
    sphere("knob", 0.07, (d / 2 + 0.08, 0.28, 0.75), P("lamp", (1.0, 0.95, 0.7), emit=0.6), o)
    for s in (-1, 1):
        box("win", (0.1, 0.8, 0.8), (d / 2, s * 1.35, 1.55), P("glass", COL["glass"], rough=0.08, spec=0.9), o, bevel=0.06)
        box("winf", (0.06, 0.96, 0.96), (d / 2 - 0.02, s * 1.35, 1.55), P("white", COL["white"]), o, bevel=0.05)
    box("chim", (0.5, 0.5, 1.2), (-d * 0.2, w * 0.22, h + 1.3), P("wall%s" % (wall,), wall, rough=0.55), o, bevel=0.08)
    return o


def barn(x, y, rot=-90):
    o = _root("barn", x, y, rot, 4.6)
    red = P("barn", (0.85, 0.12, 0.1), rough=0.5); wh = P("white", COL["white"])
    box("wall", (5.0, 6.0, 3.4), (0, 0, 1.7), red, o, bevel=0.2, segs=4)
    r = cyl("roof", 3.25, 5.3, (0, 0, 3.3), P("barnroof", (0.5, 0.52, 0.58), rough=0.5), o, rot=(0, R90, 0), verts=24)
    r.scale = (0.55, 1, 1)
    box("door", (0.12, 2.6, 2.6), (2.5, 0, 1.3), P("barndoor", (0.62, 0.08, 0.07)), o, bevel=0.06)
    for a in (0.6, -0.6):
        box("x", (0.1, 0.16, 3.3), (2.56, 0, 1.3), wh, o, bevel=0.03, rot=(a + (0 if a > 0 else 0), 0, 0))
    box("trim", (0.1, 2.9, 0.18), (2.56, 0, 2.62), wh, o, bevel=0.04)
    box("loft", (0.1, 0.9, 0.7), (2.52, 0, 3.6), wh, o, bevel=0.06)
    return o


def silo(x, y):
    o = _root("silo", x, y, 0, 2.0)
    cyl("body", 1.3, 5.0, (0, 0, 2.5), P("silo", (0.82, 0.86, 0.9), rough=0.35), o, verts=28)
    sphere("dome", 1.3, (0, 0, 5.0), P("silodome", (0.85, 0.2, 0.15)), o, scale=(1, 1, 0.6), segs=28, rings=12)
    for z in (1.2, 2.5, 3.8):
        cyl("band", 1.33, 0.12, (0, 0, z), P("gray", COL["gray"]), o, verts=28)
    return o


def windmill(x, y, rot=-90, N=2400, speed=0.16):
    """Tower with four turning sails (they face local +X)."""
    o = _root("mill", x, y, rot, 3.6)
    cyl("tower", 1.7, 6.0, (0, 0, 3.0), P("cream", COL["cream"], rough=0.55), o, verts=28, r2=1.05)
    cone("cap", 1.35, 1.6, (0, 0, 6.8), P("millroof", COL["orange"]), o, verts=28)
    box("door", (0.12, 0.9, 1.5), (1.62, 0, 0.75), P("door", COL["blue"]), o, bevel=0.06)
    box("win", (0.1, 0.7, 0.7), (1.33, 0, 3.4), P("glass", COL["glass"], rough=0.08, spec=0.9), o, bevel=0.06)
    hub = empty("millhub", (1.35, 0, 5.6), o)
    cyl("axle", 0.22, 0.7, (0, 0, 0), P("gray", COL["gray"]), hub, rot=(0, R90, 0), verts=14)
    for k in range(4):
        a = k * math.pi / 2
        box("arm", (0.14, 0.2, 3.6), (0.3, -math.sin(a) * 1.8, math.cos(a) * 1.8), P("wood2", COL["wood2"]), hub, bevel=0.04, rot=(a, 0, 0))
        box("sail", (0.08, 1.0, 2.4), (0.3, -math.sin(a) * 2.1 + math.cos(a) * 0.55, math.cos(a) * 2.1 + math.sin(a) * 0.55),
            P("white", COL["white"]), hub, bevel=0.04, rot=(a, 0, 0))
    lib.keys(hub, "rotation_euler", [(0, (0, 0, 0)), (N, (2 * math.pi * speed * N / lib.FPS, 0, 0))], interp="LINEAR")
    return o


def _legs(o, m, xs, ys, r, h):
    for x in xs:
        for y in ys:
            cyl("leg", r, h, (x, y, h / 2), m, o, verts=12, bevel=0.03)


def cow(x, y, rot=0.0, phase=0.0):
    o = _root("cow", x, y, rot, 1.6)
    wh = P("cowwhite", (0.97, 0.97, 0.95)); bl = P("cowblack", (0.08, 0.08, 0.09)); pk = P("cowpink", (1.0, 0.62, 0.68))
    box("body", (1.9, 0.95, 0.95), (0, 0, 1.05), wh, o, bevel=0.36, segs=5)
    for px, py, pz, sx in ((0.35, 0.44, 1.2, 0.5), (-0.5, -0.44, 1.05, 0.55), (-0.2, 0.2, 1.5, 0.45)):
        sphere("patch", sx, (px, py, pz), bl, o, scale=(1, 0.2 if abs(py) > 0.3 else 0.9, 0.75 if abs(py) > 0.3 else 0.12))
    _legs(o, wh, (0.62, -0.62), (0.28, -0.28), 0.15, 0.66)
    hd = empty("cowhead", (1.0, 0, 1.45), o)
    box("head", (0.7, 0.62, 0.62), (0.25, 0, 0), wh, hd, bevel=0.22, segs=4)
    box("snout", (0.3, 0.52, 0.36), (0.6, 0, -0.1), pk, hd, bevel=0.13)
    for s in (-1, 1):
        sphere("eye", 0.06, (0.52, s * 0.2, 0.12), bl, hd)
        sphere("ear", 0.16, (0.1, s * 0.4, 0.18), bl, hd, scale=(0.6, 1.2, 0.5))
        cone("horn", 0.07, 0.24, (0.12, s * 0.2, 0.42), P("cream", COL["cream"]), hd, verts=10)
    cyl("tail", 0.04, 0.8, (-1.0, 0, 0.95), bl, o, verts=8, rot=(0, 0.35, 0))
    lib.keys(hd, "rotation_euler", [(0, (0, 0, 0)), (40, (0, 0.35, 0)), (95, (0, 0.3, 0.12)), (130, (0, 0, 0)), (200, (0, 0, -0.2)), (260, (0, 0, 0))])
    _cycle(hd, "rotation_euler")
    for fc in hd.animation_data.action.fcurves:
        for kp in fc.keyframe_points:
            kp.co[0] += phase
    return o


def sheep(x, y, rot=0.0, phase=0.0):
    o = _root("sheep", x, y, rot, 1.2)
    wool = P("wool", (0.98, 0.98, 0.96), rough=0.9, spec=0.05); bl = P("cowblack", (0.08, 0.08, 0.09))
    rnd = random.Random(int(x * 7 + y * 13))
    sphere("body", 0.55, (0, 0, 0.78), wool, o, scale=(1.3, 1, 0.95))
    for k in range(9):
        a = rnd.uniform(0, 2 * math.pi); u = rnd.uniform(-0.55, 0.55)
        sphere("puff", 0.24, (u, math.cos(a) * 0.42, 0.8 + math.sin(a) * 0.36), wool, o, segs=12, rings=8)
    _legs(o, bl, (0.36, -0.36), (0.2, -0.2), 0.08, 0.5)
    hd = empty("sheephead", (0.72, 0, 0.98), o)
    sphere("head", 0.26, (0.08, 0, 0), bl, hd, scale=(1.15, 0.9, 0.95))
    sphere("top", 0.2, (-0.02, 0, 0.2), wool, hd, segs=12, rings=8)
    for s in (-1, 1):
        sphere("ear", 0.1, (0.0, s * 0.26, 0.04), bl, hd, scale=(0.6, 1.4, 0.5))
        sphere("eye", 0.045, (0.3, s * 0.11, 0.06), P("white", COL["white"]), hd)
    lib.keys(o, "location", [(0, (x, y, 0)), (70 + phase, (x, y, 0)), (76 + phase, (x, y, 0.16)), (82 + phase, (x, y, 0)), (150, (x, y, 0))])
    _cycle(o, "location")
    return o


def duck(x, y, rot=0.0, z=0.0, phase=0.0):
    o = _root("duck", x, y, rot, 0.6)
    ye = P("duck", (1.0, 0.82, 0.08)); og = P("duckbeak", COL["orange"])
    sphere("body", 0.3, (0, 0, 0.3), ye, o, scale=(1.3, 1, 0.9))
    sphere("tail", 0.14, (-0.36, 0, 0.42), ye, o, scale=(1, 0.8, 0.8))
    sphere("head", 0.2, (0.26, 0, 0.66), ye, o)
    box("beak", (0.2, 0.18, 0.07), (0.46, 0, 0.63), og, o, bevel=0.03)
    for s in (-1, 1):
        sphere("eye", 0.035, (0.38, s * 0.11, 0.72), P("cowblack", (0.08, 0.08, 0.09)), o)
    lib.keys(o, "location", [(0 + phase, (x, y, z)), (36 + phase, (x, y, z + 0.05)), (72 + phase, (x, y, z))])
    lib.keys(o, "rotation_euler", [(0 + phase, (0.05, 0, math.radians(rot))), (36 + phase, (-0.05, 0, math.radians(rot))), (72 + phase, (0.05, 0, math.radians(rot)))])
    _cycle(o, "location"); _cycle(o, "rotation_euler")
    return o


def fence(x0, y0, x1, y1, gap=1.4):
    wh = P("fence", (0.98, 0.95, 0.88), rough=0.6)
    L = math.hypot(x1 - x0, y1 - y0); a = math.atan2(y1 - y0, x1 - x0)
    n = max(1, int(round(L / gap)))
    for k in range(n + 1):
        u = k / n
        box("post", (0.16, 0.16, 0.95), (x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, 0.47), wh, bevel=0.05)
    for z in (0.38, 0.74):
        box("rail", (L, 0.07, 0.13), ((x0 + x1) / 2, (y0 + y1) / 2, z), wh, bevel=0.03, rot=(0, 0, a))


def paddock(x0, x1, y0, y1, gate=True):
    fence(x0, y1, x1, y1); fence(x0, y0, x0, y1); fence(x1, y0, x1, y1)
    if gate:
        fence(x0, y0, x0 + (x1 - x0) * 0.35, y0); fence(x1 - (x1 - x0) * 0.35, y0, x1, y0)
    else:
        fence(x0, y0, x1, y0)
    FEATURES.append(((x0 + x1) / 2, (y0 + y1) / 2, max(x1 - x0, y1 - y0) * 0.75))


def haystack(x, y, rot=0.0):
    o = _root("hay", x, y, rot, 1.4)
    cyl("hay", 0.8, 1.3, (0, 0, 0.8), P("hay", (0.98, 0.82, 0.3), rough=0.9, spec=0.05), o, rot=(R90, 0, 0), verts=22, bevel=0.08)
    for s in (-1, 1):
        cyl("hayend", 0.62, 0.04, (0, s * 0.66, 0.8), P("hay2", (0.9, 0.7, 0.22), rough=0.9, spec=0.05), o, rot=(R90, 0, 0), verts=22)


def bush(x, y, s=1.0):
    g = P("bush", (0.14, 0.62, 0.22), rough=0.6)
    for dx, dy, r in ((0, 0, 0.7), (0.6, 0.15, 0.5), (-0.55, -0.1, 0.55)):
        sphere("bush", r * s, (x + dx * s, y + dy * s, r * s * 0.7), g, segs=16, rings=10)


def rock(x, y, s=1.0):
    sphere("rock", 0.6 * s, (x, y, 0.2 * s), P("rock", (0.6, 0.62, 0.66), rough=0.8), scale=(1.2, 0.9, 0.65), segs=12, rings=8)


FLOWER_COLS = [(1.0, 0.3, 0.5), (1.0, 0.85, 0.1), (0.95, 0.95, 0.95), (0.6, 0.35, 1.0), (1.0, 0.45, 0.1)]


def flower(x, y, k=0):
    st = P("stem", (0.2, 0.7, 0.2))
    cyl("stem", 0.03, 0.4, (x, y, 0.2), st, verts=6)
    sphere("petal", 0.15, (x, y, 0.44), P("flower%d" % (k % 5), FLOWER_COLS[k % 5], rough=0.5), scale=(1, 1, 0.5), segs=10, rings=6)
    sphere("heart", 0.07, (x, y, 0.5), P("flowerc", (1.0, 0.75, 0.05)), segs=8, rings=5)


def lamp(x, y):
    cyl("lamppost", 0.09, 3.2, (x, y, 1.6), P("lamppost", (0.25, 0.3, 0.4)), verts=12)
    sphere("lampglobe", 0.3, (x, y, 3.35), P("lampglobe", (1.0, 0.97, 0.8), rough=0.2, emit=0.5), segs=14, rings=10)


def mountains():
    for k, (x, h, r) in enumerate(((-70, 26, 26), (-30, 34, 30), (12, 28, 27), (52, 36, 32), (95, 30, 28), (135, 26, 26))):
        cone("mount", r, h, (x, 96, h / 2 - 3), P("mount", (0.5, 0.66, 0.9), rough=0.9, spec=0.0), verts=28)
        cone("snow", r * 0.34, h * 0.32, (x, 96, h * 0.86 - 3), P("snow", (0.97, 0.98, 1.0), rough=0.8, emit=0.15), verts=28)


def countryside(N):
    """The same village and farms in every episode (north of the road, plus a far row to the south)."""
    FEATURES.clear()
    mountains()
    # west farm
    barn(-60, 15); silo(-66, 16); paddock(-58, -50, 9, 14)
    cow(-56, 11.5, 20); cow(-52.5, 12, 200, 60); haystack(-64, 10, 30)
    # village by the river
    house(-7, 13, -90, COL["cream"], COL["red"]); house(-1, 16, -90, (1.0, 0.8, 0.85), COL["blue"]); house(5.5, 12.5, -100, (0.85, 0.95, 1.0), COL["orange"])
    windmill(1, 25, -90, N)
    fence(-10, 9.6, 8.5, 9.6)
    lamp(-4, 8.7); lamp(7, 8.7); lamp(15.5, 8.7)
    for k, (dx, dz) in enumerate(((9.0, 0), (-12.5, 40), (15.5, 20), (-17.5, 10), (21, 55), (27, 30))):
        duck(12.0 + (0.9 if k % 2 else -0.8), dx, 90 if dx > 0 else -90, z=-0.52, phase=dz)
    # sheep meadow
    paddock(16.5, 24, 9.5, 15)
    for k, (sx, sy, sr) in enumerate(((18, 11.5, 30), (20.5, 13.5, 160), (22.5, 11, 250), (19.5, 14, -60))):
        sheep(sx, sy, sr, k * 17)
    house(29, 15, -90, (1.0, 0.92, 0.7), (0.3, 0.7, 0.3)); haystack(34.5, 12.5, 60); haystack(36.3, 13.2, 20)
    # middle farm
    barn(47, 17); silo(53, 18.5); paddock(41.5, 51, 9.5, 13.2)
    cow(44, 11.4, -10); cow(48.5, 11.2, 170, 90); house(56, 19, -90, COL["cream"], COL["purple"])
    windmill(75, 20, -90, N, speed=0.13)
    # east village
    house(82, 13.5, -90, (1.0, 0.8, 0.85), COL["red"]); house(88.5, 16, -90, COL["cream"], COL["blue"]); house(95, 13, -95, (0.85, 0.95, 1.0), (0.3, 0.7, 0.3))
    fence(79, 9.8, 98, 9.8); lamp(87, 8.9); lamp(97, 8.9); paddock(100, 108, 9.5, 14.5)
    sheep(102, 11.5, 40); sheep(105, 12.5, 200, 30); cow(104, 10.6, 90, 40)
    # far south row (behind the cameras most of the time)
    for k, x in enumerate((-66, -8, 6, 24, 72, 96, 110)):
        house(x, -31 - (k % 2) * 3, 90, [COL["cream"], (1.0, 0.8, 0.85), (0.85, 0.95, 1.0)][k % 3], [COL["red"], COL["blue"], COL["orange"]][k % 3])
    barn(34, -33, 90); silo(40, -34); windmill(-58, -30, 90, N)


# ----------------------------------------------------------------------------------------------------------------
# second layer: more life everywhere (ponds, fields, orchards, more animals, things in the sky)
# ----------------------------------------------------------------------------------------------------------------
OK = lambda x, y, m=0.0: True          # set by the episode: False where the vehicles work or a camera stands
BLACK = (0.08, 0.08, 0.09)


def pig(x, y, rot=0.0, phase=0.0):
    o = _root("pig", x, y, rot, 1.0)
    pk = P("pig", (1.0, 0.6, 0.68), rough=0.5); dk = P("pigdark", (0.95, 0.42, 0.52))
    sphere("body", 0.48, (0, 0, 0.56), pk, o, scale=(1.35, 1, 0.95))
    _legs(o, dk, (0.34, -0.34), (0.2, -0.2), 0.09, 0.3)
    hd = empty("pighead", (0.58, 0, 0.66), o)
    sphere("head", 0.3, (0.05, 0, 0), pk, hd)
    cyl("snout", 0.13, 0.12, (0.33, 0, -0.03), dk, hd, rot=(0, R90, 0), verts=14)
    for s in (-1, 1):
        sphere("eye", 0.04, (0.28, s * 0.13, 0.1), P("cowblack", BLACK), hd)
        cone("ear", 0.1, 0.16, (0.02, s * 0.2, 0.26), dk, hd, verts=8)
    sphere("tail", 0.07, (-0.66, 0, 0.7), dk, o)
    lib.keys(hd, "rotation_euler", [(phase, (0, 0, 0)), (30 + phase, (0, 0.4, 0)), (70 + phase, (0, 0.35, 0.15)), (100 + phase, (0, 0, 0)), (180 + phase, (0, 0, 0))])
    _cycle(hd, "rotation_euler")
    return o


def chicken(x, y, rot=0.0, phase=0.0, col=(0.98, 0.98, 0.95)):
    o = _root("chicken", x, y, rot, 0.5)
    wh = P("chick%s" % (col,), col, rough=0.6); rd = P("red", COL["red"]); og = P("duckbeak", COL["orange"])
    sphere("body", 0.22, (0, 0, 0.3), wh, o, scale=(1.2, 1, 1))
    sphere("tail", 0.12, (-0.24, 0, 0.42), wh, o, scale=(0.7, 0.8, 1.3))
    hd = empty("chickhead", (0.18, 0, 0.5), o)
    sphere("head", 0.13, (0, 0, 0.05), wh, hd)
    cone("beak", 0.05, 0.12, (0.15, 0, 0.04), og, hd, verts=8, rot=(0, R90, 0))
    sphere("comb", 0.06, (0, 0, 0.19), rd, hd, scale=(1.3, 0.5, 1))
    for s in (-1, 1):
        sphere("eye", 0.025, (0.09, s * 0.08, 0.09), P("cowblack", BLACK), hd)
        cyl("leg", 0.02, 0.14, (0, s * 0.08, 0.07), og, o, verts=6)
    lib.keys(hd, "rotation_euler", [(phase, (0, 0, 0)), (6 + phase, (0, 0.9, 0)), (12 + phase, (0, 0, 0)), (18 + phase, (0, 0.9, 0)), (24 + phase, (0, 0, 0)), (90 + phase, (0, 0, 0))])
    _cycle(hd, "rotation_euler")
    return o


def horse(x, y, rot=0.0, phase=0.0, col=(0.6, 0.36, 0.16)):
    o = _root("horse", x, y, rot, 1.7)
    br = P("horse%s" % (col,), col, rough=0.5); dk = P("horsemane", (0.2, 0.11, 0.05))
    box("body", (1.8, 0.8, 0.85), (0, 0, 1.3), br, o, bevel=0.34, segs=5)
    _legs(o, br, (0.62, -0.62), (0.24, -0.24), 0.12, 0.95)
    for xx in (0.62, -0.62):
        for yy in (0.24, -0.24):
            cyl("hoof", 0.14, 0.14, (xx, yy, 0.07), dk, o, verts=12)
    nk = empty("horseneck", (0.75, 0, 1.55), o)
    box("neck", (0.5, 0.42, 1.0), (0.15, 0, 0.35), br, nk, bevel=0.18, rot=(0, 0.5, 0))
    box("head", (0.8, 0.4, 0.42), (0.62, 0, 0.78), br, nk, bevel=0.16, rot=(0, 0.25, 0))
    box("mane", (0.16, 0.14, 1.0), (-0.02, 0, 0.5), dk, nk, bevel=0.06, rot=(0, 0.5, 0))
    for s in (-1, 1):
        sphere("eye", 0.05, (0.72, s * 0.2, 0.86), P("cowblack", BLACK), nk)
        cone("ear", 0.07, 0.2, (0.3, s * 0.13, 1.08), br, nk, verts=8)
    cyl("tail", 0.07, 0.9, (-1.0, 0, 1.1), dk, o, verts=8, rot=(0, 0.3, 0))
    lib.keys(nk, "rotation_euler", [(phase, (0, 0, 0)), (50 + phase, (0, 0.75, 0)), (120 + phase, (0, 0.7, 0.1)), (160 + phase, (0, 0, 0)), (240 + phase, (0, 0, 0))])
    _cycle(nk, "rotation_euler")
    return o


def pond(x, y, rx=4.0, ry=3.0, ducks=3):
    FEATURES.append((x, y, max(rx, ry) + 0.8))
    cyl("pondrim", 1.0, 0.1, (x, y, 0.03), P("sand", (0.95, 0.83, 0.55), rough=0.8), verts=36).scale = (rx + 0.45, ry + 0.45, 1)
    cyl("deco_pond", 1.0, 0.1, (x, y, 0.05), lib.mat("water", (0.05, 0.6, 1.0), rough=0.08, spec=0.9, emit=0.15), verts=36).scale = (rx, ry, 1)
    for k in range(ducks):
        a = 2.1 * k + 0.5
        duck(x + math.cos(a) * rx * 0.5, y + math.sin(a) * ry * 0.5, 40 + k * 110, z=0.02, phase=k * 23)
    for k in range(5):
        a = 1.3 * k
        cyl("reed", 0.04, 1.2, (x + math.cos(a) * (rx + 0.2), y + math.sin(a) * (ry + 0.2), 0.6), P("stem", (0.2, 0.7, 0.2)), verts=6)
        sphere("reedtop", 0.09, (x + math.cos(a) * (rx + 0.2), y + math.sin(a) * (ry + 0.2), 1.25), P("trunk", (0.62, 0.4, 0.2)), scale=(1, 1, 2.2), segs=8, rings=6)


def field(x0, x1, y0, y1, kind=0):
    """Ploughed field with rows of crops: 0 wheat, 1 cabbage, 2 sunflower, 3 carrot tops."""
    FEATURES.append(((x0 + x1) / 2, (y0 + y1) / 2, max(x1 - x0, y1 - y0) * 0.72))
    box("soil", (x1 - x0, y1 - y0, 0.1), ((x0 + x1) / 2, (y0 + y1) / 2, 0.02), P("soil", (0.5, 0.32, 0.16), rough=0.9, spec=0.05), bevel=0.04)
    n = max(2, int((y1 - y0) / 1.1))
    for k in range(n):
        y = y0 + (k + 0.5) * (y1 - y0) / n
        if kind == 0:
            box("wheat", (x1 - x0 - 0.5, 0.5, 0.7), ((x0 + x1) / 2, y, 0.38), P("wheat", (1.0, 0.8, 0.2), rough=0.8, spec=0.05), bevel=0.18)
        else:
            m = int((x1 - x0) / 1.2)
            for j in range(m):
                x = x0 + (j + 0.5) * (x1 - x0) / m
                if kind == 1:
                    sphere("cabbage", 0.3, (x, y, 0.22), P("cabbage", (0.45, 0.85, 0.3), rough=0.6), scale=(1, 1, 0.75), segs=10, rings=6)
                elif kind == 2:
                    cyl("sunstem", 0.04, 1.3, (x, y, 0.65), P("stem", (0.2, 0.7, 0.2)), verts=6)
                    cyl("sunpetal", 0.3, 0.05, (x, y - 0.03, 1.35), P("sunflower", (1.0, 0.8, 0.05), rough=0.5), verts=12, rot=(R90, 0, 0))
                    cyl("sunheart", 0.14, 0.07, (x, y - 0.05, 1.35), P("trunk", (0.62, 0.4, 0.2)), verts=10, rot=(R90, 0, 0))
                else:
                    cone("carrot", 0.2, 0.5, (x, y, 0.3), P("leaf0", (0.18, 0.72, 0.2)), verts=8)


def apple_tree(x, y, s=1.0, col=(0.95, 0.1, 0.1)):
    FEATURES.append((x, y, 1.4))
    cyl("trunk", 0.17 * s, 1.3 * s, (x, y, 0.65 * s), P("trunk", (0.62, 0.4, 0.2), rough=0.6), verts=12)
    sphere("crown", 1.05 * s, (x, y, 2.0 * s), P("leaf0", (0.18, 0.72, 0.2), rough=0.5), scale=(1, 1, 0.9), segs=20, rings=12)
    rnd = random.Random(int(x * 11 + y * 5))
    for k in range(9):
        a = rnd.uniform(0, 2 * math.pi); b = rnd.uniform(-0.3, 0.9)
        sphere("apple", 0.12 * s, (x + math.cos(a) * math.cos(b) * 1.02 * s, y + math.sin(a) * math.cos(b) * 1.02 * s, (2.0 + math.sin(b) * 0.92) * s),
               P("apple%s" % (col,), col, rough=0.3), segs=8, rings=6)


def scarecrow(x, y, rot=-90):
    o = _root("scarecrow", x, y, rot, 0.8)
    w = P("wood2", COL["wood2"])
    cyl("pole", 0.06, 2.0, (0, 0, 1.0), w, o, verts=8)
    cyl("arms", 0.05, 1.6, (0, 0, 1.45), w, o, verts=8, rot=(R90, 0, 0))
    box("shirt", (0.3, 0.8, 0.7), (0, 0, 1.25), P("blue", COL["blue"]), o, bevel=0.1)
    sphere("head", 0.26, (0, 0, 1.9), P("hay", (0.98, 0.82, 0.3)), o)
    cone("hat", 0.34, 0.4, (0, 0, 2.2), P("barndoor", (0.62, 0.08, 0.07)), o, verts=14)
    for s in (-1, 1):
        sphere("eye", 0.04, (0.23, s * 0.09, 1.95), P("cowblack", BLACK), o)


def well(x, y):
    o = _root("well", x, y, 0, 1.2)
    cyl("wall", 0.7, 0.8, (0, 0, 0.4), P("rock", (0.6, 0.62, 0.66), rough=0.8), o, verts=18, bevel=0.06)
    cyl("water", 0.55, 0.04, (0, 0, 0.78), lib.mat("water", (0.05, 0.6, 1.0), rough=0.08, spec=0.9, emit=0.15), o, verts=18)
    for s in (-1, 1):
        cyl("post", 0.06, 1.5, (0, s * 0.6, 1.25), P("wood2", COL["wood2"]), o, verts=8)
    cone("roof", 0.95, 0.6, (0, 0, 2.2), P("red", COL["red"]), o, verts=4, rot=(0, 0, math.radians(45)))
    cyl("bucket", 0.14, 0.2, (0, 0, 1.3), P("gray", COL["gray"]), o, verts=10)


def bench(x, y, rot=-90):
    o = _root("bench", x, y, rot, 0.9)
    w = P("wood", COL["wood"])
    box("seat", (0.5, 1.5, 0.1), (0, 0, 0.45), w, o, bevel=0.04)
    box("back", (0.1, 1.5, 0.45), (-0.24, 0, 0.8), w, o, bevel=0.04)
    for s in (-1, 1):
        box("leg", (0.45, 0.1, 0.45), (0, s * 0.6, 0.22), P("gray", COL["gray"]), o, bevel=0.03)


def mailbox(x, y, col=COL["red"]):
    cyl("mailpost", 0.05, 1.0, (x, y, 0.5), P("white", COL["white"]), verts=8)
    box("mailbox", (0.5, 0.3, 0.3), (x, y, 1.1), P("mail%s" % (col,), col), bevel=0.1)


def sign(x, y, col=COL["yellow"], rot=0.0):
    cyl("signpost", 0.05, 1.7, (x, y, 0.85), P("gray", COL["gray"]), verts=8)
    cyl("signface", 0.36, 0.05, (x, y, 1.85), P("sign%s" % (col,), col, rough=0.3), verts=20, rot=(R90, 0, math.radians(rot)))
    cyl("signrim", 0.42, 0.03, (x, y, 1.85), P("white", COL["white"]), verts=20, rot=(R90, 0, math.radians(rot)))


def water_tower(x, y):
    o = _root("wtower", x, y, 0, 2.4)
    for a in range(4):
        cyl("leg", 0.12, 5.2, (math.cos(a * R90 + 0.78) * 1.2, math.sin(a * R90 + 0.78) * 1.2, 2.6), P("gray", COL["gray"]), o, verts=8)
    cyl("tank", 1.8, 2.4, (0, 0, 6.2), P("teal", COL["teal"]), o, verts=24, bevel=0.2)
    cone("top", 1.9, 1.0, (0, 0, 7.9), P("red", COL["red"]), o, verts=24)
    cyl("band", 1.83, 0.2, (0, 0, 6.2), P("white", COL["white"]), o, verts=24)


def church(x, y, rot=-90):
    o = house(x, y, rot, COL["white"], COL["teal"], w=4.6, d=6.0, h=3.2)
    box("tower", (1.7, 1.7, 6.2), (2.0, 0, 3.1), P("white", COL["white"]), o, bevel=0.15)
    cone("spire", 1.4, 2.4, (2.0, 0, 7.4), P("roof%s" % (COL["teal"],), COL["teal"]), o, verts=4, rot=(0, 0, math.radians(45)))
    sphere("bell", 0.3, (2.9, 0, 5.2), P("lamp", (1.0, 0.95, 0.7), emit=0.6), o)
    return o


def tent(x, y, col=COL["orange"], rot=0.0):
    o = _root("tent", x, y, rot, 1.6)
    c = cone("tent", 1.5, 1.7, (0, 0, 0.85), P("tent%s" % (col,), col, rough=0.6), o, verts=4, rot=(0, 0, math.radians(45)))
    c.scale = (1.25, 0.9, 1)
    box("tentdoor", (0.06, 0.5, 0.9), (0.93, 0, 0.45), P("cowblack", BLACK), o, bevel=0.02)


def pine(x, y, s=1.0):
    cyl("trunk", 0.2 * s, 1.0 * s, (x, y, 0.5 * s), P("trunk", (0.62, 0.4, 0.2), rough=0.6), verts=10)
    g = P("pine", (0.08, 0.5, 0.26), rough=0.6)
    for k in range(3):
        cone("pine", (1.25 - k * 0.3) * s, 1.4 * s, (x, y, (1.5 + k * 0.8) * s), g, verts=14)


def sailboat(x, y, N, col=COL["red"], phase=0.0):
    o = empty("boat", (x, y, -0.42))
    box("hull", (1.0, 2.2, 0.4), (0, 0, 0.1), P("boat%s" % (col,), col), o, bevel=0.18)
    cyl("mast", 0.05, 2.2, (0, 0, 1.3), P("wood2", COL["wood2"]), o, verts=8)
    sl = cone("sail", 0.9, 1.8, (0, 0.5, 1.4), P("white", COL["white"]), o, verts=3)
    sl.scale = (0.12, 1, 1)
    lib.keys(o, "rotation_euler", [(phase, (0.07, 0.04, 0)), (40 + phase, (-0.07, -0.04, 0)), (80 + phase, (0.07, 0.04, 0))])
    lib.keys(o, "location", [(0, (x, y, -0.42)), (N, (x, y + 5.0, -0.42))], interp="LINEAR")
    _cycle(o, "rotation_euler")


def hot_balloon(x, y, z, N, col=COL["red"], col2=COL["yellow"], drift=(6.0, 0.0), s=1.0, phase=0.0):
    o = empty("hotballoon", (x, y, z))
    sphere("env", 3.0 * s, (0, 0, 0), P("hb%s" % (col,), col, rough=0.4), o, scale=(1, 1, 1.15), segs=24, rings=14)
    for k in range(3):
        cyl("stripe", 3.0 * s * math.cos(0.5 * (k - 1)) + 0.04, 0.5 * s, (0, 0, (k - 1) * 1.55 * s), P("hb%s" % (col2,), col2, rough=0.4), o, verts=24)
    cone("neck", 1.6 * s, 2.0 * s, (0, 0, -3.3 * s), P("hb%s" % (col,), col, rough=0.4), o, verts=20, rot=(math.pi, 0, 0))
    box("basket", (1.1 * s, 1.1 * s, 0.9 * s), (0, 0, -5.2 * s), P("wood2", COL["wood2"]), o, bevel=0.12)
    for a in range(4):
        cyl("rope", 0.03, 1.4 * s, (math.cos(a * R90 + 0.78) * 0.6 * s, math.sin(a * R90 + 0.78) * 0.6 * s, -4.3 * s), P("cream", COL["cream"]), o, verts=5)
    fr = list(range(0, N + 1, 6))
    lib.bake(o, "location", fr, [(x + drift[0] * f / N, y + drift[1] * f / N, z + 0.7 * math.sin(f * 0.035 + phase)) for f in fr])


def birds(x0, x1, y, z, N, n=5, phase=0.0):
    """A little flock crossing the sky (flapping)."""
    root = empty("flock", (x0, y, z))
    lib.keys(root, "location", [(0, (x0, y, z)), (N, (x1, y, z))], interp="LINEAR")
    if x1 < x0:
        root.rotation_euler.z = math.pi
    dk = P("bird", (0.15, 0.15, 0.2), rough=0.6)
    for k in range(n):
        b = empty("bird", (-abs(k - n // 2) * 1.5, (k - n // 2) * 1.4, (k % 2) * 0.4), root)
        sphere("b", 0.22, (0, 0, 0), dk, b, scale=(1.6, 0.8, 0.8), segs=8, rings=6)
        for s in (-1, 1):
            w = empty("wing", (0, s * 0.1, 0), b)
            box("w", (0.45, 0.9, 0.05), (0, s * 0.45, 0), dk, w, bevel=0.02)
            ph = phase + k * 3
            lib.keys(w, "rotation_euler", [(ph, (s * 0.6, 0, 0)), (ph + 5, (-s * 0.5, 0, 0)), (ph + 10, (s * 0.6, 0, 0))])
            _cycle(w, "rotation_euler")


def life(N):
    """Everything extra; each thing is only put where the episode leaves room (OK)."""
    def put(fn, x, y, *a, m=1.0, **kw):
        if OK(x, y, m):
            fn(x, y, *a, **kw)

    def area(fn, x0, x1, y0, y1, *a, **kw):
        if all(OK(x, y, 0.5) for x in (x0, x1, (x0 + x1) / 2) for y in (y0, y1, (y0 + y1) / 2)):
            fn(x0, x1, y0, y1, *a, **kw)
            return True
        return False

    # --- sky
    hot_balloon(-22, 62, 24, N, COL["red"], COL["yellow"], (8, 0)); hot_balloon(36, 72, 30, N, COL["blue"], COL["white"], (-7, 0), 1.2, 2.0)
    hot_balloon(88, 58, 22, N, COL["purple"], COL["pink"], (6, 2), 0.9, 4.0); hot_balloon(60, 50, 19, N, COL["green"], COL["yellow"], (-5, 0), 0.8, 1.0)
    hot_balloon(8, -70, 26, N, COL["orange"], COL["white"], (7, 0), 1.1, 3.0); hot_balloon(70, -64, 22, N, COL["teal"], COL["yellow"], (-6, 0), 0.9, 5.0)
    hot_balloon(-52, -60, 24, N, COL["pink"], COL["white"], (5, 0), 1.0, 0.5)
    birds(-70, 60, 40, 17, N, 5); birds(110, 10, 46, 21, N, 5, 4); birds(-20, 90, -46, 18, N, 5, 2); birds(40, 130, 30, 14, N, 3, 6)
    for k, (x, y, z, s) in enumerate(((-80, 34, 15, 1.7), (118, 36, 15, 1.8), (10, 26, 19, 1.3), (66, 26, 18, 1.2), (-30, -40, 15, 1.8), (20, -46, 17, 2.0),
                                      (60, -42, 14, 1.6), (95, -48, 17, 1.9), (-66, -44, 16, 1.7), (125, -40, 15, 1.5))):
        T_cloud(x, y, z, s)
    # --- south horizon: hills so the land does not just end
    r = random.Random(14)
    for k in range(26):
        s = r.uniform(9, 16)
        sphere("hill", s, (-95 + k * 9.5, -r.uniform(58, 74), -s * 0.45), lib.mat("hill%d" % (k % 2), [(0.3, 0.74, 0.2), (0.42, 0.84, 0.26)][k % 2], rough=0.9, spec=0.05),
               scale=(1.6, 1, 0.75), segs=28, rings=14)
    # --- behind the hangars and the west
    water_tower(-49.5, 27.5); church(-71, 26, -90)
    for k in range(9):
        pine(-45 + k * 4.2, 25.5 + (k % 2) * 1.6, 1.2 + (k % 3) * 0.15)
    area(field, -82, -70, 9, 18, 2); area(paddock, -80, -70, -14, -7)
    put(horse, -77, -10.5, 30); put(horse, -73, -11.5, 200, 70, (0.92, 0.9, 0.85))
    put(house, -84, -22, 90, (1.0, 0.8, 0.85), COL["blue"]); put(pond, -62, -13, 3.6, 2.6)
    # --- meadow in front of the hangars (south of the road)
    area(paddock, -47, -38, -15, -8.5)
    for k, (x, y, a) in enumerate(((-45, -11, 20), (-42.5, -13, 150), (-40, -10.5, 260))):
        put(sheep, x, y, a, k * 19)
    put(pond, -24, -11.5, 3.4, 2.4); put(haystack, -31, -9, 40); put(haystack, -29.2, -9.9, 10); put(scarecrow, -33.5, -13.5, 90)
    put(bench, -17, -6.5, 90); put(well, -52, -7.5); put(tent, -56, -16, COL["orange"], 60); put(tent, -60, -18.5, COL["teal"], 20)
    # --- village by the river: small things between the houses
    put(well, 2.2, 11.0); put(bench, -4.2, 10.6, -90); put(mailbox, -9.3, 10.3); put(mailbox, 3.2, 14.6, COL["blue"])
    for k, (x, y, a) in enumerate(((-3.2, 11.6, 40), (-2.2, 12.4, 200), (-4.6, 12.8, 120), (7.6, 10.6, 300))):
        put(chicken, x, y, a, k * 11, [(0.98, 0.98, 0.95), (0.75, 0.45, 0.2)][k % 2], m=0.3)
    area(field, -11, -4, 19, 25.5, 0); area(field, 5.5, 9, 17, 25, 1)
    sailboat(11.6, 30, N); sailboat(12.5, -30, N, COL["blue"], 20)
    # --- between the river and the middle farm
    put(pond, 25.5, 21.5, 3.8, 2.6)
    for k, (x, y) in enumerate(((31, 21), (34.5, 22.5), (38, 21), (32.5, 25), (36.5, 25.5))):
        put(apple_tree, x, y, 1.0 + (k % 2) * 0.15)
    area(paddock, 36.5, 40.5, 15.5, 19.5, False)
    put(pig, 37.6, 17, 20, m=0.2); put(pig, 39.2, 18.4, 200, 40, m=0.2); put(pig, 39.4, 16.4, 100, 80, m=0.2)
    for k, (x, y, a) in enumerate(((30.8, 11.6, 10), (32, 12.6, 150), (27.2, 11.2, 250))):
        put(chicken, x, y, a, k * 13, [(0.98, 0.98, 0.95), (0.75, 0.45, 0.2)][k % 2], m=0.3)
    put(mailbox, 26.4, 12.4); put(scarecrow, 62.5, 21, -90)
    # --- behind the wood pile / hole
    area(field, 58, 70, 17, 24.5, 2); area(field, 59.5, 68.5, 26, 30, 1)
    area(paddock, 78.5, 86, 19, 25); put(horse, 80.5, 21.5, -20); put(horse, 84, 23, 170, 60, (0.25, 0.16, 0.1))
    put(well, 91.5, 11.6); put(bench, 85.2, 10.8, -90); put(mailbox, 79.8, 10.6, COL["blue"]); put(mailbox, 92.6, 11.2)
    for k, (x, y, a) in enumerate(((86.5, 12, 60), (84.6, 12.6, 220), (93.5, 13.2, 140))):
        put(chicken, x, y, a, k * 9, m=0.3)
    # --- east end
    put(church, 115, 17, -90); area(field, 110, 124, 23, 30, 0); put(water_tower, 123, 14)
    for k in range(6):
        pine(101 + k * 4.5, 27 + (k % 2) * 1.5, 1.2)
    # --- far south band (seen when a camera looks south)
    area(paddock, 46, 56, -36, -30); put(cow, 49, -33, 10); put(cow, 53, -32.5, 190, 50)
    put(windmill, 63, -37, 90, N, 0.14); put(house, 84, -33, 90, COL["cream"], COL["purple"]); put(house, 50, -42, 90, (1.0, 0.8, 0.85), COL["red"])
    area(field, -6, 6, -46, -38, 0); area(field, 10, 22, -47, -39, 2); area(field, 68, 80, -46, -39, 1); area(field, 88, 104, -45, -38, 0)
    put(pond, 16, -31, 4.2, 2.8); put(church, 104, -32, 90); put(water_tower, -2, -36)
    for k in range(14):
        pine(-70 + k * 15 + (k % 3), -50 - (k % 2) * 3, 1.5)
    # --- along the road, where nobody works: signs, benches
    for k, x in enumerate(range(-100, 126, 14)):
        put(sign, x + 3.0, -3.3, [COL["yellow"], COL["blue"], COL["red"]][k % 3], m=1.6)
        put(lamp, x - 2.0, 3.3, m=1.6)
