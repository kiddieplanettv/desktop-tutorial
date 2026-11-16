"""Bölüm 3 – Çamur: kırmızı araba topun peşinden çamura saplanıyor; çekici çekiyor, damper kum döküyor."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_common import *

N = 2040
MX, MY = 45.0, -9.0
s, deck = setup(N, bridge=True, clear=[(8, 60, -24, -2)], dirt=[(26, 58, -15.5, -2.0)])
V = fleet(dict(car=(15, 0, 0)))
car, crane, flat, tow, dump = V["car"], V["crane"], V["flat"], V["tow"], V["dump"]
C = Cams()
mud = lib.sphere("deco_mud", 1.0, (MX, MY, 0.0), T.P("mud", (0.36, 0.22, 0.1), rough=0.35, spec=0.6), scale=(2.9, 2.3, 0.07), segs=40, rings=12)
lib.sphere("deco_mud2", 1.0, (MX + 0.2, MY, 0.02), T.P("mud2", (0.28, 0.16, 0.07), rough=0.25, spec=0.7), scale=(2.0, 1.5, 0.06), segs=40, rings=12)
b = T.ball()
b.location = (35.0, -4.5, b["r"])

# 1) a ball on the meadow: the red car plays with it, the ball rolls over the mud... and the car gets stuck
f1 = T.go(car, 6, [(26, 0), (30.5, -2.6), (33.9, -4.3)], speed=6.0)
sfx(6, "truck", dur=4.0); sfx(20, "birds", dur=9.0)
T.roll(b, [(f1 - 2, 35.0, -4.5), (f1 + 44, 40.0, -7.0)], hop=0.25); sfx(f1 - 2, "kick"); sfx(f1 + 4, "boing")
T.hop(car, f1 + 8, n=2, h=0.24); sfx(f1 + 10, "yay", vol=0.6)
f2 = T.go(car, f1 + 44, [(38.9, -6.5)], speed=4.5)
T.roll(b, [(f2 - 2, 40.0, -7.0), (f2 + 60, 48.9, -9.6)], hop=0.2); sfx(f2 - 2, "kick")
f3 = T.go(car, f2 + 22, [(42.0, -8.3), (44.6, -9.0)], speed=4.2)
T.body_keys(car, [(f3 - 8, 0, 0, 0), (f3 + 6, -0.12, 3.0, 0), (f3 + 26, -0.2, 2.0, 1.5)])
sfx(f3 - 4, "splash"); sfx(f3 + 8, "oops")
T.burst((44.9, -9.0, 0.1), f3 - 4, n=16, seed=3)
att = []
for k in range(2):
    a = f3 + 50 + k * 80
    T.spin_wheels(car, a, a + 54, speed=11.0)
    T.body_keys(car, [(a, -0.2, 2.0, 1.5), (a + 10, -0.21, 2.6, -1.5), (a + 22, -0.2, 1.8, 1.8), (a + 34, -0.22, 2.6, -1.2), (a + 54, -0.2, 2.0, 1.5)])
    T.burst((43.8, -9.5, 0.1), a + 4, n=12, seed=10 + k); T.burst((43.8, -8.4, 0.1), a + 20, n=12, seed=20 + k)
    sfx(a, "truck", dur=2.2); sfx(a + 6, "slip"); sfx(a + 26, "splash")
f4 = f3 + 50 + 160
sfx(f4 + 4, "sad")
for k in range(3):
    sfx(f4 + 44 + k * 16, "honk")
C.follow(0, f1 - 10, car, (4.0, -9.0, 2.2), look=(1.0, 0, 0.7), lens=36)
C.shot(f1 - 10, f3 - 30, (38.0, -18.0, 4.6), (38.5, -6.0, 0.6), (41.5, -18.0, 4.6), (42.5, -7.5, 0.6), lens=32)
C.shot(f3 - 30, f3 + 50, (49.0, -13.8, 1.8), (44.6, -9.0, 0.6), (48.6, -13.4, 1.7), (44.6, -9.0, 0.6), lens=34)
C.shot(f3 + 50, f4 + 90, (41.2, -13.2, 2.2), (44.6, -9.0, 0.6), (41.8, -13.6, 2.4), (44.6, -9.0, 0.6), lens=34)

# 2) the tow truck comes and pulls: the wheels just spin
f5 = f4 + 90
T.place(tow, f5, 20.0, 0, 0)
T.beacon(tow, (0.15, 0, 2.2), f5, f5 + 260)
f6 = T.go(tow, f5, [(30, -1.5), (36, -3.5), (40.0, -5.2), (41.4, -7.4), (40.6, -8.8), (39.4, -9.0)], speed=5.5)
sfx(f5, "truck", dur=5.0); sfx(f5 + 30, "honk"); T.nod(tow, f6, deg=3)
RA = f6 + 24                                   # rope on
sfx(RA, "ding")
g1 = T.drive_path(tow, RA + 16, RA + 44, [(39.05, -9.0)])
T.spin_wheels(tow, RA + 44, RA + 110, speed=10.0)
T.body_keys(tow, [(RA + 44, 0, 0, 0), (RA + 56, -0.02, -2.0, 0.6), (RA + 70, -0.02, -1.4, -0.6), (RA + 86, -0.02, -2.0, 0.5), (RA + 110, 0, 0, 0)])
T.body_keys(car, [(RA + 40, -0.2, 2.0, 1.5), (RA + 60, -0.17, 0.5, 0.5), (RA + 100, -0.17, 0.8, -0.6), (RA + 124, -0.2, 2.0, 1.5)])
T.burst((40.6, -9.0, 0.1), RA + 50, n=10, col=(0.3, 0.7, 0.2), seed=31, name="grassbit")
sfx(RA + 40, "truck", dur=3.0); sfx(RA + 50, "slip"); sfx(RA + 112, "oops")
g2 = T.drive_path(tow, RA + 116, RA + 140, [(39.4, -9.0)], reverse=True)
f7 = RA + 150
for k in range(3):
    sfx(f7 + k * 16, "honk")
C.follow(f5, f5 + 90, tow, (4.5, -8.5, 2.3), look=(-1.0, 0, 0.8), lens=34)
C.shot(f5 + 90, RA + 10, (45.0, -16.0, 4.2), (42.0, -9.0, 0.8), (44.0, -15.5, 3.8), (42.0, -9.0, 0.8), lens=32)
C.shot(RA + 10, f7 + 50, (42.3, -13.0, 1.5), (42.0, -9.0, 0.9), (41.6, -13.4, 1.7), (41.6, -9.0, 0.9), lens=34)

# 3) the dump truck brings sand
f8 = f7 + 50
T.place(dump, f8, 22.0, 0, 0)
dump.sand.scale = (1.75, 1.0, 0.75)
f9 = T.go(dump, f8, [(40, 0), (49.5, -0.5)], speed=6.0)
f10 = T.go(dump, f9 + 10, [(46.2, -4.6)], speed=2.4, reverse=True)
sfx(f8, "truck", dur=6.0); sfx(f9 + 10, "beep_reverse", dur=2.4); T.nod(dump, f9, deg=3)
TA = f10 + 14
TE = T.tip(dump, TA, TA + 46, deg=50, hold=56)
lib.keys(dump.sand, "scale", [(TA + 20, (1.75, 1.0, 0.75)), (TA + 80, (0.9, 0.8, 0.3)), (TA + 96, (0.001, 0.001, 0.001))])
lib.keys(dump.sand, "location", [(TA + 20, (1.1, 0, 0.95)), (TA + 90, (-0.3, 0, 0.7))])
pile = lib.sphere("sandpile", 1.0, (44.25, -7.2, 0.0), T.P("sandpile", (0.98, 0.8, 0.42), rough=0.85, spec=0.1), scale=(0.001, 0.001, 0.001), segs=32, rings=16)
lib.keys(pile, "scale", [(TA + 30, (0.001, 0.001, 0.001)), (TA + 96, (1.5, 1.4, 0.95)), (TE + 10, (1.5, 1.4, 0.95)), (TE + 80, (3.1, 2.5, 0.1))])
lib.keys(pile, "location", [(TE + 10, (44.25, -7.2, 0.0)), (TE + 80, (44.8, -8.9, 0.02))])
T.burst((44.3, -7.2, 0.3), TA + 40, n=14, col=(0.98, 0.8, 0.42), seed=41, name="sandbit", height=0.8)
T.burst((44.3, -7.2, 0.3), TA + 62, n=14, col=(0.98, 0.8, 0.42), seed=42, name="sandbit", height=0.8)
sfx(TA, "ratchet", dur=1.8); sfx(TA + 34, "whoosh"); sfx(TA + 50, "crackle", dur=2.0); sfx(TE - 40, "ratchet", dur=1.6); sfx(TE + 12, "sparkle")
f11 = T.go(dump, TE + 6, [(49.8, -2.0), (53.0, -3.5)], speed=3.5)
C.follow(f8, f8 + 84, dump, (5.5, -9.5, 3.0), look=(0, 0, 1.4), lens=32)
C.shot(f8 + 84, TA - 6, (54.5, -11.0, 5.0), (46.5, -5.5, 1.4), (53.5, -10.5, 4.6), (46.0, -6.0, 1.4), lens=30)
C.shot(TA - 6, TE - 30, (39.2, -3.4, 2.8), (45.0, -6.6, 1.7), (39.8, -3.0, 2.6), (45.0, -6.8, 1.5), lens=32)
C.shot(TE - 30, TE + 100, (45.0, -17.0, 6.0), (45.0, -8.2, 0.3), (45.0, -16.0, 5.4), (45.0, -8.4, 0.3), lens=32)

# 4) second pull: out it comes
f12 = TE + 100
T.drive_path(tow, f12, f12 + 96, [(35.2, -9.0)])
T.drive_path(car, f12 + 6, f12 + 100, [(40.5, -9.0)], reverse=True)
fr_ = list(range(f12 + 6, f12 + 56))
bake(car.body, "location", fr_, [(0, 0, -0.2 * (1 - ((f - f12 - 6) / 49.0) ** 2 * (3 - 2 * (f - f12 - 6) / 49.0))) for f in fr_])
bake(car.body, "rotation_euler", fr_, [(0, math.radians(2.0) * (1 - (f - f12 - 6) / 49.0), 0) for f in fr_])
sfx(f12, "truck", dur=4.0); sfx(f12 + 40, "pop"); party((41.0, -9.0, 3.6), f12 + 104)
RB = f12 + 112
T.rope("rope", lambda f: tow.at(f, tow.hook), lambda f: car.at(f, (-1.28, 0, 0.62 + (car.body.location.z if False else 0))), RA, RB)
for k, n in enumerate(("car", "tow", "dump")):
    T.hop(V[n], f12 + 108 + k * 6, n=3, h=0.26 if n != "dump" else 0.14)
sfx(f12 + 130, "honk"); sfx(f12 + 150, "honk")
C.shot(f12, f12 + 190, (42.0, -17.0, 3.6), (42.0, -9.0, 0.8), (39.5, -17.0, 3.6), (39.5, -9.0, 0.8), lens=32)

# 5) the ball is still behind the mud: round it goes (not through the mud this time!)
f13 = f12 + 190
f14 = T.go(car, f13, [(42.5, -12.9), (47.5, -13.6), (51.2, -11.6), (50.3, -9.9)], speed=5.0)
T.roll(b, [(f14 - 2, 48.9, -9.6), (f14 + 50, 46.4, -5.6), (f14 + 110, 40.5, -3.6)], hop=0.2); sfx(f14 - 2, "kick"); sfx(f14 + 4, "boing")
T.hop(car, f14 + 10, n=2, h=0.24)
f15 = T.go(car, f14 + 60, [(49.5, -6.5), (45.0, -4.0), (41.9, -3.7)], speed=5.0)
T.roll(b, [(f15 - 2, 40.5, -3.6), (f15 + 50, 36.0, -2.9)], hop=0.15); sfx(f15 - 2, "kick")
T.hop(car, f15 + 10, n=2, h=0.24); sfx(f15 + 10, "yay", vol=0.7)
T.go(tow, f14 + 70, [(33.5, -6.0), (36.0, -2.2), (42, 0), (66, 0)], speed=5.5)
T.go(dump, f14 + 10, [(57.0, -1.5), (62, 0), (100, 0)], speed=5.5)
sfx(f14 + 30, "truck", dur=6.0); sfx(f15 + 40, "honk"); sfx(f15 + 70, "honk")
C.shot(f13, f14 + 60, (47.5, -20.0, 5.8), (47.0, -9.5, 0.5), (46.5, -19.5, 5.6), (46.0, -8.5, 0.5), lens=32)
C.shot(f14 + 60, N, (40.0, -15.5, 4.2), (42.5, -4.0, 0.8), (38.0, -19.0, 6.5), (41.5, -4.0, 0.8), lens=32)
T.crane_bake(crane, N)
print("FRAMES", f1, f2, f3, f4, f5, f6, RA, f7, f8, f9, f10, TA, TE, f12, RB, f13, f14, f15)
done("t_ep3")
