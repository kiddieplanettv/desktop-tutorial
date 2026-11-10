"""Final (20 s): everyone celebrates in the park and waves goodbye."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from story import *

N = 480
W = build_world(N, farm=False)
cam = camera("cam", [(0, (64.0, 16.5, 2.2), (68.5, 8.2, 1.3)), (240, (70.0, 17.0, 2.4), (70.0, 8.2, 1.4)),
                     (420, (76.0, 16.5, 2.2), (71.5, 8.2, 1.3)), (479, (76.5, 17.0, 8.0), (71.0, 6.0, 9.0))], lens=28)
cut(0, cam)
vs = [(make_police(), "burak", 64.0), (make_firetruck(), "kemal", 71.0), (make_recycler(), "murat", 78.5)]
for v, who, x in vs:
    v.root.location = (x, NORTH_LANE, 0)
    v.root.rotation_euler.z = math.radians(180)
    dc = driver_card(v, who)
    dc.wiggle(20, N, a=7, period=28)
    flash_lights(v, 0, N)
roster = [("ada", 64.6), ("emir", 66.2), ("elif", 67.8), ("deniz", 69.4), ("pamuk", 71.0), ("cimcime", 72.4), ("sami", 74.2)]
cs = []
for k, (nm, x) in enumerate(roster):
    c = cd.char(nm, (x, 8.6 + (k % 2) * 0.5, 0))
    cs.append(c)
mama = cd.char("pamuk", (75.8, 9.2, 0), height=1.3, tag="mama")
cs.append(mama)
for wave, f0 in enumerate([30, 180, 320]):
    for i, c in enumerate(cs):
        c.cheer(f0 + i * 5, n=2)
    sfx(f0, "yay", vol=0.8)
for i, (x, f) in enumerate([(66, 40), (74, 120), (70, 200), (67, 300), (73, 360)]):
    confetti((x, 7.5, 1.0), f, n=45, seed=200 + i)
    sfx(f, "confetti", vol=0.8)
balloons((67, 7.8, 0.5), 80, n=6, seed=31)
balloons((73, 7.8, 0.5), 230, n=6, seed=32)
sfx(80, "balloon"); sfx(230, "balloon")
sfx(60, "siren_police", dur=0.9, vol=0.5); sfx(90, "siren_fire", dur=0.9, vol=0.5); sfx(120, "truck_beep", dur=0.9, vol=0.5)
sfx(70, "baa", vol=0.6); sfx(140, "monkey", vol=0.6)
tm = [mat(f"bye{i}", c, rough=0.25, emit=0.3) for i, c in enumerate(
    [C["red"], C["orange"], C["yellow"], C["green"], C["blue"], C["purple"], C["pink"]])]
lets = letters_row("HOŞÇA KALIN!", 1.3, 70.0, 7.0, 3.4, tm, prefix="B")
for k, o in enumerate(lets):
    f = 250 + k * 5
    o.location.x = 140.0 - o.location.x
    x = o.location.x
    o.rotation_euler.z = math.radians(180)
    key(o, "scale", 0, (0.001,) * 3)
    keys(o, "scale", [(f - 1, (0.001,) * 3), (f + 6, (1.3,) * 3), (f + 10, (1, 1, 1))])
    sfx(f, "pop", vol=0.4, pitch=1.0 + k * 0.04)
    for ff in range(310 + k * 2, 450, 24):
        keys(o, "location", [(ff, (x, 7.0, 3.4)), (ff + 10, (x, 7.0, 3.85)), (ff + 20, (x, 7.0, 3.4))])
sfx(310, "tada")
for c in cs:
    c.wiggle(390, N, a=12, period=22)
finish(N, "k_finale")
