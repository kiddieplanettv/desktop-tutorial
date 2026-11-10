"""Bölüm 2 – Ağaçtaki Cimcime (70 s): the monkey climbs a tree and can't get down; İtfaiyeci Kemal helps."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from story import *
from mathutils import Euler
from cards import smooth

N = 1680
W = build_world(N)
TX, TY = 60.0, 10.8
tr, tip = big_tree((TX, TY, 0), branch_side=-1)
mon = cd.char("cimcime", (62.0, 8.6, 0))
elif_ = cd.char("elif", (66.5, 9.4, 0))
den = cd.char("deniz", (68.4, 9.9, 0))
ft = make_firetruck()
XR = 63.0
ft.root.location = (22.0, NORTH_LANE, 0)
kem_cab = driver_card(ft, "kemal")
kem_bk = cd.char("kemal", (0.3, 0, 0.05), height=1.05, parent=ft.parts["bucket_level"], tag="kemal_bk", shadow=False)
kem_bk.show(0, False)
sfx(0, "birds", dur=N / FPS)

# --- 0-150: monkey plays, kids play
for f in (10, 52, 94):
    mon.hop(f, n=2, h=0.5, period=16)
mon.spin(130, dur=16)
sfx(14, "monkey"); sfx(96, "monkey")
elif_.cheer(20, n=3); den.cheer(60, n=3)
WI = camera("WI", [(0, (63.5, 0.5, 2.4), (63.5, 10, 2.2)), (150, (63.0, 1.2, 2.4), (62.0, 10, 2.4))], lens=28)
cut(0, WI)

# --- 150-330: climbing
mon.walk_to(150, 190, TX + 0.45, TY - 0.55)
mon.z_to(195, 300, 2.6)
mon.walk_to(290, 330, tip.x, tip.y + 0.15)
mon.z_to(300, 330, tip.z + 0.05)
mon.wiggle(195, 300, a=12, period=14)
sfx(195, "climb", dur=4.6); sfx(220, "monkey")
CL = camera("CL", [(150, (TX + 2.5, 3.8, 1.6), (TX + 0.3, TY - 0.6, 1.4)), (330, (TX + 2.0, 3.4, 2.6), (TX, TY - 1.2, 3.8))], lens=32)
cut(150, CL)

# --- 330-470: stuck and scared
mon.shake(340, 900, amp=0.02)
cd.emote(mon, "!", 340, 390)
cd.emote(mon, "tear", 395, 470)
cd.emote(mon, "?", 480, 540)
sfx(342, "monkey_scared"); sfx(430, "monkey_scared")
MO = camera("MO", [(330, (TX + 1.8, 4.2, 4.2), (tip.x, tip.y, 4.7)), (470, (TX + 1.5, 4.7, 4.3), (tip.x, tip.y, 4.75))], lens=36)
cut(330, MO)

# --- 470-580: kids notice and run over
elif_.walk_to(470, 540, 61.6, 7.2)
den.walk_to(474, 548, 63.2, 7.5)
cd.emote(elif_, "!", 482, 530); cd.emote(den, "!", 486, 530)
elif_.tilt(545, 620, 12); den.hop(550, n=2)
sfx(482, "oops")
KI = camera("KI", [(470, (64.0, 1.6, 1.6), (63.0, 8.0, 1.6)), (580, (63.4, 1.8, 1.8), (62.2, 8.0, 2.4))], lens=28)
cut(470, KI)

# --- 580-760: fire truck arrives
drive(ft, [(570, (22.0, NORTH_LANE), 0), (760, (XR, NORTH_LANE), 0)])
flash_lights(ft, 580, 1300)
sfx(584, "siren_fire", dur=(770 - 584) / FPS)
cd.emote(kem_cab, "!", 600, 660, dz=0.15, size=0.4)
TR = follow_cam("TR", ft.root, 580, 690, offset=(4.5, -8.0, 2.0), look_offset=(0.0, 0.5, 1.4), lens=30)
cut(580, TR)
AR = camera("AR", [(690, (XR + 5.0, -6.5, 2.4), (XR - 1.0, 4.0, 2.4)), (780, (XR + 4.5, -6.0, 2.6), (XR - 1.5, 5.0, 3.0))], lens=28)
cut(690, AR)

# --- 780-900: ladder + bucket up to the monkey
piv, ext, lvl = ft.parts["ladder_pivot"], ft.parts["ladder_ext"], ft.parts["bucket_level"]
P = Vector((XR - 2.2, NORTH_LANE, 2.05 + 0.15))
K = Vector((tip.x, tip.y - 0.4, tip.z - 0.25))
d = K - P
yaw = math.atan2(d.y, d.x)
pitch = math.atan2(d.z, math.hypot(d.x, d.y))
reach = d.length
ext_len = max(0.0, min(3.5, reach - 3.45 - 0.3))
keys(piv, "rotation_euler", [(780, (0, 0, 0)), (820, (0, 0, yaw)), (850, (0, -pitch, yaw))])
keys(lvl, "rotation_euler", [(820, (0, 0, 0)), (850, (0, pitch, 0))])
keys(ext, "location", [(850, (0, 0, 0.12)), (885, (ext_len, 0, 0.12))])
kem_cab.show(776, False)
kem_bk.show(776, True)
sfx(780, "ladder", dur=105 / FPS)
LA = camera("LA", [(776, (XR + 3.0, -7.5, 3.2), (XR - 2.0, 6.0, 3.6)), (900, (XR + 2.0, -7.0, 4.0), (TX + 0.5, 7.0, 4.2))], lens=26)
cut(776, LA)


def bucket_world(f):
    r = evalv(piv, "rotation_euler", f)
    e = evalv(ext, "location", f)
    v = Vector((e.x + 3.45 + 0.3, 0, 0.27))
    v.rotate(Euler((0, r.y, 0)))
    v.rotate(Euler((0, 0, r.z)))
    return P + v

# --- 900-960: monkey hops into the bucket
a0 = Vector((tip.x, tip.y + 0.15, tip.z + 0.05))
for f in range(905, 931, 2):
    t = (f - 905) / 26
    bw = bucket_world(f)
    p = a0.lerp(bw, smooth(t))
    mon.path.append((f, Vector((p.x, p.y, 0))))
    mon.zpath.append((f, p.z + 0.8 * math.sin(math.pi * t)))
sfx(905, "boing"); sfx(932, "monkey_happy")
cd.emote(kem_bk, "heart", 935, 990, dz=0.1, size=0.4)
cd.emote(mon, "heart", 940, 990)

# --- 960-1080: ladder lowers, monkey rides
keys(ext, "location", [(965, (ext_len, 0, 0.12)), (1005, (0, 0, 0.12))])
keys(piv, "rotation_euler", [(1005, (0, -pitch, yaw)), (1045, (0, -math.radians(4), yaw))])
keys(lvl, "rotation_euler", [(1005, (0, pitch, 0)), (1045, (0, math.radians(4), 0))])
sfx(965, "ladder", dur=80 / FPS)
for f in range(932, 1062, 2):
    bw = bucket_world(f)
    mon.path.append((f, Vector((bw.x, bw.y, 0))))
    mon.zpath.append((f, bw.z))
RI = camera("RI", [(960, (XR + 4.0, -5.0, 3.6), (TX + 0.5, 6.5, 3.6)), (1080, (XR + 3.0, -5.5, 2.6), (TX + 1.0, 5.5, 2.2))], lens=30)
cut(960, RI)

# --- 1062-1100: hop down to the kids
bw = bucket_world(1062)
dest = Vector((62.4, 6.9, 0))
for f in range(1064, 1100, 2):
    t = (f - 1064) / 36
    p = bw.lerp(dest, smooth(t))
    mon.path.append((f, Vector((p.x, p.y, 0))))
    mon.zpath.append((f, max(0.0, p.z + 1.0 * math.sin(math.pi * t))))
mon.zpath.append((1101, 0.0))
sfx(1064, "boing"); sfx(1100, "monkey_happy")

# --- 1100-1500: celebration
celebrate((62.4, 7.0, 0), 1110)
mon.spin(1112, dur=18).cheer(1135, n=4)
elif_.cheer(1115, n=4); den.cheer(1120, n=4)
kem_bk.wiggle(1110, 1260, a=8, period=22)
CE = camera("CE", [(1100, (56.8, 4.4, 1.6), (62.6, 7.2, 1.3)), (1300, (57.4, 4.6, 1.55), (62.6, 7.2, 1.25))], lens=30)
cut(1100, CE)
# ladder home again
keys(piv, "rotation_euler", [(1300, (0, -math.radians(4), yaw)), (1360, (0, 0, 0))])
keys(lvl, "rotation_euler", [(1300, (0, math.radians(4), 0)), (1360, (0, 0, 0))])
sfx(1300, "ladder", dur=60 / FPS)
kem_bk.show(1366, False); kem_cab.show(1366, True)
HO = camera("HO", [(1300, (XR + 6.0, -7.0, 2.6), (XR - 2.0, 5.0, 2.2)), (1500, (XR + 5.0, -6.5, 2.4), (XR - 2.0, 5.0, 2.0))], lens=28)
cut(1300, HO)
cd.emote(kem_cab, "star", 1400, 1470, dz=0.15, size=0.4)
for c in (elif_, den, mon):
    c.wiggle(1380, 1660, a=10, period=24)

# --- 1500-1680: fire truck leaves, camera up
drive(ft, [(1510, (XR, NORTH_LANE), 0), (1680, (XR + 28, NORTH_LANE), 0)])
sfx(1505, "honk")
roll_wheels(ft, 0, N)
outro_cam("G", 1500, 1680, (XR + 5.0, -6.5, 2.4), (XR - 2.0, 5.0, 2.0))
finish(N, "k_ep2")
