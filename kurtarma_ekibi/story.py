"""Shared world for the 'Kahraman Kasaba' episodes that use the user's own characters."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
from lib import *
from vehicles import *
import cards as cd

PARK = (50, 92, 5.5, 26)        # x0, x1, y0, y1 (north side of the road)
FARM = (128, 178, 5.0, 40)
NORTH_LANE, SOUTH_LANE = 1.8, -1.8
SIDEWALK_N = 4.4


def build_world(N, farm=True, park_props=True):
    s = reset(N)
    cd.reset_cards()
    st = standard_world(N, skip_zones=[(PARK[0] - 2, 4.6, PARK[1] + 2, 32), (FARM[0], 4.6, FARM[1], 45)])
    W = dict(scene=s, station=st)
    cd.park(*PARK)
    W["pg"] = cd.playground((80, 16.5, 0))
    for x, y, r in ((58, 9.2, -90), (88, 9.2, -90)):
        cd.bench((x, y, 0), rot=math.radians(r))
    for x, y in ((53, 22), (66, 23), (91, 22), (73, 24)):
        tree((x, y, 0), s=1.25, seed=int(x * 3))
    for x in (51, 63, 75, 87):
        lamp_post((x, 5.0, 0))
    if farm:
        barn((152, 22, 0), rot=math.radians(-90))
        for k in range(3):
            cyl("hay", 0.7, 1.0, (140 + k * 1.6, 12, 0.7), mat("hay", (0.95, 0.8, 0.35), rough=0.9), rot=(math.radians(90), 0, 0), verts=20)
        x = FARM[0] + 2
        while x < FARM[1] - 2:
            if not (133.5 < x < 139.5):
                box("ffence", (0.12, 0.12, 0.9), (x, 6.0, 0.45), mat("fence", (1, 0.95, 0.85), rough=0.6), bevel=0.03)
            x += 1.4
        for a0, a1 in ((FARM[0] + 2, 133.5), (139.5, FARM[1] - 2)):
            box("ffrail", (a1 - a0, 0.08, 0.1), ((a0 + a1) / 2, 6.0, 0.7), mat("fence", (1, 0.95, 0.85)), bevel=0.02)
        for gx in (133.6, 139.4):
            box("gatepost", (0.2, 0.2, 1.4), (gx, 6.0, 0.7), mat("gatepost", (0.85, 0.3, 0.25), rough=0.5), bevel=0.05)
        box("farmgrass", (FARM[1] - FARM[0], FARM[3] - FARM[2], 0.05), ((FARM[0] + FARM[1]) / 2, (FARM[2] + FARM[3]) / 2, 0.025),
            noise_mat("farmgrass", (0.45, 0.78, 0.2), (0.6, 0.85, 0.3), 0.8, rough=0.85), bevel=0)
    return W


def driver_card(v, name, h=None):
    h = h or {"fire": 0.82, "recycler": 0.82}.get(v.kind, 0.9)
    return cd.char(name, (0, 0, -0.08), height=h, parent=v.seat, shadow=False)


def flash_lights(v, f0, f1, period=10):
    for i, m in enumerate(v.lights):
        flash(m, f0, f1, period=period, on=9, phase=i)


def outro_cam(name, f0, f1, loc, tgt, up=(3, 2, 9), look_up=(8, 6, 10), lens=30):
    c = camera(name, [(f0, loc, tgt), (f1, tuple(Vector(loc) + Vector(up)), tuple(Vector(tgt) + Vector(look_up)))], lens=lens)
    cut(f0, c)
    return c


def celebrate(center, f0, face=math.radians(-90), n_conf=55):
    sfx(f0, "yay")
    confetti(tuple(Vector(center) + Vector((0, 0, 0.6))), f0 + 4, n=n_conf)
    sfx(f0 + 4, "confetti")
    stars_burst(tuple(Vector(center) + Vector((0, 0, 2.2))), f0 + 10, n=8, face_rot=face, radius=2.4)
    balloons(tuple(Vector(center) + Vector((0, -0.4, 0.3))), f0 + 40, n=7)
    sfx(f0 + 40, "balloon")


def finish(N, seg):
    cd.finish_all(N)
    render(seg)


def track_cam(name, fn, f0, f1, offset, look=(0, 0, 1), step=2, lens=30):
    """Camera that follows any position function fn(frame) -> Vector (e.g. a card's path)."""
    ks = []
    for f in range(f0, f1 + 1, step):
        p = Vector(fn(f))
        ks.append((f, tuple(p + Vector(offset)), tuple(p + Vector(look))))
    cdat = bpy.data.cameras.new(name)
    cdat.lens = lens
    cdat.clip_end = 600
    c = bpy.data.objects.new(name, cdat)
    bpy.context.scene.collection.objects.link(c)
    t = empty(name + "_tgt")
    from lib import _dof
    _dof(cdat, t)
    frames = [k[0] for k in ks]
    bake(c, "location", frames, [k[1] for k in ks])
    bake(t, "location", frames, [k[2] for k in ks])
    con = c.constraints.new("TRACK_TO"); con.target = t
    con.track_axis = "TRACK_NEGATIVE_Z"; con.up_axis = "UP_Y"
    return c
