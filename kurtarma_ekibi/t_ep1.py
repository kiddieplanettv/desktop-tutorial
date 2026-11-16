"""Bölüm 1 – Köprü: kırmızı araba dereyi geçemiyor; vinç ve uzun kamyon yeni köprüyü yerine koyuyor."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_common import *

N = 1800
s, deck = setup(N, bridge=False, clear=[(-10, 32, -18, -2)], pads=[(-6, 9.4, 2.0, 7.4), (-6, 9.4, -7.4, -2.0)])
V = fleet()
car, crane, flat, tow, dump = V["car"], V["crane"], V["flat"], V["tow"], V["dump"]
C = Cams()
DZ = flat.bed_z + 0.33

# 1) the little red car sets off and reaches the river: no bridge!
fa = T.go(car, 10, exit_pts("car") + [(-20, 0), (0, 0), (8.0, 0)], speed=7.5)
sfx(10, "honk"); sfx(24, "truck", dur=6.0); sfx(60, "birds", dur=8.0)
T.nod(car, fa, deg=5); sfx(fa - 2, "brake")
T.hop(car, fa + 22, n=2, h=0.22); sfx(fa + 22, "question")
T.hop(car, fa + 70, n=1, h=0.15); sfx(fa + 66, "honk"); sfx(fa + 80, "honk")
fb = T.go(car, fa + 100, [(3.6, 0)], speed=3.0, reverse=True); sfx(fa + 100, "beep_reverse", dur=1.5)
C.shot(0, 96, (-52, -16, 8.0), (-40, 6, 1.5), (-49, -14, 7.0), (-39, 4, 1.2), lens=32)
C.follow(96, fa - 40, car, (3.8, -8.0, 2.0), look=(0.8, 0, 0.7), lens=38)
C.shot(fa - 40, fa + 14, (2.0, -7.5, 2.4), (9.5, 0, 0.8), (3.0, -7.0, 2.2), (10.0, 0, 0.8), lens=34)
C.shot(fa + 14, fb + 10, (18.0, -1.3, 1.7), (8.4, 0, 1.0), (17.4, -1.1, 1.9), (7.0, 0, 1.0), lens=40)

# 2) help sets off: the long truck (with a new bridge deck) and the crane
f1 = fb + 10
T.drive_path(flat, f1 + 6, f1 + 108, exit_pts("flat") + [(4, 0)])
T.drive_path(crane, f1 + 30, f1 + 108, exit_pts("crane") + [(-10, 0)])
sfx(f1 + 6, "truck", dur=6.0); sfx(f1 + 20, "honk"); sfx(f1 + 44, "honk")
C.shot(f1, f1 + 110, (-8, -16, 6.5), (-19, 6, 2.0), (-6, -14, 5.5), (-16, 3, 1.8), lens=30)
f2 = f1 + 110
T.place(flat, f2, -20, 0, 0); T.place(crane, f2, -31, 0, 0)
T.drive_path(flat, f2, f2 + 170, [(-7, 0), (-4, 0), (0.5, -4.2), (6.0, -4.6)])
T.drive_path(crane, f2 + 4, f2 + 190, [(-12, 0), (-4.5, 0), (0.5, 4.2), (8.0, 4.6)])
T.nod(flat, f2 + 170, deg=3); T.nod(crane, f2 + 190, deg=3); sfx(f2 + 168, "brake"); sfx(f2 + 60, "truck", dur=5.0)
C.follow(f2, f2 + 96, flat, (7.0, -11.0, 3.2), look=(-2.5, 1.0, 1.2), lens=30)
C.shot(f2 + 96, f2 + 200, (18.0, -11.5, 6.8), (7.5, 0, 1.2), (17.0, -11, 6.2), (7.5, 0, 1.4), lens=30)

# 3) crane work: lift the deck off the truck, swing it over the river, lower it
f3 = f2 + 204
src = flat.at(f3, (flat.bed_x, 0, 0))
F_ATT, F_DOWN, F_END = T.crane_job(crane, f3, (src.x, src.y), DZ + 0.05, (RX, 0), 0.08, pace=1.25)
T.crane_bake(crane, N)
def on_truck(f):
    p = flat.at(f, (flat.bed_x, 0, 0))
    return (p.x, p.y, DZ), flat.pose(f)[2]
T.hang_bake(crane, deck, N, [(F_ATT, F_DOWN, (RX, 0, 0.03), 0.0)], on_truck)
sfx(f3, "ratchet", dur=1.6); sfx(F_ATT - 22, "ratchet", dur=0.9); sfx(F_ATT, "ding")
sfx(F_ATT + 4, "ratchet", dur=1.2); sfx(F_ATT + 40, "ratchet", dur=2.4); sfx(F_DOWN - 44, "ratchet", dur=1.6)
sfx(F_DOWN, "thud"); sfx(F_DOWN + 5, "ding", pitch=1.3); sfx(F_DOWN + 20, "ratchet", dur=1.4)
C.shot(f3, F_ATT + 30, (-1.0, -12.5, 3.6), (5.5, -3.0, 2.4), (0.0, -12.0, 4.2), (6.0, -2.5, 3.2), lens=32)
C.shot(F_ATT + 30, F_DOWN - 40, (20.5, -11.0, 5.6), (9.0, 0.5, 3.2), (19.5, -10.5, 5.0), (10.0, 0.3, 2.6), lens=28)
C.shot(F_DOWN - 40, F_END, (19.0, -8.5, 3.4), (11.0, 0, 1.0), (18.2, -8.0, 3.0), (11.0, 0, 0.9), lens=32)
T.hop(flat, F_DOWN + 26, n=1, h=0.15); T.hop(crane, F_END + 4, n=1, h=0.12); sfx(F_DOWN + 28, "honk")

# 4) the red car tries the new bridge, then everybody crosses
f4 = F_END + 8
fc = T.go(car, f4, [(8, 0), (RX, 0), (20.0, 0)], speed=3.6); sfx(f4, "truck", dur=3.5)
T.hop(car, fc + 8, n=3, h=0.3)
party((20.0, 0, 3.6), fc + 10)
C.shot(f4, fc - 28, (21.5, -1.7, 1.4), (10.0, 0, 0.9), (21.9, -1.8, 1.5), (13.0, 0, 0.9), lens=36)
C.shot(fc - 28, fc + 96, (28.5, -9.5, 3.8), (15.0, 0.5, 1.2), (27.0, -9.0, 3.4), (15.0, 0.5, 1.2), lens=30)
T.hop(flat, fc + 14, n=2, h=0.16); T.hop(crane, fc + 18, n=2, h=0.14); sfx(fc + 16, "honk")
f5 = fc + 96
g = T.go(car, f5, [(40, 0), (70, 0)], speed=6.0)
T.drive_path(flat, f5 + 10, f5 + 150, [(2.0, -3.0), (-3.5, -0.3), (-9, 0)], reverse=True); sfx(f5 + 10, "beep_reverse", dur=2.0)
T.go(flat, f5 + 156, [(RX, 0), (40, 0), (72, 0)], speed=6.0)
T.drive_path(crane, f5 + 150, f5 + 260, [(3.0, 3.6), (-2.0, 0.6), (-6.5, 0)], reverse=True)
T.go(crane, f5 + 266, [(RX, 0), (40, 0), (70, 0)], speed=6.0)
sfx(f5 + 156, "truck", dur=6.0); sfx(f5 + 200, "honk"); sfx(f5 + 300, "honk")
C.shot(f5, f5 + 190, (1.5, -9.5, 3.0), (6.0, -1.5, 1.2), (3.0, -9.0, 2.8), (9.0, -0.5, 1.2), lens=30)
C.shot(f5 + 190, f5 + 300, (16.5, -6.5, 1.5), (11.0, 0, 1.2), lens=30)
C.shot(f5 + 300, N, (30.0, -12.0, 7.5), (14.0, 0, 1.0), (33.0, -13.0, 9.0), (16.0, 0, 1.0), lens=30)
T.crane_bake(crane, N)
print("FRAMES", fa, fb, f1, f2, f3, F_ATT, F_DOWN, F_END, f4, fc, f5, f5 + 300)
done("t_ep1")
