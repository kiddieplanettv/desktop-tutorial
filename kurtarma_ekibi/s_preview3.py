"""30 sn önizleme – gerçek 3D, iskeletli karakterler (Hunyuan3D-2mv + kullanıcının karakter sayfaları)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from story import *
import anim3d as a3

N = 720
W = build_world(N, farm=False)
for o in list(bpy.data.objects):
    if o.name.startswith(("fpost", "frail")):
        bpy.data.objects.remove(o)
tree((73.6, 12.9, 0), s=1.3, seed=77)
A0, E0 = (65.6, 10.2), (67.6, 10.2)
ada = a3.Char3D("ada", (*A0, 0), heading=0)
emir = a3.Char3D("emir", (*E0, 0), heading=0)
sami = a3.Char3D("sami", (73.2, 12.4, 0), heading=90)
bur = a3.Char3D("burak", (64.6, 3.4, 0), heading=0)
pol = make_police()
pol.root.location = (36.0, NORTH_LANE, 0)
drv = a3.Char3D("burak", (0, 0, 0), heading=-90, tag="burak_drv")
drv.root.parent = pol.seat
drv.root.scale = (0.62,) * 3
drv.root.location = (0.05, 0, -0.15)
drv.add(a3.sit(0, N))
a3.visible(drv, 0, 499)
a3.visible(bur, 500)
for k, c in enumerate((ada, emir, sami, bur, drv)):
    c.add(a3.idle(phase=k * 1.3))
b = cd.ball()
sfx(0, "birds", dur=N / FPS)

# 0-96: hello! (happy)
ada.expr(0, "happy").add(a3.wave(8, 80, "R"))
emir.expr(0, "happy").add(a3.wave(14, 84, "L"))
sfx(20, "giggle")
C1 = camera("C1", [(0, (66.6, 4.6, 1.3), (66.6, 10.2, 0.75)), (96, (66.6, 6.0, 1.15), (66.6, 10.2, 0.7))], lens=32)
cut(0, C1)

# 96-220: face each other and kick the ball
ada.face(96, 90); emir.face(100, -90)
pts = [(0, (66.6, 9.9), 0), (110, (66.6, 9.9), 0), (128, (65.95, 10.1), 0.3)]
f = 128
for k in range(4):
    kicker = ada if k % 2 == 0 else emir
    kicker.add(a3.kick(f - 4, "R"))
    sfx(f, "kick", vol=0.6)
    f += 22
    pts.append((f, (67.25, 10.1) if k % 2 == 0 else (65.95, 10.1), 0.35))
ada.add(a3.cheer(214, 236, jumps=1, h=0.15)); emir.add(a3.cheer(216, 238, jumps=1, h=0.15))
sfx(214, "giggle")
C2 = camera("C2", [(96, (66.6, 6.3, 1.0), (66.6, 10.2, 0.6)), (220, (66.6, 6.7, 0.95), (66.6, 10.2, 0.6))], lens=30)
cut(96, C2)

# 220-330: Sami sneaks in (walks on tiptoe), grabs the ball and runs
sfx(220, "sneak", dur=4.5)
sami.move(220, 290, 68.9, 10.6, gait="sneak")
sami.face(292, 0)
pts += [(240, (68.9, 10.2), 0.4), (296, (68.9, 10.2), 0.0)]
keys(b, "scale", [(298, (1, 1, 1)), (303, (0.001,) * 3), (592, (0.001,) * 3), (596, (1, 1, 1))])
sami.add(a3.bow(294, 302, deg=30))
sfx(299, "pop")
sami.move(306, 346, 74.5, 8.6, gait="run")
C3 = camera("C3", [(220, (68.4, 4.6, 1.2), (69.2, 10.6, 0.75)), (330, (69.8, 4.6, 1.2), (70.8, 10.4, 0.75))], lens=28)
cut(220, C3)

# 330-420: the kids are surprised, then sad
for c, d in ((ada, 0), (emir, 4)):
    c.face(330 + d, 25 if c is ada else -25)
    c.expr(332 + d, "surprised").add(a3.surprised(334 + d, 370))
    c.expr(376 + d, "sad").add(a3.sad(378 + d, 560))
cd_ = __import__("cards")
sfx(334, "oops"); sfx(380, "sad")
C4 = camera("C4", [(330, (66.6, 7.4, 1.0), (66.6, 10.2, 0.8)), (420, (66.6, 7.9, 0.95), (66.6, 10.2, 0.8))], lens=28)
cut(330, C4)

# 420-500: police car arrives
drive(pol, [(410, (36.0, NORTH_LANE), 0), (488, (63.0, NORTH_LANE), 0)])
roll_wheels(pol, 0, N)
flash_lights(pol, 420, N)
sfx(422, "siren_police", dur=70 / FPS)
drv.expr(440, "angry")
C5 = track_cam("C5", lambda f: evalv(pol.root, "location", f), 420, 488, offset=(6.0, -6.5, 1.6), look=(0, 0.3, 1.3), lens=30)
cut(420, C5)

# 500-560: Burak steps out (serious), Sami runs right into him
bur.expr(500, "angry")
bur.move(500, 534, 68.6, 3.6, gait="run")
bur.face(534, 0).add(a3.point(538, 566, "R"))
sfx(538, "whistle")
sami.move(500, 540, 70.9, 4.2, gait="run")
sami.face(542, -90)
sami.expr(542, "surprised").add(a3.surprised(542, 566))
sfx(543, "oops")
C6 = camera("C6", [(500, (69.4, -3.0, 1.6), (69.0, 4.0, 1.0)), (560, (69.4, -2.2, 1.5), (69.4, 4.0, 1.0))], lens=30)
cut(500, C6)

# 560-640: Sami is ashamed (sad), says sorry and gives the ball back
sami.face(560, 0)
sami.expr(568, "sad").add(a3.sad(568, N)).add(a3.bow(586, 620, deg=30))
ada.move(560, 600, 67.6, 4.7, gait="run")
emir.move(562, 602, 66.3, 4.5, gait="run")
ada.face(604, 0); emir.face(606, 0)
pts += [(586, (70.9, 4.0), 0.0), (612, (68.0, 4.3), 0.6)]
sfx(596, "kick", vol=0.5)
ada.expr(614, "happy").add(a3.cheer(616, 700, jumps=4, h=0.22))
emir.expr(618, "happy").add(a3.cheer(620, 704, jumps=4, h=0.22))
bur.expr(624, "neutral")
sfx(616, "giggle")
C7 = camera("C7", [(560, (68.6, -1.8, 1.45), (68.6, 4.4, 1.0)), (640, (68.6, -1.2, 1.4), (68.6, 4.4, 1.0))], lens=26)
cut(560, C7)

# 640-720: the kids celebrate getting the ball back; Sami stays sad and ashamed
sfx(640, "yay")
confetti((67.4, 4.4, 1.0), 644, n=45)
sfx(644, "confetti")
stars_burst((67.0, 4.4, 2.2), 650, n=8, face_rot=math.radians(-90), radius=1.6)
balloons((66.0, 6.5, 0.3), 660, n=6)
sfx(660, "balloon")
bur.add(a3.wave(650, 710, "L"))
outro_cam("G", 660, 720, (68.6, -1.2, 1.4), (68.6, 4.4, 1.0), up=(0, -2.0, 2.2), look_up=(0, 0, 0.9))
cut(640, C7)
cd.ball_path(b, sorted(pts))
a3.bake_all(N)
_s = bpy.context.scene
_s.render.resolution_x, _s.render.resolution_y = 1280, 720
_s.eevee.taa_render_samples = 12
_s.eevee.use_soft_shadows = True
_s.eevee.shadow_cascade_size = "2048"
finish(N, "k_preview4")
