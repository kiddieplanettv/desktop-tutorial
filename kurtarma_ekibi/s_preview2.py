"""30 sn önizleme (karakter sayfalarıyla): yöne göre dönen, duruma göre ifade değiştiren karakterler."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from story import *

N = 720
W = build_world(N, farm=False)
for o in list(bpy.data.objects):
    if o.name.startswith(("fpost", "frail")):
        bpy.data.objects.remove(o)
ada = cd.sprite("ada", (65.4, 10.2, 0))
emir = cd.sprite("emir", (67.8, 10.4, 0))
sami = cd.sprite("sami", (75.0, 12.2, 0))
tree((73.6, 12.9, 0), s=1.3, seed=77)
pol = make_police()
pol.root.location = (36.0, NORTH_LANE, 0)
bur_drv = driver_card(pol, "burak")
bur = cd.sprite("burak", (67.0, 3.6, 0))
bur.show(0, False)
b = cd.ball()
sfx(0, "birds", dur=N / FPS)

# 0-96: hello
for c in (ada, emir):
    c.pose(0, "front")
ada.pose(26, "happy").hop(28, n=2, h=0.3).pose(66, "front")
emir.pose(34, "happy").hop(36, n=2, h=0.3).pose(72, "front")
sfx(28, "giggle"); sfx(40, "boing", vol=0.5)
C1 = camera("C1", [(0, (66.6, 3.2, 1.4), (66.6, 10.3, 0.8)), (96, (66.6, 5.0, 1.2), (66.6, 10.3, 0.75))], lens=30)
cut(0, C1)

# 96-220: face each other and pass the ball
ada.turn(96, "q_r"); emir.turn(100, "q_l")
A, E = (65.4, 10.2), (67.8, 10.4)
pts = [(0, (66.6, 10.0), 0), (110, (66.6, 10.0), 0), (126, A, 0.35)]
f = 126
for k in range(4):
    who = ada if k % 2 == 0 else emir
    who.squash(f - 2).hop(f, n=1, h=0.18)
    sfx(f, "kick", vol=0.6)
    tgt = E if k % 2 == 0 else A
    f += 22
    pts.append((f, tgt, 0.45))
ada.pose(208, "happy"); emir.pose(212, "happy")
ada.pose(232, "q_r"); emir.pose(234, "q_l")
sfx(208, "giggle")
C2 = camera("C2", [(96, (66.6, 6.2, 1.0), (66.6, 10.3, 0.7)), (220, (66.6, 6.6, 0.95), (66.6, 10.3, 0.7))], lens=30)
cut(96, C2)

# 220-330: Sami sneaks in, grabs the ball, runs off
sfx(220, "sneak", dur=4.5)
sami.pose(220, "side_l").walk_to(222, 286, 69.4, 10.9)
sami.pose(288, "front")
cd.emote(sami, "note", 290, 318)
pts += [(240, (68.9, 10.7), 0.4), (300, (68.9, 10.7), 0.0)]
keys(b, "scale", [(300, (1, 1, 1)), (305, (0.001,) * 3), (585, (0.001,) * 3), (590, (1, 1, 1))])
sfx(301, "pop")
sami.turn(306, "q_r", "side_r").walk_to(312, 345, 75.5, 9.0)
C3 = camera("C3", [(220, (68.6, 5.0, 1.15), (69.6, 10.9, 0.8)), (330, (70.0, 5.0, 1.15), (71.0, 10.6, 0.8))], lens=28)
cut(220, C3)

# 330-420: the kids are surprised, then sad
ada.pose(330, "surprised").hop(332, n=1, h=0.2)
emir.pose(333, "surprised").hop(335, n=1, h=0.2)
cd.emote(ada, "!", 334, 372); cd.emote(emir, "!", 337, 372)
ada.pose(378, "sad"); emir.pose(382, "sad")
cd.emote(ada, "tear", 384, 420)
sfx(334, "oops"); sfx(380, "sad")
C4 = camera("C4", [(330, (66.6, 7.2, 1.0), (66.6, 10.3, 0.85)), (420, (66.6, 7.7, 0.95), (66.6, 10.3, 0.85))], lens=28)
cut(330, C4)

# 420-520: Polis Burak arrives and steps out
drive(pol, [(410, (36.0, NORTH_LANE), 0), (488, (66.0, NORTH_LANE), 0)])
roll_wheels(pol, 0, N)
flash_lights(pol, 420, N)
sfx(422, "siren_police", dur=70 / FPS)
C5 = track_cam("C5", lambda f: evalv(pol.root, "location", f), 420, 488, offset=(6.0, -6.5, 1.6), look=(0, 0.3, 1.3), lens=30)
cut(420, C5)
bur_drv.show(496, False)
bur.show(496, True).pose(496, "side_r").walk_to(498, 520, 69.6, 3.6)
bur.pose(522, "angry")
cd.emote(bur, "!", 524, 560)
sfx(526, "whistle")
C6 = camera("C6", [(488, (70.5, -3.2, 1.6), (68.0, 3.0, 1.1)), (560, (71.2, -3.0, 1.6), (70.2, 4.0, 1.0))], lens=30)
cut(488, C6)

# Sami runs straight into him
sami.at(520, 73.6, 5.6).pose(520, "side_l").walk_to(522, 548, 71.0, 4.0)
sami.pose(550, "surprised").hop(550, n=1, h=0.25)
sfx(551, "oops")
sami.pose(568, "sad")
bur.pose(566, "side_l")

# 560-640: Sami says sorry and gives the ball back
for c, x in ((ada, 68.4), (emir, 67.2)):
    c.at(560, x, 5.2)
ada.pose(560, "sad"); emir.pose(560, "sad")
pts += [(584, (70.6, 4.2), 0.0), (608, (68.5, 5.0), 0.8)]
sfx(590, "kick", vol=0.5)
sami.bow(592, n=2, a=18)
cd.emote(sami, "heart", 600, 640)
ada.pose(610, "happy").hop(612, n=2, h=0.3); emir.pose(614, "happy").hop(616, n=2, h=0.3)
bur.pose(616, "happy")
sfx(612, "giggle")
C7 = camera("C7", [(560, (69.4, -1.6, 1.4), (69.6, 4.6, 1.0)), (640, (69.4, -1.0, 1.35), (69.6, 4.6, 1.0))], lens=26)
cut(560, C7)

# 640-720: everyone celebrates
sami.pose(640, "happy").hop(642, n=3, h=0.3)
for c in (ada, emir):
    c.hop(646, n=4, h=0.35)
celebrate((69.4, 4.4, 0), 640, n_conf=45)
outro_cam("G", 660, 720, (69.4, -1.0, 1.35), (69.6, 4.6, 1.0), up=(0, -2.0, 2.2), look_up=(0, 0, 0.9))
cut(640, C7)
cd.ball_path(b, sorted(pts))
finish(N, "k_preview2")
