"""Bölüm 2 – Devrilen ağaç: yol kapalı; çekici itemiyor, vinç kütüğü uzun kamyona yüklüyor, kereste yığınına götürüyorlar."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_common import *

N = 2040
LX, LY = 34.0, 0.6
PX, PY = 64.5, 11.0
s, deck = setup(N, bridge=True, clear=[(-22, 46, -18, -2), (50, 76, -24, -2), (58, 71, 8, 14), (36, 44, 2, 9)],
                pads=[(16, 37, 2.0, 7.8), (21, 37, -7.8, -2.0), (44, 70, 2.0, 7.8), (52, 73, -7.8, -2.0)])
V = fleet(dict(tow=(-10, 0, 0), car=(-19, 0, 0)))
car, crane, flat, tow, dump = V["car"], V["crane"], V["flat"], V["tow"], V["dump"]
C = Cams()
R = 0.38
wood = T.P("log", (0.62, 0.38, 0.18), rough=0.7); ring = T.P("logring", (0.95, 0.78, 0.5), rough=0.7)


def make_log(L=6.2, leaves=True):
    root = lib.empty("log")
    lib.cyl("trunk", R, L, (0, 0, 0), wood, root, rot=(0, math.radians(90), 0), verts=20, bevel=0.05)
    for sx in (-1, 1):
        lib.cyl("end", R * 0.86, 0.04, (sx * L / 2, 0, 0), ring, root, rot=(0, math.radians(90), 0), verts=20)
    if leaves:
        g = T.P("leaf0", (0.18, 0.72, 0.2), rough=0.5)
        lib.cyl("branch", 0.12, 1.1, (L / 2 - 0.9, 0.5, 0.3), wood, root, rot=(math.radians(-55), 0, 0), verts=10)
        lib.sphere("puff", 0.7, (L / 2 - 0.9, 1.0, 0.75), g, root, segs=18, rings=10)
        lib.cyl("branch", 0.1, 0.9, (L / 2 - 2.2, -0.4, 0.3), wood, root, rot=(math.radians(50), 0, 0), verts=10)
        lib.sphere("puff", 0.55, (L / 2 - 2.2, -0.8, 0.7), g, root, segs=18, rings=10)
    return root


log = make_log()
lib.cyl("stump", 0.45, 0.7, (LX, 4.6, 0.35), wood, verts=20, bevel=0.06)
lib.cyl("stumptop", 0.4, 0.05, (LX, 4.6, 0.72), ring, verts=20)
for k, (dy, z) in enumerate(((-0.42, R), (0.42, R))):          # the wood pile further east
    pl = make_log(leaves=False); pl.location = (PX, PY + dy, z)
lib.box("pilepost", (0.25, 0.25, 1.6), (PX + 3.6, PY, 0.8), T.P("red", T.COL["red"]), bevel=0.06)
lib.box("pilesign", (0.12, 1.9, 0.9), (PX + 3.6, PY, 1.9), T.P("cream", T.COL["cream"]), bevel=0.06)

# 1) the tow truck and the red car are out for a drive; a fallen tree blocks the road
fa = T.go(tow, 6, [(0, 0), (20, 0), (28.6, 0)], speed=6.2)
fb = T.go(car, 14, [(0, 0), (16, 0), (23.6, 0)], speed=6.2)
sfx(6, "truck", dur=7.0); sfx(30, "birds", dur=8.0); sfx(60, "honk")
T.nod(tow, fa, deg=5); sfx(fa - 3, "brake"); T.nod(car, fb, deg=4)
T.hop(tow, fa + 24, n=2, h=0.2); sfx(fa + 24, "question"); sfx(fa + 60, "honk")
C.follow(0, 120, tow, (4.5, -9.0, 2.2), look=(-3.0, 0, 0.8), lens=34)
C.shot(120, fa + 70, (39.5, -5.5, 2.3), (30.5, 0.2, 0.9), (38.8, -5.0, 2.1), (31.0, 0.2, 0.9), lens=32)

# 2) the tow truck tries to push the tree away: too heavy
f1 = fa + 76
push = []
g = T.go(tow, f1, [(31.72, 0)], speed=2.2)
for k in range(2):
    a = g + 8 + k * 96
    T.spin_wheels(tow, a, a + 62, speed=10.0)
    T.body_keys(tow, [(a, 0, 0, 0), (a + 8, -0.03, 2.2, 0), (a + 20, -0.02, 1.6, 0.6), (a + 32, -0.03, 2.2, -0.6), (a + 44, -0.02, 1.8, 0.5),
                      (a + 60, -0.03, 2.0, 0), (a + 72, 0, 0, 0)])
    push.append((a, a + 62))
    sfx(a, "truck", dur=2.6); sfx(a + 10, "slip"); sfx(a + 64, "oops")
f2 = g + 8 + 2 * 96
sfx(f2 + 4, "sad")
g2 = T.go(tow, f2 + 20, [(27.6, 0)], speed=2.6, reverse=True); sfx(f2 + 20, "beep_reverse", dur=1.6)
C.shot(fa + 70, g + 60, (36.5, -6.0, 1.6), (32.6, 0, 0.7), (36.0, -5.6, 1.5), (32.8, 0, 0.7), lens=36)
C.shot(g + 60, f2 + 20, (29.5, -6.8, 2.4), (32.5, 0.2, 0.7), (30.0, -6.4, 2.2), (32.8, 0.2, 0.7), lens=34)

# 3) calling for help; the helpers come over the new bridge
f3 = g2 + 8
T.beacon(tow, (0.15, 0, 2.2), f3, f3 + 150)
for k in range(3):
    sfx(f3 + 6 + k * 16, "honk")
T.hop(car, f3 + 10, n=2, h=0.2)
T.go(car, f3 + 56, [(25.5, -2.5), (27.0, -5.4)], speed=3.0)
T.go(tow, f3 + 66, [(30.0, -2.2), (32.2, -5.6)], speed=3.0)
C.shot(f2 + 20, f3 + 84, (20.0, -7.5, 3.2), (27.0, 0, 1.0), (20.8, -8.0, 3.4), (27.5, -0.5, 1.0), lens=32)
f4 = f3 + 84
T.place(flat, f4, 1.0, 0, 0); T.place(crane, f4, -10.0, 0, 0)
ff = T.go(flat, f4, [(14, 0), (22, 0), (28.2, 0)], speed=6.0)
fc = T.go(crane, f4 + 22, [(12, 0), (16.5, 0.8), (21.0, 4.9), (30.6, 5.6)], speed=6.0)
T.nod(flat, ff, deg=3); T.nod(crane, fc, deg=3); sfx(f4, "truck", dur=7.0); sfx(f4 + 40, "honk"); sfx(ff - 3, "brake")
C.shot(f4, f4 + 96, (19.5, -9.0, 2.4), (10.5, 0, 1.4), (20.0, -9.4, 2.6), (12.0, 0, 1.4), lens=30)
C.shot(f4 + 96, fc + 14, (42.0, -13.0, 7.5), (30.5, 1.0, 1.0), (41.0, -12.5, 7.0), (30.5, 1.0, 1.2), lens=30)

# 4) crane job 1: the log goes onto the long truck
f5 = fc + 16
A1, D1, E1 = T.crane_job(crane, f5, (LX, LY), R + 0.48, (flat.at(f5, (flat.bed_x, 0, 0)).x, 0), flat.bed_z + R + 0.48, pace=1.25)


def lying(f):
    dx = 0.0
    for a, b in push:
        if a <= f <= b + 14:
            dx = 0.16 * math.sin(math.pi * min(1.0, (f - a) / (b + 14 - a))) * (1 + 0.15 * math.sin(f * 1.3))
    return (LX + dx, LY, R), -math.pi / 2


def riding(f):
    p = flat.at(f, (flat.bed_x, 0, 0))
    return (p.x, p.y, flat.bed_z + R), flat.pose(f)[2]


sfx(f5, "ratchet", dur=1.6); sfx(A1 - 22, "ratchet", dur=0.9); sfx(A1, "ding"); sfx(A1 + 4, "ratchet", dur=1.2)
sfx(A1 + 40, "ratchet", dur=2.4); sfx(D1 - 44, "ratchet", dur=1.6); sfx(D1, "thud"); sfx(D1 + 5, "ding", pitch=1.3)
C.shot(fc + 14, A1 + 34, (39.5, 4.8, 2.6), (34.0, 0.4, 1.0), (39.2, 4.4, 3.2), (33.6, 0.6, 2.0), lens=32)
C.shot(A1 + 34, D1 - 44, (42.0, -12.0, 6.2), (30.5, 1.5, 2.8), (41.0, -11.5, 5.6), (30.0, 1.0, 2.6), lens=28)
C.shot(D1 - 44, E1 + 70, (21.0, -8.0, 3.6), (27.0, 0, 2.2), (21.6, -8.4, 3.4), (27.4, 0, 2.0), lens=32)
party((30.0, 0, 4.2), D1 + 22, big=False)
for k, n in enumerate(("car", "tow", "flat")):
    T.hop(V[n], D1 + 24 + k * 6, n=2, h=0.22 if n != "flat" else 0.14)

# 5) off to the wood pile
f6 = E1 + 70
T.go(tow, f6, [(34.5, -2.2), (39, 0), (55, 0), (63.0, -2.0), (69.0, -5.0)], speed=6.0)
T.go(car, f6 + 70, [(31.0, -4.6), (34.5, -3.6), (38.5, -0.6), (44, 0), (50, 0), (58.0, -2.0), (62.5, -5.6)], speed=6.0)
fg = T.go(flat, f6 + 120, [(45, 0), (60.5, 0)], speed=6.0)
fh = T.go(crane, f6 + 30, [(34.5, 4.4), (39.0, 0.4), (44, 0), (49.0, 3.4), (54.0, 5.4), (60.5, 5.6)], speed=6.2)
fh = max(fh, fg)
T.nod(flat, fg, deg=3); T.nod(crane, fh, deg=3)
sfx(f6, "truck", dur=8.0); sfx(f6 + 30, "honk"); sfx(fg - 3, "brake")
C.shot(f6, f6 + 124, (41.5, -11.5, 5.2), (31.5, -2.0, 1.0), (42.5, -11.0, 5.0), (34.0, -1.0, 1.0), lens=30)
C.follow(f6 + 124, f6 + 206, flat, (5.5, -10.0, 3.0), look=(-1.5, 0, 1.4), lens=32)
C.shot(f6 + 206, fh + 12, (73.5, -11.0, 6.5), (62.0, 2.0, 1.0), (72.5, -10.5, 6.0), (62.0, 2.0, 1.2), lens=30)

# 6) crane job 2: the log goes onto the pile
f7 = fh + 14
A2, D2, E2 = T.crane_job(crane, f7, (flat.at(f7, (flat.bed_x, 0, 0)).x, 0), flat.bed_z + R + 0.48, (PX, PY), R + 0.66 + 0.48, pace=1.25)
T.crane_bake(crane, N)
T.hang_bake(crane, log, N, [(A1, D1, riding, 0.0), (A2, D2, (PX, PY, R + 0.66), 0.0)], lying, dz=0.48)
sfx(f7, "ratchet", dur=1.6); sfx(A2, "ding"); sfx(A2 + 4, "ratchet", dur=1.2); sfx(A2 + 40, "ratchet", dur=2.4)
sfx(D2 - 44, "ratchet", dur=1.6); sfx(D2, "thud"); sfx(D2 + 5, "ding", pitch=1.3)
C.shot(fh + 12, A2 + 34, (53.5, -8.0, 3.6), (59.4, 0, 2.4), (54.0, -8.4, 4.0), (59.8, 0.4, 3.0), lens=32)
C.shot(A2 + 34, D2 - 40, (73.0, -7.0, 5.8), (62.5, 5.0, 2.8), (72.4, -6.6, 5.4), (63.0, 6.0, 2.4), lens=28)
C.shot(D2 - 40, D2 + 40, (70.5, 5.0, 2.4), (64.5, 11.0, 1.1), (70.1, 4.6, 2.2), (64.5, 11.0, 1.1), lens=34)

# 7) well done, everybody
f8 = D2 + 40
party((63.5, 1.0, 4.4), f8 + 6)
for k, n in enumerate(("car", "tow", "flat", "crane")):
    T.hop(V[n], f8 + 8 + k * 6, n=3, h=0.26 if n in ("car", "tow") else 0.14)
sfx(f8 + 20, "honk"); sfx(f8 + 44, "honk")
gd = T.go(car, f8 + 50, [(65.0, -6.6), (60.0, -6.6), (56.5, -5.0), (58.0, -3.6), (62.5, -5.6)], speed=5.5)
T.hop(car, gd + 6, n=2, h=0.26); sfx(gd + 6, "boing")
C.shot(f8, N, (62.5, -17.0, 5.5), (63.0, 0.5, 1.4), (62.5, -21.0, 8.0), (63.0, 0.5, 1.4), lens=30)
print("FRAMES", fa, f1, f2, f3, f4, f5, A1, D1, E1, f6, fg, fh, f7, A2, D2, E2, f8, gd)
done("t_ep2")
