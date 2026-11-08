"""Intro (20 s): fly down to town, title pops in, the five vehicles say hello."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
from lib import *
from vehicles import *
import people as pp

N = 480
s = reset(N)
st = standard_world(N)
vs = park_vehicles(st)

cam1 = camera("C1", [(0, (11, -48, 30), (11, 10, 22)), (60, (11, -38, 20), (11, 6, 12)), (130, (10.9, -16, 5.5), (10.9, 4, 5.4))], lens=30)
cut(0, cam1)
sfx(0, "whoosh")
sfx(70, "whoosh", vol=0.6)

# title letters
title = "KURTARMA EKİBİ"
tm = [mat(f"title{i}", c, rough=0.25, emit=0.25) for i, c in enumerate(
    [C["red"], C["orange"], C["yellow"], C["green"], C["blue"], C["purple"], C["pink"]])]
letters = letters_row(title, 1.55, 10.9, -1.0, 6.2, tm)
for i, o in enumerate(letters):
    f = 140 + i * 5
    key(o, "scale", 0, (0.001,) * 3)
    keys(o, "scale", [(f - 1, (0.001,) * 3), (f + 6, (1.3,) * 3), (f + 10, (1, 1, 1))])
    sfx(f, "pop", vol=0.45, pitch=1.0 + i * 0.04)
    z = o.location.z
    for k, ff in enumerate(range(205 + i * 2, 245 + i * 2, 20)):
        keys(o, "location", [(ff, (o.location.x, -1.0, z)), (ff + 8, (o.location.x, -1.0, z + 0.5)), (ff + 16, (o.location.x, -1.0, z))])
    keys(o, "scale", [(262 + i, (1, 1, 1)), (270 + i, (0.001,) * 3)])
sfx(205, "tada")
sfx(262, "whoosh", vol=0.6)
cam2 = camera("C2", [(130, (10.9, -16, 5.5), (10.9, 4, 5.4)), (270, (10.9, -14.5, 4.8), (10.9, 4, 5.0))], lens=30)
cut(130, cam2)

# vehicles come out one by one
sounds = ["siren_police", "siren_ambulance", "siren_fire", "siren_tow", "heli"]
for i, v in enumerate(vs):
    dx = DOOR_X[i]
    f = 285 + i * 34
    open_door(st, i, f - 22, 18)
    for e in v.eyes:
        keys(e, "scale", [(0, (1, 1, 0.08)), (f - 2, (1, 1, 0.08)), (f + 4, (1, 1, 1))])
    keys(v.root, "location", [(f, (dx, STATION_Y + 3.6, 0)), (f + 22, (dx, 5.6, 0))])
    if v.kind == "heli":
        keys(v.root, "scale", [(f, (0.8,) * 3), (f + 22, (1, 1, 1))])
        keys(v.parts["rotor"], "scale", [(f, (0.5, 0.5, 1)), (f + 22, (1, 1, 1))])
        spin(v.parts["rotor"], f + 10, N, 2.0)
        jump(v.root, f + 26, n=2, h=0.8, period=16)
    else:
        roll_wheels(v, f, f + 24)
    wiggle_happy(v, f + 26, n=2, h=0.3)
    for k, m in enumerate(v.lights):
        flash(m, f + 4, N, period=10, on=9, phase=k)
    sfx(f + 6, sounds[i], dur=1.4, vol=0.7)
    sfx(f + 26, "boing", vol=0.4)
    pp.wave(v.driver, f + 8, f + 60, side="l", seated=True)
    pp.auto_blink(v.driver, 0, N, i + 40)
    auto_blink(v.eyes, f + 20, N, seed=i + 30)
# move camera in sync with the vehicle reveals
ks = []
for i in range(5):
    f = 285 + i * 34
    ks.append((f - 12, (DOOR_X[i] - 1.0, -8.5, 2.4), (DOOR_X[i], 6, 1.6)))
ks.append((470, (10.9, -15.5, 4.0), (10.9, 5, 2.0)))
cam3 = camera("C3b", ks, lens=30)
cut(270, cam3)
for v in vs:
    wiggle_happy(v, 445, n=2, h=0.3)
for k, (x, nm, kw) in enumerate([(-2.6, "k1", dict(hair_style="pigtails", hair="black", dress=True, shirt=(1.0, 0.8, 0.15), skin="tan")),
                                  (24.4, "k2", dict(hair_style="spiky", hair="brown", shirt=(0.2, 0.65, 0.95), iris="hazel"))]):
    P = pp.make_person(nm, H=1.1, **kw)
    P.root.location = (x, 5.2, 0)
    P.root.rotation_euler.z = math.radians(-90)
    pp.auto_blink(P, 0, N, 50 + k)
    pp.wave(P, 280 + k * 20, 420, side="r" if k == 0 else "l")
    pp.cheer(P, 445, n=2)
sfx(445, "yay", vol=0.8)
render("intro")
