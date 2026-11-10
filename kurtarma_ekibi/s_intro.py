"""Giriş (20 s): fly into town, title, everyone says hello, the vehicles parade past."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from story import *

N = 480
W = build_world(N, farm=False)
C1 = camera("C1", [(0, (70, -40, 32), (70, 20, 22)), (60, (70, -26, 16), (70, 12, 8)), (110, (70, -9.0, 4.2), (70, 9, 3.0))], lens=30)
cut(0, C1)
sfx(0, "whoosh"); sfx(60, "whoosh", vol=0.6); sfx(0, "birds", dur=N / FPS)

tm = [mat(f"title{i}", c, rough=0.25, emit=0.3) for i, c in enumerate(
    [C["red"], C["orange"], C["yellow"], C["green"], C["blue"], C["purple"], C["pink"]])]
lets = letters_row("KAHRAMAN KASABA", 1.35, 70.0, 7.0, 4.6, tm, prefix="T")
for i, o in enumerate(lets):
    f = 118 + i * 5
    x = o.location.x
    key(o, "scale", 0, (0.001,) * 3)
    keys(o, "scale", [(f - 1, (0.001,) * 3), (f + 6, (1.3,) * 3), (f + 10, (1, 1, 1))])
    sfx(f, "pop", vol=0.4, pitch=1.0 + i * 0.03)
    for ff in range(185 + i * 2, 225, 20):
        keys(o, "location", [(ff, (x, 7.0, 4.6)), (ff + 8, (x, 7.0, 5.1)), (ff + 16, (x, 7.0, 4.6))])
    keys(o, "scale", [(226 + i, (1, 1, 1)), (234 + i, (0.001,) * 3)])
sfx(185, "tada")
C2 = camera("C2", [(110, (70, -9.0, 4.2), (70, 9, 3.4)), (230, (70, -7.5, 3.8), (70, 9, 3.2))], lens=30)
cut(110, C2)

roster = [("ada", 63.0), ("emir", 65.2), ("elif", 67.4), ("deniz", 69.6), ("pamuk", 71.8), ("cimcime", 74.0), ("sami", 76.4)]
snd = {"pamuk": "baa", "cimcime": "monkey", "sami": "sneak_short"}
cs = []
for k, (nm, x) in enumerate(roster):
    c = cd.char(nm, (x, 8.6, 0))
    f = 236 + k * 22
    c.pop(f)
    c.cheer(f + 8, n=2)
    c.wiggle(f + 40, N, a=7, period=26)
    sfx(f, "pop"); sfx(f + 4, snd.get(nm, "giggle"), vol=0.6)
    cs.append(c)
C3 = camera("C3", [(230, (62.5, 1.8, 1.6), (63.5, 8.6, 1.0)), (395, (76.0, 1.8, 1.6), (75.5, 8.6, 1.0))], lens=30)
cut(230, C3)

# parade on the road
vs = [(make_police(), "burak"), (make_firetruck(), "kemal"), (make_recycler(), "murat")]
for k, (v, who) in enumerate(vs):
    driver_card(v, who)
    x0 = 40.0 - k * 7.5
    v.root.location = (x0, NORTH_LANE, 0)
    drive(v, [(390, (x0, NORTH_LANE), 0), (480, (x0 + 38, NORTH_LANE), 0)])
    flash_lights(v, 390, 480)
    roll_wheels(v, 0, N)
sfx(396, "siren_police", dur=1.5, vol=0.6); sfx(420, "siren_fire", dur=1.4, vol=0.6); sfx(445, "beep_reverse", dur=1.0, vol=0.6)
for c in cs:
    c.cheer(420, n=3)
sfx(425, "yay", vol=0.8)
C4 = camera("C4", [(395, (66.0, -9.5, 2.6), (68, 6, 1.6)), (480, (70.0, -10.0, 2.8), (70, 6, 1.6))], lens=28)
cut(395, C4)
finish(N, "k_intro")
