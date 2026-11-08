"""Helicopter episode (55 s): lamb stuck on a mountain ledge, flown back to its mother."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
from lib import *

N = 1320
D = 70.0
FACE = math.radians(90)  # animals look toward +Y (where the cameras are)
s = reset(N)
st = standard_world(N, skip_zones=[(D - 25, -80, D + 75, -4.6)])
vs = park_vehicles(st)
v = vs[4]
dx = DOOR_X[4]
rotor, trot = v.parts["rotor"], v.parts["tail_rotor"]

# props: mountain with ledge, farm
mountain((D + 6, -40, 0), r=16, h=20)
ledge = Vector((D + 5.5, -29.0, 7.0))
cyl("ledge", 2.2, 0.6, tuple(ledge - Vector((0, 0, 0.3))), mat("rock", (0.55, 0.5, 0.48), rough=0.9))
for k in range(5):
    tree((D - 8 + k * 6, -48 + (k % 2) * 4, 0), s=1.1, seed=40 + k)
barn((D + 42, -32, 0), rot=math.radians(90))
lamb = make_animal("lamb", name="lamb")
lamb.root.location = tuple(ledge + Vector((0.4, 0.3, 0.3)))
lamb.root.rotation_euler.z = FACE
mama = make_animal("lamb", scale=1.45, name="mama")
farm_spot = Vector((D + 36, -22.5, 0))
mama.root.location = tuple(farm_spot)
mama.root.rotation_euler.z = math.radians(120)
set_mood(lamb, 0, False)
set_mood(mama, 0, False)
sad_pose(lamb, 0, 706)
cry(lamb, 480, 660)
auto_blink(lamb.eyes, 0, N, 21)
auto_blink(mama.eyes, 0, N, 22)

# ---------------------------------------------------------------- alarm
flash(st["lamp"], 0, 216, period=10, on=12)
alert_bubble((10.9, 8.3, 9.2), 6, 96, face_rot=math.radians(-90))
sfx(0, "alarm", dur=4.0)
camA = camera("A", [(0, (10.9, -13, 3.5), (10.9, 9, 4.6)), (96, (10.9, -9.5, 3.2), (10.9, 9, 4.8))], lens=28)
cut(0, camA)
camB = camera("B", [(96, (dx + 0.3, 0.5, 1.7), (dx, 10, 1.6)), (216, (dx + 0.3, 2.3, 1.7), (dx, 10, 1.5))], lens=32)
cut(96, camB)
open_door(st, 4, 100, 30)
for e in v.eyes:
    keys(e, "scale", [(0, (1, 1, 0.08)), (140, (1, 1, 0.08)), (148, (1, 1, 1))])
sfx(142, "wake")
blink(v.eyes, [178])
auto_blink(v.eyes, 216, N, 23)
for m in v.lights:
    flash(m, 150, N, period=16, on=10)

# ---------------------------------------------------------------- roll out + take off + fly
r = v.root
keys(r, "scale", [(226, (0.8,) * 3), (262, (1, 1, 1))])
keys(rotor, "scale", [(226, (0.5, 0.5, 1)), (262, (1, 1, 1))])
hover1 = ledge + Vector((-1.0, 0.6, 4.2))
seq = [
    (216, (dx, STATION_Y + 3.6, 0), (0, 0, -90)),
    (262, (dx, 5.0, 0), (0, 0, -90)),
    (300, (dx, 5.0, 0), (0, 0, -90)),
    (340, (dx + 2, 3.0, 6.0), (0, 0, -60)),
    (420, ((dx + hover1.x) / 2 + 4, -10, 10.5), (0, 8, -35)),
    (540, tuple(hover1), (0, 0, -20)),
]
for f, loc, rot in seq:
    key(r, "location", f, loc)
    key(r, "rotation_euler", f, tuple(math.radians(a) for a in rot))
spin(rotor, 230, N, 2.6)
spin(trot, 230, N, 4.0, axis=1)
sfx(230, "heli", dur=(N - 230) / FPS)
camC = camera("C", [(216, (dx + 7, -7.0, 1.8), (dx, 6, 1.6)), (340, (dx + 8, -9.0, 2.2), (dx + 2, 3, 5.5))], lens=30)
cut(216, camC)
camD = follow_cam("Dcam", r, 340, 480, offset=(-9.0, 7.0, 3.0), look_offset=(4, -3, 0), lens=30)
cut(340, camD)
camE = camera("E", [(480, (D - 10, -8, 7.5), (D + 4, -29, 9.6)), (600, (D - 8, -10, 8.0), (D + 4, -29, 9.6))], lens=28)
cut(480, camE)
sfx(492, "baa_sad")

# ---------------------------------------------------------------- basket rescue
basket = empty("basket")
bm = mat("basket", (0.75, 0.5, 0.25), rough=0.7)
cyl("bk", 0.7, 0.55, (0, 0, 0.27), bm, basket, verts=20)
torus("bkrim", 0.7, 0.07, (0, 0, 0.55), bm, basket, rot=(math.radians(90), 0, 0))
rope = cyl("rope", 0.04, 1.0, (0, 0, 0), mat("ropem", (0.9, 0.85, 0.7), rough=0.6), verts=8)

L = {}
def rope_len_keys(pairs):
    for f, l in pairs:
        L[f] = l

rope_len_keys([(0, 0.4), (600, 0.4), (650, 3.9), (712, 3.9), (760, 1.6), (900, 1.6), (950, 8.6), (1005, 8.6), (1060, 0.4), (N, 0.4)])
fs_sorted = sorted(L)

def rope_len(f):
    for a, b in zip(fs_sorted, fs_sorted[1:]):
        if a <= f <= b:
            return L[a] + (L[b] - L[a]) * ease((f - a) / (b - a))
    return L[fs_sorted[-1]]

# keep the helicopter hovering above the ledge, then fly to the farm
hover2 = farm_spot + Vector((-1.6, 1.2, 9.4))
for f, loc, rot in [(560, tuple(hover1), (0, 0, -20)), (712, tuple(hover1), (0, 0, -20)), (770, tuple(hover1 + Vector((0, 0, 0.6))), (0, 0, 0)),
                    (840, tuple((hover1 + hover2) / 2 + Vector((0, 0, 1.5))), (0, 8, 10)), (900, tuple(hover2), (0, 0, 0)),
                    (1005, tuple(hover2), (0, 0, 0)), (1200, tuple(hover2 + Vector((0, 0, 0.5))), (0, 0, 0))]:
    key(r, "location", f, loc)
    key(r, "rotation_euler", f, tuple(math.radians(a) for a in rot))
# gentle hover bob
frames = list(range(216, N + 1, 2))
bake(v.body, "location", frames, [(0, 0, 0.12 * math.sin(f * 0.12)) if f > 330 else (0, 0, 0) for f in frames])

frames = list(range(560, N + 1, 2))
bk_locs, rope_locs, rope_sc = [], [], []
for f in frames:
    p, _ = world_pos(r, f)
    top = p + Vector((0, 0, 0.55))
    l = rope_len(f)
    bk_locs.append(tuple(top - Vector((0, 0, l + 0.55))))
    rope_locs.append(tuple(top - Vector((0, 0, l / 2))))
    rope_sc.append((1, 1, l))
bake(basket, "location", [0] + frames, [bk_locs[0]] + bk_locs)
bake(rope, "location", [0] + frames, [rope_locs[0]] + rope_locs)
bake(rope, "scale", [0] + frames, [rope_sc[0]] + rope_sc)
sfx(600, "winch", dur=50 / FPS)
sfx(712, "winch", dur=48 / FPS)
sfx(900, "winch", dur=50 / FPS)
sfx(1005, "winch", dur=55 / FPS)

def bk_at(f):
    return Vector(bk_locs[(f - 560) // 2])

# lamb hops into the basket
a = Vector(lamb.root.location); b = bk_at(700) + Vector((0, 0, 0.35))
fr = list(range(662, 701, 2))
bake(lamb.root, "location", fr, [tuple(a.lerp(b, ease((f - 662) / 38)) + Vector((0, 0, 1.2 * math.sin(math.pi * (f - 662) / 38)))) for f in fr])
sfx(662, "boing")
happy_pose(lamb, 706)
set_mood(lamb, 708, True)
sfx(710, "baa")
fr = list(range(702, 952, 2))
bake(lamb.root, "location", fr, [tuple(bk_at(f) + Vector((0, 0, 0.35))) for f in fr])
# hop out to mama
a = bk_at(952) + Vector((0, 0, 0.35)); b = farm_spot + Vector((-1.4, 1.0, 0))
fr = list(range(954, 987, 2))
bake(lamb.root, "location", fr, [tuple(a.lerp(b, ease((f - 954) / 32)) + Vector((0, 0, 1.0 * math.sin(math.pi * (f - 954) / 32)))) for f in fr])
sfx(954, "boing")
set_mood(mama, 988, True)
happy_pose(mama, 988)
sfx(990, "baa")
hearts_burst(tuple(farm_spot + Vector((-0.6, 0.6, 2.2))), 994, n=7, face_rot=FACE)
sfx(994, "love")

H1 = camera("H1", [(600, (D - 4.0, -14.5, 8.6), (D + 4.5, -28.5, 9.4)), (770, (D - 3.5, -15.0, 9.4), (D + 4.5, -28.5, 10.2))], lens=30)
cut(600, H1)
H2 = follow_cam("H2", r, 770, 900, offset=(-5, 13, -1.0), look_offset=(0, 0, -2.5), lens=30)
cut(770, H2)
H3 = camera("H3", [(900, (D + 31, -7.0, 4.5), (D + 35, -22, 3.2)), (1200, (D + 31.5, -9.0, 3.6), (D + 35, -22, 2.6))], lens=32)
cut(900, H3)

# ---------------------------------------------------------------- celebration + outro
cf = 1004
c = farm_spot + Vector((-0.8, 0.8, 0.6))
sfx(cf, "yay")
confetti(tuple(c + Vector((0, 0, 0.5))), cf + 4, n=55)
sfx(cf + 4, "confetti")
stars_burst(tuple(c + Vector((0, 0, 2.2))), cf + 10, n=8, face_rot=FACE, radius=2.4)
balloons(tuple(c + Vector((0, 0.5, 0.3))), cf + 40, n=7)
sfx(cf + 40, "balloon")
jump(mama.root, cf + 8, n=4, h=0.6)
jl = lamb.root
for i in range(4):
    f = cf + 8 + i * 14
    sfx(f, "boing", vol=0.5)
# lamb jumps (its z already baked until 986; add jumps after)
fr = list(range(cf + 8, cf + 8 + 4 * 14 + 1))
base = Vector(b)
bake(lamb.root, "location", fr, [tuple(base + Vector((0, 0, 0.7 * abs(math.sin(math.pi * (f - cf - 8) / 14))))) for f in fr])
for f, loc, rot in [(1210, tuple(hover2 + Vector((0, 0, 0.5))), (0, 0, 0)), (1320, tuple(hover2 + Vector((26, 10, 9))), (0, 10, 20))]:
    key(r, "location", f, loc)
    key(r, "rotation_euler", f, tuple(math.radians(a) for a in rot))
sfx(1206, "whoosh")
cl, _ = world_pos(H3, 1200)
G = camera("G", [(1200, tuple(cl), (D + 35, -22, 2.6)), (1320, tuple(cl + Vector((3, 2, 8))), (D + 52, -14, 12))], lens=32)
cut(1200, G)
render("ep_heli")
