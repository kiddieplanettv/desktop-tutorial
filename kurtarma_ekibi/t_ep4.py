"""Bölüm 4 – Yoldaki çukur: uzun kamyonun tekeri çukura düşüyor; çekici çekiyor, damper kumla dolduruyor, vinç düşen sandığı geri koyuyor."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_common import *

N = 2040
HXP = 74.0
s, deck = setup(N, bridge=True, clear=[(40, 100, -22, -2), (70, 80, 4, 12), (55, 62, 9, 15)], pads=[(52, 71, -7.4, -2.0), (55, 85, 2.0, 7.8)])
V = fleet(dict(flat=(44, 0, 0)))
car, crane, flat, tow, dump = V["car"], V["crane"], V["flat"], V["tow"], V["dump"]
C = Cams()
lib.cyl("deco_hole", 1.3, 0.02, (HXP, -0.2, 0.05), T.P("hole", (0.05, 0.04, 0.04), rough=0.9, spec=0.0), verts=28).scale = (1.0, 1.25, 1)
rnd = random.Random(5)
for k in range(11):
    a = 2 * math.pi * k / 11
    lib.box("deco_chunk", (rnd.uniform(0.3, 0.55), rnd.uniform(0.25, 0.45), 0.14), (HXP + math.cos(a) * 1.42, -0.2 + math.sin(a) * 1.75, 0.08),
            lib.mat("road", (0.22, 0.22, 0.26)), bevel=0.05, rot=(rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2), a))
CZ = flat.bed_z + 0.45
slots = (-2.9, -1.6, -0.3)
ccol = (T.COL["green"], T.COL["pink"], T.COL["teal"])
crates = []
for k, sx in enumerate(slots):
    c = lib.empty("crate%d" % k)
    lib.box("cr", (0.9, 0.9, 0.9), (0, 0, 0), T.P("crate%d" % k, ccol[k]), c, bevel=0.1)
    lib.box("crband", (0.94, 0.3, 0.94), (0, 0, 0), T.P("white", T.COL["white"]), c, bevel=0.05)
    crates.append(c)

# 1) the long truck carries crates; its front wheel drops into a hole in the road
fa = T.go(flat, 6, [(60, 0), (HXP - 2.95, 0)], speed=6.0)
sfx(6, "truck", dur=6.0); sfx(30, "birds", dur=6.0)
T.body_keys(flat, [(fa - 5, 0, 0, 0), (fa + 5, -0.13, 5.0, -2.0), (fa + 14, -0.1, 4.0, -1.5)])
sfx(fa - 2, "thud"); sfx(fa + 6, "oops")
GX, GY = HXP - 3.1, 2.95
for k in range(1):
    a = fa + 70 + k * 84
    T.spin_wheels(flat, a, a + 56, speed=-9.0)
    T.body_keys(flat, [(a, -0.1, 4.0, -1.5), (a + 12, -0.09, 3.4, 1.0), (a + 26, -0.1, 4.2, -1.6), (a + 40, -0.09, 3.4, 0.8), (a + 56, -0.1, 4.0, -1.5)])
    sfx(a, "truck", dur=2.4); sfx(a + 8, "slip")
f1 = fa + 70 + 84
sfx(f1, "sad")
for k in range(3):
    sfx(f1 + 40 + k * 16, "honk")
C.follow(0, fa - 50, flat, (6.0, -10.0, 3.0), look=(0.5, 0, 1.4), lens=32)
C.shot(fa - 50, fa + 60, (79.5, -4.6, 1.5), (73.2, -0.4, 0.9), (79.0, -4.2, 1.4), (73.2, -0.4, 0.9), lens=34)
C.shot(fa + 60, f1 + 90, (77.5, 9.5, 3.4), (72.0, 0.8, 1.2), (77.0, 9.0, 3.2), (72.0, 1.0, 1.0), lens=32)

# 2) the tow truck pulls the long truck back out
f2 = f1 + 90
T.place(tow, f2, 48.0, 0, 0)
T.beacon(tow, (0.15, 0, 2.2), f2, f2 + 300)
f3 = T.go(tow, f2, [(58, 0), (62.0, -3.5), (65.5, -4.0), (66.3, -1.7), (64.9, -0.1), (63.7, 0)], speed=5.5)
sfx(f2, "truck", dur=5.0); sfx(f2 + 30, "honk"); T.nod(tow, f3, deg=3)
RA = f3 + 20
sfx(RA, "ding")
T.body_keys(flat, [(RA + 8, -0.1, 4.0, -1.5), (RA + 34, 0, 0, 0)])
T.drive_path(tow, RA + 34, RA + 150, [(57.7, 0)])
T.drive_path(flat, RA + 38, RA + 154, [(HXP - 2.95 - 6.0, 0)], reverse=True)
FX = HXP - 2.95 - 6.0
sfx(RA + 30, "truck", dur=5.0); sfx(RA + 60, "pop"); sfx(RA + 156, "yay", vol=0.7)
RB = RA + 166
T.rope("rope", lambda f: tow.at(f, tow.hook), lambda f: flat.at(f, (-4.15, 0, 0.95)), RA, RB)
T.hop(tow, RA + 160, n=2, h=0.22); T.hop(flat, RA + 164, n=1, h=0.12)
f4 = T.go(tow, RB + 10, [(55.5, -1.5), (54.0, -5.0)], speed=3.0)
C.follow(f2, f2 + 80, tow, (4.5, -8.5, 2.3), look=(-1.0, 0, 0.8), lens=34)
C.shot(f2 + 80, RA + 20, (60.0, -9.0, 3.4), (65.5, -0.5, 1.0), (60.6, -9.4, 3.2), (65.8, -0.3, 1.0), lens=32)
C.shot(RA + 20, RB + 30, (64.5, -11.5, 3.6), (66.0, 0, 1.2), (60.0, -11.5, 3.6), (62.5, 0, 1.2), lens=30)

# 3) the dump truck fills the hole with sand and rolls it flat
f5 = RB + 30
T.place(dump, f5, 46.0, 0, 0)
dump.sand.scale = (1.75, 1.0, 0.75)
f6 = T.go(dump, f5, [(56, 0), (61.5, 4.8), (72.0, 5.6), (79.6, 3.0), (81.2, 0.3)], speed=6.0)
f7 = T.go(dump, f6 + 8, [(77.7, 0)], speed=2.2, reverse=True)
sfx(f5, "truck", dur=7.0); sfx(f6 + 8, "beep_reverse", dur=2.0)
TA = f7 + 12
TE = T.tip(dump, TA, TA + 44, deg=50, hold=50)
lib.keys(dump.sand, "scale", [(TA + 20, (1.75, 1.0, 0.75)), (TA + 76, (0.9, 0.8, 0.3)), (TA + 92, (0.001, 0.001, 0.001))])
lib.keys(dump.sand, "location", [(TA + 20, (1.1, 0, 0.95)), (TA + 86, (-0.3, 0, 0.7))])
pile = lib.sphere("sandpile", 1.0, (HXP + 0.1, -0.2, 0.0), T.P("sandpile", (0.98, 0.8, 0.42), rough=0.85, spec=0.1), scale=(0.001, 0.001, 0.001), segs=32, rings=16)
T.burst((HXP + 0.2, -0.2, 0.3), TA + 38, n=14, col=(0.98, 0.8, 0.42), seed=41, name="sandbit", height=0.8)
T.burst((HXP + 0.2, -0.2, 0.3), TA + 60, n=14, col=(0.98, 0.8, 0.42), seed=42, name="sandbit", height=0.8)
sfx(TA, "ratchet", dur=1.8); sfx(TA + 32, "whoosh"); sfx(TA + 46, "crackle", dur=2.0); sfx(TE - 40, "ratchet", dur=1.6)
p1 = T.go(dump, TE + 8, [(72.9, 0)], speed=2.4, reverse=True)
p2 = T.go(dump, p1 + 8, [(78.2, 0)], speed=2.6)
p3 = p2
p4 = T.go(dump, p3 + 8, [(86.0, 0), (100, 0), (126, 0)], speed=5.0)
lib.keys(pile, "scale", [(TA + 30, (0.001, 0.001, 0.001)), (TA + 92, (1.35, 1.5, 0.95)), (TE + 30, (1.35, 1.5, 0.95)), (p1, (1.55, 1.8, 0.4)),
                         (p2, (2.0, 2.4, 0.12))])
sfx(TE + 8, "beep_reverse", dur=2.0); sfx(TE + 40, "thud"); sfx(p1 + 30, "thud"); sfx(p2 + 4, "sparkle")
C.shot(f5, f5 + 70, (52.0, -9.5, 3.4), (58.0, 1.5, 1.4), (53.0, -9.5, 3.4), (60.0, 2.5, 1.4), lens=32)
C.shot(f5 + 70, TA - 6, (84.5, -9.5, 5.0), (76.5, 0.5, 1.4), (83.5, -9.0, 4.6), (76.0, 0, 1.4), lens=30)
C.shot(TA - 6, TE + 8, (71.6, -6.4, 2.6), (75.4, -0.2, 1.5), (71.2, -6.0, 2.4), (75.2, -0.2, 1.3), lens=32)
C.shot(TE + 8, p3 + 30, (76.5, -8.5, 2.6), (74.5, 0, 0.7), (75.5, -8.5, 2.4), (74.2, 0, 0.6), lens=32)

# 4) the crane puts the fallen crate back
f8 = p3 + 30
T.place(crane, f8, 50.0, 0, 0)
f9 = T.go(crane, f8, [(57, 0), (61.0, 4.6), (66.5, 6.2)], speed=5.5)
sfx(f8, "truck", dur=4.0); T.nod(crane, f9, deg=3)
f10 = f9 + 12
slot = (FX + slots[2], 0)
A1, D1, E1 = T.crane_job(crane, f10, (GX, GY), 0.45 + 0.52, slot, CZ + 0.52, pace=1.2)
T.crane_bake(crane, N)


def ride(k):
    def fn(f):
        p = flat.at(f, (slots[k], 0, 0))
        return (p.x, p.y, CZ + flat.body.location.z * 0), flat.pose(f)[2]
    return fn


def crate2(f):
    if f < fa:
        return ride(2)(f)
    u = min(1.0, (f - fa) / 26.0)
    p0 = flat.at(fa, (slots[2], 0, 0))
    return (p0.x + (GX - p0.x) * u, GY * (u ** 1.5), CZ + (0.45 - CZ) * u * u + 0.5 * math.sin(math.pi * u) * (1 - u)), 0.0


sfx(fa + 2, "whoosh"); sfx(fa + 26, "thud")
sfx(f10, "ratchet", dur=1.6); sfx(A1, "ding"); sfx(A1 + 4, "ratchet", dur=1.2); sfx(A1 + 40, "ratchet", dur=2.2)
sfx(D1 - 40, "ratchet", dur=1.5); sfx(D1, "thud"); sfx(D1 + 5, "ding", pitch=1.3)
C.shot(f8, f9 + 10, (58.0, 12.5, 4.4), (63.5, 3.0, 1.4), (59.0, 13.0, 4.4), (65.5, 4.0, 1.4), lens=32)
C.shot(f9 + 10, A1 + 30, (75.5, 6.5, 2.2), (70.9, 2.9, 0.9), (75.2, 6.9, 2.8), (70.6, 3.0, 1.8), lens=34)
C.shot(A1 + 30, E1, (71.5, -10.0, 5.2), (66.5, 1.5, 2.6), (70.5, -9.6, 4.8), (66.0, 1.0, 2.4), lens=30)

# 5) the road is whole again: everybody drives on
f11 = E1 + 4
party((70.0, 0, 4.4), f11)
for k, n in enumerate(("flat", "crane", "tow")):
    T.hop(V[n], f11 + 4 + k * 6, n=2, h=0.22 if n == "tow" else 0.13)
f12 = f11 + 56
g1 = T.go(flat, f12, [(72.0, 0), (76.5, 0), (100, 0), (124, 0)], speed=5.5)
T.place(car, f12 + 30, 50.0, 0, 0)
g2 = T.go(car, f12 + 30, [(62, 0), (72.5, 0)], speed=7.0)
T.hop(car, g2 + 4, n=2, h=0.26); sfx(g2 + 4, "boing")
g3 = T.go(car, g2 + 34, [(100, 0), (124, 0)], speed=6.5)
T.go(tow, f12 + 110, [(56.5, -1.5), (62, 0), (100, 0), (124, 0)], speed=6.0)
T.go(crane, f12 + 140, [(70.0, 4.5), (74.5, 0.4), (100, 0), (124, 0)], speed=5.5)
sfx(f12, "truck", dur=8.0); sfx(f12 + 60, "honk"); sfx(f12 + 130, "honk"); sfx(f12 + 200, "honk")
C.shot(f11, f12 + 60, (80.0, -6.0, 1.8), (73.5, -0.2, 0.9), (80.6, -6.4, 2.0), (73.5, -0.2, 0.9), lens=34)
C.shot(f12 + 60, N, (84.0, -13.0, 5.5), (72.0, 0, 1.2), (88.0, -15.5, 8.0), (74.0, 0, 1.2), lens=30)
T.crane_bake(crane, N)
for k in (0, 1):
    fr_ = list(range(N + 1))
    bake(crates[k], "location", fr_, [ride(k)(f)[0] for f in fr_]); bake(crates[k], "rotation_euler", fr_, [(0, 0, ride(k)(f)[1]) for f in fr_])
T.hang_bake(crane, crates[2], N, [(A1, D1, ride(2), 0.0)], crate2, dz=0.52, sway=0.04)
fr_ = list(range(fa, fa + 27))
bake(crates[2], "rotation_euler", fr_, [(math.pi * min(1.0, (f - fa) / 26.0), 0, 0) for f in fr_])
print("FRAMES", fa, f1, f2, f3, RA, RB, f5, f6, f7, TA, TE, p1, p2, p3, f8, f9, A1, D1, E1, f11, f12, g1, g2, g3)
done("t_ep4")
