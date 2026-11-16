"""Toy countryside for the 'Minik Ustalar' videos: houses, barn, silo, windmills, farm animals, fences, haystacks,
flowers, bushes, rocks, lamp posts, mountains. Everything is built from simple rounded shapes (plastic toy look)."""
import bpy, math, random
import lib
from lib import box, cyl, sphere, empty, cone
from toys import P, COL, R90

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
