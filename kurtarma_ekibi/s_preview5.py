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
tree((69.9, 11.6, 0), s=1.3, seed=77)
A0, E0 = (65.9, 10.2), (67.3, 10.2)
ada = a3.Char3D("ada", (*A0, 0), heading=0)
emir = a3.Char3D("emir", (*E0, 0), heading=0)
sami = a3.Char3D("sami", (69.35, 10.95, 0), heading=90)
bur = a3.Char3D("burak", (65.8, 3.5, 0), heading=-90)
pol = make_police()
pol.root.location = (36.0, NORTH_LANE, 0)
drv = a3.Char3D("burak", (0, 0, 0), heading=-90, tag="burak_drv")
drv.look_cam = False
drv.root.parent = pol.seat
drv.root.scale = (0.62,) * 3
drv.root.location = (0.05, 0, -0.15)
drv.add(a3.sit(0, N))
a3.visible(drv, 0, 499)
a3.visible(bur, 500)
a3.visible(sami, 206)
for k, c in enumerate((ada, emir, sami, bur, drv)):
    c.add(a3.idle(phase=k * 1.3))
b = cd.ball()
sfx(0, "birds", dur=N / FPS)

# 0-96: hello! (happy)
ada.expr(0, "happy").add(a3.wave(8, 80, "R"))
emir.expr(0, "happy").add(a3.wave(14, 84, "L"))
sfx(20, "giggle")
C1 = camera("C1", [(0, (66.6, 5.6, 1.15), (66.6, 10.2, 0.7)), (96, (66.6, 6.4, 1.05), (66.6, 10.2, 0.68))], lens=32)
cut(0, C1)

# 96-220: turn to each other (three-quarter to the camera) and kick the ball
ada.face(96, 55); emir.face(100, -55)
pts = [(0, (66.6, 9.9), 0), (110, (66.6, 9.9), 0), (128, (66.2, 10.0), 0.3)]
f = 128
for k in range(4):
    kicker = ada if k % 2 == 0 else emir
    kicker.add(a3.kick(f - 4, "R"))
    sfx(f, "kick", vol=0.6)
    f += 22
    pts.append((f, (67.0, 10.0) if k % 2 == 0 else (66.2, 10.0), 0.35))
a3.cheer_on(ada, 212, jumps=1); a3.cheer_on(emir, 215, jumps=1)
sfx(214, "giggle")
C2 = camera("C2", [(96, (66.6, 6.6, 1.0), (66.6, 10.2, 0.6)), (220, (66.6, 6.9, 0.95), (66.6, 10.2, 0.6))], lens=30)
cut(96, C2)

# 220-330: Sami sneaks in from behind the tree, grabs the ball and runs.
# The kids are looking the other way (not laughing any more) and do not notice him.
ada.expr(222, "neutral"); emir.expr(226, "neutral")
ada.face(226, 70, dur=16); emir.face(232, 60, dur=16)
sfx(220, "sneak", dur=4.5)
fs = sami.go(222, 68.55, 10.45, "sneak", rate=1.7)
sami.face(fs + 1, 0, dur=8)
pts += [(240, (68.5, 10.0), 0.4), (fs + 4, (68.5, 10.0), 0.0)]
keys(b, "scale", [(fs + 8, (1, 1, 1)), (fs + 13, (0.001,) * 3), (606, (0.001,) * 3), (610, (1, 1, 1))])
sami.add(a3.bow(fs + 4, fs + 14, deg=32))
sfx(fs + 9, "pop")
fr = sami.go(fs + 18, 71.2, 8.8, "run")
print("SAMI sneak end", fs, "run end", fr)
C3 = camera("C3", [(220, (68.6, 5.6, 1.15), (68.9, 10.6, 0.7)), (330, (69.2, 5.6, 1.15), (69.6, 10.4, 0.7))], lens=28)
cut(220, C3)

# 330-420: the kids notice: surprised, then sad
for c, d in ((ada, 0), (emir, 4)):
    c.face(326 + d, 20 if c is ada else -20)
    c.expr(332 + d, "surprised").add(a3.surprised(334 + d, 370))
    c.expr(376 + d, "sad").add(a3.sad(378 + d, 470, k=0.5))
sfx(334, "oops"); sfx(380, "sad")
C4 = camera("C4", [(330, (66.6, 7.4, 1.0), (66.6, 10.2, 0.8)), (420, (66.6, 7.9, 0.95), (66.6, 10.2, 0.8))], lens=28)
cut(330, C4)

# 420-500: police car arrives; the kids hurry towards the road
drive(pol, [(410, (36.0, NORTH_LANE), 0), (488, (63.0, NORTH_LANE), 0)])
roll_wheels(pol, 0, N)
flash_lights(pol, 420, N)
sfx(422, "siren_police", dur=70 / FPS)
drv.expr(440, "angry")
C5 = track_cam("C5", lambda f: evalv(pol.root, "location", f), 420, 488, offset=(6.0, -6.5, 1.6), look=(0, 0.3, 1.3), lens=30)
cut(420, C5)
fa = ada.go(472, 66.3, 4.6, "run")
fe = emir.go(476, 67.3, 4.9, "run")
print("KIDS arrive", fa, fe)

# 500-560: Burak gets out (serious) and runs to block Sami, who runs right into him
bur.expr(500, "angry")
fb = bur.go(502, 68.3, 3.7, "run")
bur.face(fb + 1, 0, dur=8).add(a3.point(fb + 6, fb + 34, "R"))
sfx(fb + 6, "whistle")
fs2 = sami.go(max(fr + 6, 444), 70.2, 4.3, "run")
print("BURAK arrive", fb, "SAMI caught", fs2)
sami.face(fs2 + 1, 60, dur=8)
sami.expr(fs2 + 2, "surprised").add(a3.surprised(fs2 + 2, fs2 + 26))
sfx(fs2 + 3, "oops")
C6 = camera("C6", [(500, (69.0, -0.9, 1.35), (68.8, 4.0, 0.9)), (560, (69.2, -0.5, 1.3), (69.2, 4.0, 0.9))], lens=28)
cut(500, C6)

# 560-640: Sami is ashamed (sad), says sorry and gives the ball back
fsad = max(568, fs2 + 28)
sami.face(fsad - 6, 25)
sami.expr(fsad, "sad").add(a3.sad(fsad, N, k=0.5))
ada.face(fa + 2, 0); emir.face(fe + 2, 0)
pts += [(606, (69.7, 4.1), 0.0), (632, (66.85, 4.05), 0.5)]
sfx(610, "kick", vol=0.5)
fh = max(fa, fe) + 6
ada.expr(fh, "happy"); emir.expr(fh + 3, "happy")
a3.cheer_on(ada, fh + 2, jumps=2); a3.cheer_on(emir, fh + 6, jumps=2)
bur.expr(fh + 4, "neutral")
sfx(fh + 2, "giggle")
C7 = camera("C7", [(560, (68.2, 0.2, 1.25), (68.2, 4.4, 0.85)), (640, (68.2, 0.5, 1.2), (68.2, 4.4, 0.85))], lens=24)
cut(560, C7)

# 640-720: the kids celebrate getting the ball back; Sami stays sad and ashamed
sfx(650, "yay")
confetti((67.0, 4.6, 1.0), 654, n=45)
sfx(654, "confetti")
stars_burst((66.8, 4.6, 2.2), 660, n=8, face_rot=math.radians(-90), radius=1.6)
balloons((65.6, 6.5, 0.3), 666, n=6)
sfx(666, "balloon")
bur.add(a3.wave(662, 712, "L"))
outro_cam("G", 672, 720, (68.2, 0.5, 1.2), (68.2, 4.4, 0.85), up=(0, -1.4, 1.4), look_up=(0, 0, 0.7))
cut(640, C7)
cd.ball_path(b, sorted(pts), ground=a3.ground_z)
a3.bake_all(N)
_s = bpy.context.scene
_s.render.resolution_x, _s.render.resolution_y = 1280, 720
_s.eevee.taa_render_samples = 12
_s.eevee.use_soft_shadows = True
_s.eevee.shadow_cascade_size = "2048"
finish(N, "k_preview5")
