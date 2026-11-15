"""30 sn önizleme – oyuncak araçlar: köprü yok, vinç ve uzun kamyon köprüyü yerine koyuyor."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import lib, toys as T
from lib import camera, cut, sfx, bake

N = 720
LO = "--lo" in sys.argv
lib.DOF_FSTOP = 16
s = lib.reset(N, res=(640, 360) if LO else (1280, 720), samples=4 if LO else 12)
lib.world(top=(0.1, 0.45, 1.0), horizon=(0.7, 0.9, 1.0), light=0.75)
lib.sun(energy=3.0, rot=(math.radians(52), 0, math.radians(-35)), angle=14)
s.eevee.use_soft_shadows = True
s.eevee.shadow_cascade_size = "2048"
s.eevee.use_gtao = True
RX = 12.0
T.world(RX)
for k, (x, y, sz, kd) in enumerate(((-6, 7, 1.3, 0), (-1, 10, 1.1, 1), (4, 8, 1.4, 2), (-12, 9, 1.2, 1), (17, 8, 1.3, 0), (21, 11, 1.1, 1),
                                    (26, 7, 1.4, 2), (-9, -17, 1.2, 0), (0, -18, 1.0, 1), (19, -17, 1.3, 2), (30, -16, 1.1, 0),
                                    (-30, 13, 1.3, 1), (-34, -8, 1.2, 0), (8, 13, 1.0, 1), (16, 14, 1.2, 0))):
    T.tree(x, y, sz, kd)
# base: four hangars in the vehicles' colours
HX = (-29.0, -24.0, -19.0, -14.0)
cols = (T.COL["red"], T.COL["orange"], T.COL["blue"], T.COL["yellow"])
for x, c in zip(HX, cols):
    T.hangar(x, 8.0, c)
    lib.box("apron", (3.6, 8.2, 0.06), (x, 3.9, 0.0), lib.mat("road", (0.22, 0.22, 0.26)), bevel=0.02)

car = T.make_car("kirmizi", T.COL["red"], loc=(HX[0], 9.0), heading=-90)
crane = T.make_crane("vinc", T.COL["orange"], loc=(HX[1], 10.0), heading=-90)
flat = T.make_flatbed("tir", T.COL["blue"], loc=(HX[2], 10.5), heading=-90)
taxi = T.make_car("sari", T.COL["yellow"], loc=(HX[3], 6.0), heading=-90)
deck = T.bridge_deck()
DZ = flat.bed_z + 0.33

# ---- story
# 1) the little red car leaves the base and drives to the river
T.drive_path(car, 8, 185, [(HX[0], 3.0), (-25.5, 0.2), (-18, 0), (0, 0), (8.0, 0)])
sfx(8, "honk"); sfx(20, "truck", dur=6.0)
T.nod(car, 185, deg=5)
sfx(183, "brake")
T.hop(car, 204, n=2, h=0.22)
sfx(204, "question"); sfx(226, "honk")
T.drive_path(car, 236, 276, [(3.6, 0)], reverse=True)
sfx(238, "beep_reverse", dur=1.4)
# 2) help is coming: the crane and the long truck with a new bridge deck
T.drive_path(flat, 222, 372, [(HX[2], 3.0), (-15.5, 0.2), (-9, 0), (-4, 0), (0.5, -3.4), (6.4, -3.9)])
T.drive_path(crane, 236, 384, [(HX[1], 3.0), (-20.5, 0.2), (-12, 0), (-4.5, 0), (0.5, 3.4), (8.2, 3.9)])
sfx(224, "truck", dur=6.5); sfx(250, "honk")
T.nod(flat, 372, deg=3); T.nod(crane, 384, deg=3)
sfx(372, "brake")
# 3) crane work
F_ATT, F_LIFT, F_SWING, F_DOWN, F_REL = 446, 470, 520, 556, 566
src = flat.at(F_ATT, (flat.bed_x, 0, 0))
y0, p0, c0 = T.crane_aim(crane, F_ATT, (src.x, src.y), DZ + 0.05)
y1, p1, c1 = T.crane_aim(crane, F_ATT, (RX, 0), 0.08)
hy = math.degrees(crane.pose(400)[2])
T.crane_keys(crane, [(0, -90, 14, 1.2), (236, -90, 14, 1.2), (237, hy, 14, 1.2), (396, hy, 14, 1.2), (428, y0, p0, 1.6),
                     (F_ATT, y0, p0, c0), (F_LIFT, y0, p0 + 4, c0 - 2.0), (F_SWING, y1, p1, c1 - 4.6), (F_DOWN, y1, p1, c1),
                     (F_REL, y1, p1, c1), (600, y1 + 25, p1, 2.0), (N, y1 + 25, p1, 2.0)])
# the boom follows the truck's heading while driving
ks = [(f, math.degrees(crane.pose(f)[2]), 14, 1.2) for f in range(236, 397, 2)]
crane.ctl = sorted([k for k in crane.ctl if not 236 <= k[0] <= 396] + ks)
T.crane_bake(crane, N)
sfx(398, "ratchet", dur=1.4); sfx(430, "ratchet", dur=0.8); sfx(F_ATT, "ding")
sfx(F_LIFT, "ratchet", dur=2.0); sfx(F_SWING + 6, "ratchet", dur=1.4); sfx(F_DOWN, "thud"); sfx(F_DOWN + 4, "ding", pitch=1.3)
# the deck rides on the truck, then hangs on the hook, then lies across the river
fr = list(range(N + 1)); dl, dr = [], []
for f in fr:
    if f < F_ATT:
        p = flat.at(f, (flat.bed_x, 0, 0)); dl.append((p.x, p.y, DZ)); dr.append((0, 0, flat.pose(f)[2]))
    elif f <= F_DOWN:
        hk = T.crane_tip(crane, f)[1]
        sw = 0.05 * math.sin((f - F_LIFT) * 0.35) * max(0, min(1, (f - F_LIFT) / 10, (F_DOWN - f) / 14))
        dl.append((hk.x, hk.y, hk.z - 0.05)); dr.append((0, sw, flat.pose(F_ATT)[2] * 0 + sw * 0.6))
    else:
        dl.append((RX, 0, 0.03)); dr.append((0, 0, 0))
bake(deck, "location", fr, dl); bake(deck, "rotation_euler", fr, dr)
T.hop(flat, 572, n=1, h=0.15); T.hop(crane, 578, n=1, h=0.12)
sfx(574, "honk")
# 4) the red car crosses the new bridge; everybody is happy
T.drive_path(car, 588, 664, [(8, 0), (RX, 0), (19.5, 0)])
sfx(588, "truck", dur=3.0)
T.hop(car, 672, n=3, h=0.3)
T.hop(flat, 676, n=2, h=0.16); T.hop(crane, 680, n=2, h=0.14)
sfx(672, "yay"); sfx(676, "honk"); sfx(690, "tada")
lib.confetti((19.5, 0, 3.5), 674, n=60, spread=5.0, height=5.0)
lib.stars_burst((19.5, 0, 2.6), 672, n=8, radius=2.4)

# ---- cameras
def follow(name, t, f0, f1, off, look=(0, 0, 0.8), lens=35, smooth=12):
    xs = [t.pose(f) for f in range(f0, f1 + 1)]
    ks = []
    for k, f in enumerate(range(f0, f1 + 1)):
        w = xs[max(0, k - smooth):k + smooth + 1]
        x = sum(p[0] for p in w) / len(w); y = sum(p[1] for p in w) / len(w)
        ks.append((f, (x + off[0], y + off[1], off[2]), (x + look[0], y + look[1], look[2])))
    c = camera(name, ks[:1], lens)
    tgt = bpy.data.objects[name + "_tgt"]
    bake(c, "location", [k[0] for k in ks], [k[1] for k in ks])
    bake(tgt, "location", [k[0] for k in ks], [k[2] for k in ks])
    return c

c1 = camera("c1", [(0, (-34, -14, 7.5), (-22, 6, 1.5)), (84, (-31, -12, 6.5), (-21, 4, 1.2))], 32)
c2 = follow("c2", car, 84, 190, (3.5, -7.5, 1.9), look=(0.6, 0, 0.6), lens=38)
c3 = camera("c3", [(190, (17.2, -6.2, 1.7), (8.4, 0, 0.7)), (262, (16.6, -5.8, 1.9), (7.0, 0, 0.7))], 40)
c4 = follow("c4", flat, 262, 344, (6.5, -10.5, 3.0), look=(-2.0, 1.0, 1.0), lens=30)
c5 = camera("c5", [(344, (17.5, -11, 6.5), (7.5, 0, 1.2)), (400, (16.5, -10.5, 6.0), (7.5, 0, 1.4))], 30)
c6 = camera("c6", [(400, (1.5, -10.5, 3.2), (6.0, -2.5, 2.2)), (470, (2.5, -10.0, 3.6), (6.5, -2.0, 3.0))], 34)
c7 = camera("c7", [(470, (19.0, -9.5, 5.0), (9.5, 0.5, 2.6)), (588, (18.0, -9.0, 4.2), (10.0, 0.3, 1.6))], 30)
c8 = camera("c8", [(588, (18.2, -7.0, 1.7), (10.0, 0, 0.6)), (640, (18.8, -7.2, 1.8), (13.0, 0, 0.6))], 38)
c9 = camera("c9", [(640, (27.5, -9.0, 3.6), (14.5, 0.5, 1.2)), (N, (26.0, -8.5, 3.2), (14.5, 0.5, 1.2))], 30)
for f, c in ((0, c1), (84, c2), (190, c3), (262, c4), (344, c5), (400, c6), (470, c7), (588, c8), (640, c9)):
    cut(f, c)
lib.render("t_preview")
print("BUILT")
