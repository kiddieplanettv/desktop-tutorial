"""Giriş: beş araç garajlarından çıkıp sıralanıyor."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_common import *

N = 240
s, deck = setup(N, bridge=False)
V = fleet()
C = Cams()
order = ("car", "tow", "dump", "crane", "flat")
for k, n in enumerate(order):
    f0 = 8 + k * 16
    T.drive_path(V[n], f0, f0 + 70, [(HX[n], 5.2)])
    sfx(f0, "honk")
    T.nod(V[n], f0 + 70, deg=3)
T.crane_bake(V["crane"], N)
for k, n in enumerate(order):
    T.hop(V[n], 168 + k * 6, n=2, h=0.26 if n in ("car", "tow") else 0.16)
sfx(8, "truck", dur=5.0); sfx(168, "yay"); sfx(190, "tada")
title = lib.text("title", "MİNİK USTALAR", 3.4, (-30, 2.0, 7.6), T.P("title", (1.0, 0.82, 0.05), emit=0.35), rot=(math.radians(78), 0, 0), extrude=0.35, bevel=0.06)
lib.pop_in(title, 120, dur=12)
lib.confetti((-30, 2, 8.5), 172, n=80, spread=14.0, height=6.0)
C.shot(0, 110, (-30, -30, 12.5), (-30, 8, 3.0), (-30, -26, 10.5), (-30, 7, 3.2), lens=30)
C.shot(110, N, (-30, -28.5, 7.8), (-30, 6, 4.4), (-30, -26.5, 7.2), (-30, 6, 4.4), lens=30)
done("t_intro")
