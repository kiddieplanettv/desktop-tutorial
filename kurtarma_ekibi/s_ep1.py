"""Bölüm 1 – Kayıp Top (70 s): Sinsi Sami steals the kids' ball, Polis Burak catches him, Sami says sorry."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from story import *

N = 1680
W = build_world(N)

ada = cd.char("ada", (63.5, 10.0, 0))
emir = cd.char("emir", (67.5, 10.6, 0))
sami = cd.char("sami", (72.9, 13.6, 0))
tree((72.4, 12.9, 0), s=1.3, seed=77)
b = cd.ball()
pol = make_police()
pol.root.location = (56, NORTH_LANE, 0)
bur = driver_card(pol, "burak")
cd.puddle((100.6, SIDEWALK_N, 0.12))
sfx(0, "birds", dur=N / FPS)

# --- 0-370: kids play ball
A, E = (63.5, 10.0), (67.5, 10.6)
pts = [(0, A, 0)]
f, who = 18, 0
while f < 370:
    pts.append((f, E if who == 0 else A, 1.1))
    sfx(f - 18, "kick", vol=0.6)
    (ada if who == 0 else emir).hop(f - 20, n=1)
    who ^= 1
    f += 30
last = pts[-1][1]
# a big kick rolls the ball toward the tree
pts += [(392, (70.8, 12.4), 0.6), (430, (71.6, 12.9), 0.0)]
sfx(370, "kick")
ada.cheer(120, n=2); emir.cheer(240, n=2)
W1 = camera("W1", [(0, (65.4, 1.2, 1.9), (66, 11, 1.1)), (110, (65.6, 2.6, 1.7), (66, 11, 1.0))], lens=30)
cut(0, W1)
W2 = camera("W2", [(110, (65.3, 3.6, 1.3), (65.5, 10.3, 0.9)), (250, (65.8, 4.4, 1.2), (65.6, 10.3, 0.9))], lens=34)
cut(110, W2)

# --- 250-520: Sami peeks, tiptoes, grabs the ball, sneaks away
sfx(250, "sneak", dur=11.0)
sami.walk_to(262, 300, 72.0, 13.3, bounce=False).tilt(262, 330, -18)
cd.emote(sami, "note", 300, 350)
sami.walk_to(380, 430, 71.9, 13.0)
sami.hop(432, n=1, h=0.3)
keys(b, "scale", [(452, (1, 1, 1)), (458, (0.001,) * 3), (961, (0.001,) * 3), (965, (1, 1, 1))])
sfx(452, "pop")
sami.face(462, -1).walk_to(470, 540, 79.5, 12.2)
S1 = camera("S1", [(250, (70.2, 6.3, 1.4), (72.2, 13.2, 1.1)), (370, (70.6, 6.8, 1.4), (72.0, 13.0, 1.0))], lens=40)
cut(250, S1)
W3 = camera("W3", [(370, (70.0, 6.8, 1.5), (72, 12.6, 1.0)), (500, (71.5, 6.8, 1.5), (74.5, 12.4, 1.0))], lens=30)
cut(370, W3)

# --- 500-620: kids notice, sad
for c in (ada, emir):
    c.walk_to(470, 500, c._pos(470).x + 0.6, c._pos(470).y)
cd.emote(ada, "!", 505, 545); cd.emote(emir, "!", 508, 545)
cd.emote(ada, "tear", 550, 620); cd.emote(emir, "tear", 556, 620)
ada.tilt(545, 620, 10); emir.tilt(545, 620, -10)
sfx(505, "oops"); sfx(548, "sad")
K = camera("K", [(500, (66.3, 4.6, 1.25), (66.4, 10.4, 1.0)), (620, (66.3, 5.4, 1.2), (66.4, 10.4, 1.0))], lens=28)
cut(500, K)

# --- 620-700: Burak sees it, siren on
cd.emote(bur, "!", 626, 690, dz=0.15, size=0.4)
bur.hop(630, n=1, h=0.12)
flash_lights(pol, 650, 1300)
sfx(652, "siren_police", dur=(1000 - 652) / FPS)
P = camera("P", [(620, (60.2, -0.6, 1.7), (56.4, NORTH_LANE + 0.2, 1.6)), (700, (59.8, -0.4, 1.7), (56.4, NORTH_LANE + 0.2, 1.6))], lens=32)
cut(620, P)

# --- 700-1000: chase along the north sidewalk, Sami slips in the puddle
sami.walk_to(700, 760, 81.0, 5.6).walk_to(760, 955, 100.2, SIDEWALK_N)
drive(pol, [(700, (56, NORTH_LANE), 0), (1000, (94.6, NORTH_LANE), 0)])
C1 = track_cam("C1", sami._pos, 700, 840, offset=(-1.5, -8.0, 1.8), look=(2.0, 0, 0.9), lens=30)
cut(700, C1)
C2 = follow_cam("C2", pol.root, 840, 960, offset=(-3.5, -8.5, 2.2), look_offset=(5.0, 1.5, 1.0), lens=28)
cut(840, C2)
sami.fall(958, 1075, side=1)
sfx(956, "splash"); sfx(960, "slip"); sfx(966, "thud")
pts += [(456, (71.9, 13.0), 0.0), (962, (100.3, SIDEWALK_N), 0.0), (990, (102.6, 3.6), 0.6), (1010, (103.2, 3.4), 0.0)]
F = camera("F", [(960, (102.4, -3.6, 1.5), (100.9, 4.0, 0.8)), (1010, (102.2, -3.2, 1.45), (100.9, 4.0, 0.8))], lens=32)
cut(960, F)
roll_wheels(pol, 0, N)

# --- 1010-1090: Burak arrives
cd.emote(bur, "star", 1020, 1080, dz=0.15, size=0.4)
bur.wiggle(1020, 1080, a=6)
B2 = camera("B2", [(1010, (98.8, -0.6, 1.7), (95.0, NORTH_LANE + 0.2, 1.6)), (1090, (98.5, -0.4, 1.7), (95.0, NORTH_LANE + 0.2, 1.6))], lens=32)
cut(1010, B2)

# --- 1090-1240: kids arrive, Sami returns the ball and says sorry
ada.at(1000, 92.0, SIDEWALK_N + 0.3).walk_to(1060, 1150, 98.0, SIDEWALK_N + 0.4)
emir.at(1000, 90.5, SIDEWALK_N - 0.2).walk_to(1065, 1155, 96.6, SIDEWALK_N - 0.1)
ada.face(1000, 1); emir.face(1000, 1)
cd.emote(sami, "?", 1080, 1130)
pts += [(1110, (103.2, 3.4), 0.0), (1150, (100.6, SIDEWALK_N - 0.3), 0.5), (1185, (98.2, SIDEWALK_N + 0.2), 1.0)]
sfx(1150, "kick", vol=0.5)
sami.bow(1190, n=2)
cd.emote(sami, "heart", 1215, 1260)
ada.cheer(1192, n=2); emir.cheer(1196, n=2)
sfx(1194, "giggle")
M = camera("M", [(1090, (100.6, -2.6, 1.5), (99.6, SIDEWALK_N, 0.95)), (1240, (100.4, -2.2, 1.45), (99.6, SIDEWALK_N, 0.95))], lens=30)
cut(1090, M)

# --- 1240-1500: everyone plays together
p1, p2, p3 = (98.2, SIDEWALK_N + 0.2), (100.6, SIDEWALK_N - 0.3), (96.6, SIDEWALK_N - 0.1)
order = [p2, p3, p1, p2, p1, p3, p2, p1]
f = 1240
for k, p in enumerate(order):
    pts.append((f + 26, p, 1.0))
    sfx(f, "kick", vol=0.5)
    f += 26
celebrate((99.4, 3.6, 0), 1250)
for c in (ada, emir):
    c.cheer(1260, n=4)
sami.cheer(1300, n=3)
flash_lights(pol, 1250, 1450, period=8)
sfx(1262, "honk")
WIDE = camera("WIDE", [(1240, (100.0, -4.8, 2.0), (99.0, 3.8, 1.2)), (1500, (100.0, -3.6, 1.9), (99.0, 3.8, 1.1))], lens=28)
cut(1240, WIDE)

# --- 1500-1680: wave goodbye, camera rises
for c in (ada, emir, sami):
    c.wiggle(1500, 1640, a=10, period=24)
outro_cam("G", 1500, 1680, (100.0, -3.6, 1.9), (99.0, 3.8, 1.1))
cd.ball_path(b, pts)
finish(N, "k_ep1")
