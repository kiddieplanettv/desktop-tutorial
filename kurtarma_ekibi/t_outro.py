"""Kapanış: beş araç köprüden geçip garajlarına dönüyor."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_common import *

N = 480
s, deck = setup(N, bridge=True, clear=[(0, 34, -18, -2)])
order = ("car", "tow", "dump", "crane", "flat")
xs = dict(car=22, tow=28, dump=36, crane=45, flat=55)
V = fleet({n: (xs[n], 0, 180) for n in order})
C = Cams()
for k, n in enumerate(order):
    T.go(V[n], 4 + k * 4, [(RX, 0), (-6, 0), (-14, 0)], speed=7.5)
sfx(4, "truck", dur=7.5); sfx(30, "honk"); sfx(80, "honk"); sfx(130, "honk")
C.shot(0, 196, (19.5, -10.5, 3.8), (12.5, 0, 1.3), (18.5, -10.0, 3.4), (11.0, 0, 1.3), lens=30)
CUT = 196
for k, n in enumerate(order):
    T.place(V[n], CUT, HX[n] + 16.0 + k * 3.0, 0, 180)
    f = T.drive_path(V[n], CUT + 4 + k * 6, CUT + 96 + k * 6, [(HX[n] + 4.0, 0.3), (HX[n], 4.6)])
    T.nod(V[n], f, deg=3)
sfx(CUT + 4, "truck", dur=4.5)
for k, n in enumerate(order):
    for j in range(2):
        T.hop(V[n], 330 + k * 6 + j * 56, n=2, h=0.26 if n in ("car", "tow") else 0.15)
T.crane_bake(V["crane"], N)
title = lib.text("title", "GÖRÜŞÜRÜZ!", 3.6, (-30, 2.0, 8.0), T.P("title", (1.0, 0.82, 0.05), emit=0.35), rot=(math.radians(78), 0, 0), extrude=0.35, bevel=0.06)
lib.pop_in(title, 326, dur=12)
lib.confetti((-30, 2, 9.0), 332, n=90, spread=15.0, height=6.0)
lib.confetti((-30, 2, 9.0), 396, n=90, spread=15.0, height=6.0, seed=3)
lib.balloons((-30, 3, 1.0), 340, n=9, rise=14, dur=140)
sfx(330, "yay"); sfx(346, "tada"); sfx(360, "honk"); sfx(392, "honk"); sfx(400, "confetti")
C.shot(CUT, N, (-30, -34, 12.0), (-30, 7, 4.0), (-30, -31.0, 9.6), (-30, 6, 4.8), lens=30)
done("t_outro")
