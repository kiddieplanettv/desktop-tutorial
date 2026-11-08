"""Finale (20 s): the whole team and their friends celebrate, then wave goodbye."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
from lib import *

N = 480
FACE = math.radians(-90)
s = reset(N)
st = standard_world(N)
vs = park_vehicles(st)
for i in range(5):
    set_door_open(st, i)
xs = [1.5, 6.5, 11.5, 17.0]
ground_vs = [v for v in vs if v.kind != "heli"]
for v, x in zip(ground_vs, xs):
    v.root.location = (x + 2.5, 1.0, 0)
    v.root.rotation_euler.z = math.radians(-90)
heli = vs[4]
heli.root.location = (11.0, 3.0, 7.5)
heli.root.rotation_euler.z = math.radians(-90)
heli.root.scale = (1, 1, 1)
heli.parts["rotor"].scale = (1, 1, 1)
spin(heli.parts["rotor"], 0, N, 2.4)
spin(heli.parts["tail_rotor"], 0, N, 4.0, axis=1)
frames = list(range(0, N + 1, 2))
bake(heli.body, "location", frames, [(0, 0, 0.25 * math.sin(f * 0.1)) for f in frames])

friends = []
for kind, sc, x, nm in [("puppy", 1.0, 3.0, "pup"), ("puppy", 1.4, 4.6, "mom"), ("bunny", 1.0, 7.5, "bun"),
                         ("kitten", 1.0, 10.0, "kit"), ("lamb", 1.0, 15.5, "lamb"), ("lamb", 1.4, 17.4, "mama")]:
    a = make_animal(kind, scale=sc, name=nm)
    a.root.location = (x + 2.0, -4.6, 0)
    a.root.rotation_euler.z = FACE
    set_mood(a, 0, True)
    friends.append(a)
    if kind == "bunny":
        a.bump.scale = (0.001,) * 3
        a.bandage.scale = (1, 1, 1)
car = make_bubblecar()
car.root.location = (14.8, -4.4, 0)
car.root.rotation_euler.z = FACE
car.parts["sad"].scale = (0.001,) * 3
car.parts["happy"].scale = (1, 1, 1)

for i, v in enumerate(vs):
    for k, m in enumerate(v.lights):
        flash(m, 0, N, period=10, on=9, phase=k + i)
    auto_blink(v.eyes, 0, N, seed=80 + i)
for i, a in enumerate(friends):
    auto_blink(a.eyes, 0, N, seed=90 + i)
    if hasattr(a, "tail"):
        wag(a, 0, N)

cam = camera("cam", [(0, (-2.0, -17.5, 4.0), (9.0, 0, 2.6)), (240, (11.5, -18.0, 4.6), (11.5, 0, 3.0)),
                     (420, (24.0, -16.5, 4.2), (14.0, 0, 2.8)), (479, (25.0, -14.0, 9.0), (16.0, 2, 12.0))], lens=30)
cut(0, cam)

# waves of joy
actors = [v.root for v in ground_vs] + [a.root for a in friends] + [car.root]
for wave, f0 in enumerate([30, 190, 330]):
    for i, o in enumerate(actors):
        jump(o, f0 + i * 5, n=2, h=0.6, period=14)
    sfx(f0, "yay", vol=0.8)
    for i in range(0, len(actors), 3):
        sfx(f0 + i * 5, "boing", vol=0.35)
for i, (x, f) in enumerate([(4, 40), (18, 120), (11, 200), (6, 300), (16, 360)]):
    confetti((x, -2.0, 1.0), f, n=45, seed=200 + i)
    sfx(f, "confetti", vol=0.8)
balloons((6, -3.0, 0.5), 80, n=6, seed=31)
balloons((16, -3.0, 0.5), 230, n=6, seed=32)
sfx(80, "balloon"); sfx(230, "balloon")
for i, v in enumerate(ground_vs):
    sfx(50 + i * 22, ["siren_police", "siren_ambulance", "siren_fire", "siren_tow"][i], dur=0.9, vol=0.5)

# goodbye text
msg = "HOŞÇA KALIN!"
tm = [mat(f"bye{i}", c, rough=0.25, emit=0.25) for i, c in enumerate(
    [C["red"], C["orange"], C["yellow"], C["green"], C["blue"], C["purple"], C["pink"]])]
lets = letters_row(msg, 1.5, 12.5, -3.0, 5.4, tm, prefix="B")
for k, o in enumerate(lets):
    f = 250 + k * 5
    x = o.location.x
    key(o, "scale", 0, (0.001,) * 3)
    keys(o, "scale", [(f - 1, (0.001,) * 3), (f + 6, (1.3,) * 3), (f + 10, (1, 1, 1))])
    sfx(f, "pop", vol=0.4, pitch=1.0 + k * 0.04)
    for ff in range(310 + k * 2, 450, 24):
        keys(o, "location", [(ff, (x, -3.0, 5.4)), (ff + 10, (x, -3.0, 5.9)), (ff + 20, (x, -3.0, 5.4))])
sfx(310, "tada")
# everyone waves goodbye: a little side-to-side wobble
for a in friends:
    frames = list(range(380, N + 1, 3))
    bake(a.body, "rotation_euler", frames, [(0.18 * math.sin((f - 380) * 0.35), 0, 0) for f in frames])
render("finale")
