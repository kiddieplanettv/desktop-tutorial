"""Bölüm 3 – Temiz Park (70 s): kids and Geri Dönüşümcü Murat sort the picnic litter into recycling bins."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from story import *
from cards import smooth

N = 1680
W = build_world(N)
FACE = math.radians(-90)
kids = dict(ada=cd.char("ada", (66.8, 9.2, 0)), elif_=cd.char("elif", (68.4, 9.8, 0)),
            deniz=cd.char("deniz", (72.6, 9.8, 0)), emir=cd.char("emir", (74.2, 9.2, 0)))
rec = make_recycler()
rec.root.location = (20.0, NORTH_LANE, 0)
mur_cab = driver_card(rec, "murat")
binroot, bns = cd.bins((70.5, 7.0, 0), rot=math.radians(-90))
key(binroot, "scale", 0, (0.001,) * 3)
mur = cd.char("murat", (70.5, 7.75, 0.42), height=1.3, shadow=False)
mur.show(0, False)
# picnic blanket + basket
box("blanket", (2.4, 1.8, 0.03), (70.4, 11.4, 0.08), mat("blanket", (0.95, 0.3, 0.35), rough=0.8), bevel=0)
for i in range(4):
    box("blstripe", (2.42, 0.18, 0.035), (70.4, 10.7 + i * 0.45, 0.085), mat("blwhite", (1, 1, 1), rough=0.8), bevel=0)
box("basket", (0.6, 0.45, 0.35), (71.2, 11.7, 0.25), mat("basketw", (0.75, 0.5, 0.25), rough=0.7), bevel=0.06)
sfx(0, "birds", dur=N / FPS)

# litter: (kind, pos, kid, bin)
rnd = random.Random(5)
items = []
spots = {"ada": (66.2, 10.6), "elif_": (68.2, 11.4), "deniz": (72.8, 11.2), "emir": (74.6, 10.6)}
kinds = [("paper", 0), ("bottle", 1), ("jar", 2)]
for r in range(3):
    for kname in ("ada", "elif_", "deniz", "emir"):
        kind, b = kinds[(r + len(items)) % 3]
        sx, sy = spots[kname]
        p = (sx + rnd.uniform(-0.8, 0.8), sy + rnd.uniform(-0.6, 0.6), 0.06)
        items.append((cd.litter(kind, p), kname, b))

# --- 0-150: messy park, kids are sad
for k in kids.values():
    k.tilt(10, 140, rnd.choice([-8, 8]))
cd.emote(kids["ada"], "?", 20, 80); cd.emote(kids["emir"], "?", 30, 90)
cd.emote(kids["elif_"], "tear", 70, 140); cd.emote(kids["deniz"], "tear", 75, 140)
sfx(40, "sad")
WI = camera("WI", [(0, (70.5, 1.0, 2.6), (70.5, 10.5, 0.8)), (150, (70.5, 2.2, 2.4), (70.5, 10.5, 0.7))], lens=26)
cut(0, WI)

# --- 150-330: recycling truck arrives
drive(rec, [(140, (20.0, NORTH_LANE), 0), (320, (64.5, NORTH_LANE), 0)])
flash_lights(rec, 150, 340, period=14)
sfx(150, "truck", dur=170 / FPS)
sfx(300, "beep_reverse", dur=1.2)
cd.emote(mur_cab, "star", 250, 320, dz=0.12, size=0.38)
TR = follow_cam("TR", rec.root, 150, 330, offset=(5.0, -8.5, 2.2), look_offset=(0, 0.5, 1.4), lens=30)
cut(150, TR)

# --- 330-420: Murat brings the bins, kids gather
pop_in(binroot, 334, 10)
sfx(334, "magic")
mur_cab.show(330, False); mur.show(330, True)
cd.emote(mur, "!", 345, 400)
mur.hop(340, n=2, h=0.25)
for k in kids.values():
    k.tilt(150, 150, 0)
for k in ("ada", "emir"):
    kids[k].hop(360, n=2)
BI = camera("BI", [(330, (70.5, 2.6, 1.6), (70.5, 8.0, 1.2)), (420, (70.5, 3.0, 1.55), (70.5, 8.0, 1.15))], lens=30)
cut(330, BI)

# --- 420-1140: sorting game, 12 items, 60 frames each
binx = [69.5, 70.5, 71.5]
f = 420
cams = []
for i, (o, kname, b) in enumerate(items):
    kid = kids[kname]
    kp = kid._pos(f)
    hand = Vector((kp.x, kp.y - 0.25, 0.75))
    start = Vector(o.location)
    fr = list(range(f, f + 13))
    bake(o, "location", fr, [tuple(start.lerp(hand, smooth((x - f) / 12))) for x in fr])
    kid.hop(f, n=1, h=0.2)
    o.location = hand
    cd.throw(o, f + 22, f + 44, (binx[b], 7.0, 1.2), h=1.3)
    lid = bns[b]["lid"]
    keys(lid, "rotation_euler", [(f + 30, (0, 0, 0)), (f + 36, (0, math.radians(-105), 0)), (f + 48, (0, math.radians(-105), 0)), (f + 54, (0, 0, 0))])
    sfx(f + 22, "whoosh", vol=0.5)
    sfx(f + 44, "ding", pitch=1.0 + 0.05 * (i % 4))
    stars_burst((binx[b], 6.9, 1.6), f + 44, n=5, face_rot=FACE, radius=0.8)
    mur.hop(f + 44, n=1, h=0.15)
    kid.cheer(f + 46, n=1)
    f += 60
    if i % 3 == 0:
        cams.append(f - 60)
alt = [((70.5, 2.6, 1.6), (70.5, 8.6, 1.0), 28), ((66.6, 4.4, 1.4), (67.8, 9.4, 0.9), 32),
       ((74.4, 4.4, 1.4), (73.2, 9.4, 0.9), 32), ((70.5, 3.4, 1.5), (70.5, 8.4, 1.0), 26)]
for j, f0 in enumerate(cams):
    cl, tl, ln = alt[j % 4]
    c = camera(f"SO{j}", [(f0, cl, tl), (f0 + 180, tuple(Vector(cl) + Vector((0, 0.5, 0))), tl)], lens=ln)
    cut(f0, c)

# --- 1140-1300: the park blooms
rnd2 = random.Random(9)
for k in range(16):
    fl = cd.flower((rnd2.uniform(64, 77), rnd2.uniform(8.2, 13.5), 0), seed=400 + k)
    pop_in(fl, 1150 + k * 5, 8)
sfx(1150, "sparkle"); sfx(1170, "magic")


def butterfly(name, c0, f0, f1, col, seed):
    r = random.Random(seed)
    root = empty(name, c0)
    m = mat("bfly" + str(col), col, rough=0.4, emit=0.4)
    wings = []
    for sd in (-1, 1):
        piv = empty("wpiv", (0, 0, 0), root)
        sphere("wing", 0.16, (0, sd * 0.14, 0), m, piv, scale=(1.0, 1.0, 0.1), segs=12, rings=6)
        wings.append((piv, sd))
    sphere("bbody", 0.035, (0, 0, 0), mat("bbody", (0.1, 0.1, 0.1)), root, scale=(3, 1, 1), segs=8, rings=5)
    frames = list(range(0, N + 1, 2))
    locs, sc = [], []
    for fr in frames:
        t = (fr - f0) / FPS
        locs.append((c0[0] + 1.5 * math.sin(t * 0.9 + seed), c0[1] + 0.8 * math.sin(t * 1.3 + seed), c0[2] + 0.4 * math.sin(t * 2.1) + 0.2 * t if fr > f0 else c0[2]))
        sc.append((1, 1, 1) if f0 <= fr <= f1 else (0.001,) * 3)
    bake(root, "location", frames, locs)
    bake(root, "scale", frames, sc)
    for piv, sd in wings:
        bake(piv, "rotation_euler", frames, [(sd * math.radians(55) * math.sin(fr * 1.4), 0, 0) for fr in frames])


for k, col in enumerate([C["pink"], C["yellow"], (0.5, 0.7, 1.0), C["orange"]]):
    butterfly(f"bf{k}", (66.5 + k * 2.5, 9.5, 1.6), 1160 + k * 10, N, col, k * 3)
BL = camera("BL", [(1140, (70.5, 1.6, 2.4), (70.5, 10.5, 0.9)), (1300, (70.5, 2.8, 2.2), (70.5, 10.5, 0.9))], lens=26)
cut(1140, BL)

# --- 1300-1500: celebration
celebrate((70.5, 8.6, 0), 1300)
for j, k in enumerate(kids.values()):
    k.cheer(1306 + j * 4, n=4)
mur.hop(1310, n=4, h=0.25)
cd.emote(mur, "heart", 1330, 1420)
flash_lights(rec, 1300, 1480, period=10)
CE = camera("CE", [(1300, (70.5, 3.2, 1.7), (70.5, 8.6, 1.2)), (1500, (70.5, 4.0, 1.6), (70.5, 8.6, 1.15))], lens=26)
cut(1300, CE)

# --- 1500-1680: wave + camera up
for k in kids.values():
    k.wiggle(1500, 1660, a=10, period=24)
mur.wiggle(1500, 1660, a=8, period=26)
roll_wheels(rec, 0, N)
outro_cam("G", 1500, 1680, (70.5, 4.0, 1.6), (70.5, 8.6, 1.15))
finish(N, "k_ep3")
