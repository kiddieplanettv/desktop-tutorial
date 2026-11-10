"""Bölüm 4 – Kayıp Kuzu (70 s): Pamuk is lost in town; the kids and Polis Burak take her home to the farm."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from story import *

N = 1680
W = build_world(N)
SS = -SIDEWALK_N
ZX = 108.0
for k in range(7):
    box("zebra", (0.6, 0.9, 0.02), (ZX, -3.0 + k * 1.0, 0.075), mat("zebra", (1, 1, 1), rough=0.5), bevel=0)
pam = cd.char("pamuk", (98.0, SS, 0))
mama = cd.char("pamuk", (141.5, 10.0, 0), height=1.35, tag="mama")
eli = cd.char("elif", (90.0, SS - 0.2, 0))
den = cd.char("deniz", (88.8, SS + 0.2, 0))
pol = make_police()
pol.root.location = (70.0, NORTH_LANE, 0)
bur = driver_card(pol, "burak")
car = make_bubblecar()
car.root.location = (80.0, SOUTH_LANE, 0)
sam = driver_card(car, "sami", h=0.8)
sfx(0, "birds", dur=N / FPS)

# --- 0-160: Pamuk is lost
pam.walk_to(0, 70, 103.0, SS)
pam.face(80, -1).face(105, 1).face(130, -1)
cd.emote(pam, "?", 70, 130)
cd.emote(pam, "tear", 120, 170)
pam.tilt(130, 170, 10)
sfx(40, "baa_sad"); sfx(125, "baa_sad")
LO = camera("LO", [(0, (101.0, -12.0, 1.8), (101.5, SS, 0.8)), (160, (102.0, -11.0, 1.7), (102.5, SS, 0.75))], lens=32)
cut(0, LO)

# --- 160-300: the kids find her
eli.walk_to(150, 240, 101.4, SS - 0.1)
den.walk_to(155, 245, 100.2, SS + 0.25)
cd.emote(eli, "!", 245, 285); cd.emote(den, "!", 248, 285)
cd.emote(pam, "heart", 275, 330)
eli.hop(260, n=1); pam.hop(285, n=2, h=0.3)
sfx(250, "oops", vol=0.6); sfx(286, "baa")
sfx(262, "giggle")
FI = camera("FI", [(160, (101.6, -9.0, 1.4), (101.8, SS, 0.75)), (300, (102.2, -8.4, 1.35), (102.4, SS, 0.75))], lens=32)
cut(160, FI)

# --- 300-420: walk to the crossing; police stops traffic
for c, dx in ((eli, -0.8), (den, -1.9), (pam, 0.4)):
    c.face(300, 1)
    c.walk_to(300, 390, ZX + dx, SS - 0.05)
drive(pol, [(290, (70.0, NORTH_LANE), 0), (400, (ZX - 3.8, NORTH_LANE), 0)])
flash_lights(pol, 300, 1100)
sfx(304, "siren_police", dur=96 / FPS)
drive(car, [(300, (80.0, SOUTH_LANE), 0), (420, (ZX - 4.2, SOUTH_LANE), 0)])
sfx(400, "brake")
cd.emote(bur, "!", 405, 460, dz=0.12, size=0.38)
cd.emote(sam, "star", 425, 480, dz=0.1, size=0.36)
CR = camera("CR", [(300, (ZX + 8.0, -9.0, 2.6), (ZX - 2.0, -1.0, 1.0)), (420, (ZX + 7.0, -8.0, 2.4), (ZX - 2.5, -0.5, 1.0))], lens=28)
cut(300, CR)

# --- 420-600: crossing the road
for c, dx in ((eli, -0.8), (den, -1.9), (pam, 0.4)):
    c.walk_to(430, 570, ZX + dx, SIDEWALK_N + 0.1)
sfx(430, "tiptoe", dur=5.5)
bur.wiggle(470, 560, a=6)
CX = camera("CX", [(420, (ZX + 6.5, -2.5, 1.6), (ZX - 1.0, 0.5, 0.8)), (600, (ZX + 6.0, -1.0, 1.7), (ZX - 1.0, 2.5, 0.8))], lens=30)
cut(420, CX)
cd.emote(bur, "heart", 575, 630, dz=0.12, size=0.38)
car_go = 600
drive(car, [(car_go, (ZX - 4.2, SOUTH_LANE), 0), (720, (ZX + 30, SOUTH_LANE), 0)])
sfx(605, "beep_happy")

# --- 600-900: walk east to the farm, police escorts
GATE = 136.0
for c, dx, dy in ((pam, 0.8, 0.0), (eli, -0.4, -0.2), (den, -1.5, 0.25)):
    c.walk_to(600, 890, GATE + dx, SIDEWALK_N + dy)
drive(pol, [(610, (ZX - 3.8, NORTH_LANE), 0), (900, (GATE - 4.0, NORTH_LANE), 0)])
WK = track_cam("WK", pam._pos, 600, 900, offset=(-1.0, -8.5, 1.9), look=(0.5, 0, 0.8), lens=30)
cut(600, WK)

# --- 900-1060: Pamuk sees mama
cd.emote(pam, "!", 900, 940)
cd.emote(mama, "heart", 910, 1000)
sfx(902, "baa"); sfx(925, "baa_mama")
pam.walk_to(940, 1010, 140.2, 9.4)
pam.hop(1012, n=3, h=0.35)
mama.hop(1015, n=2, h=0.3)
hearts_burst((140.9, 9.6, 1.8), 1015, n=7, face_rot=math.radians(-90))
sfx(1015, "love")
for c, x in ((eli, 138.6), (den, 137.4)):
    c.walk_to(950, 1040, x, 8.8)
FA = camera("FA", [(900, (136.5, 1.0, 2.0), (138.5, 7.5, 0.9)), (1015, (138.2, 6.6, 1.7), (140.2, 9.6, 0.9)), (1060, (138.4, 6.8, 1.6), (140.2, 9.6, 0.9))], lens=26)
cut(900, FA)

# --- 1060-1300: celebration at the farm
celebrate((139.6, 8.6, 0), 1070)
eli.cheer(1075, n=4); den.cheer(1080, n=4); pam.cheer(1090, n=3)
sfx(1085, "honk")
cd.emote(bur, "star", 1090, 1160, dz=0.12, size=0.38)
CE = camera("CE", [(1060, (139.6, 6.7, 1.7), (139.8, 9.3, 0.9)), (1300, (139.6, 7.0, 1.6), (139.8, 9.3, 0.9))], lens=24)
cut(1060, CE)

# --- 1300-1500: snuggle + waves
pam.tilt(1300, 1460, 14); mama.tilt(1300, 1460, -10)
for c in (eli, den):
    c.wiggle(1300, 1500, a=10, period=24)
cd.emote(pam, "heart", 1320, 1400); cd.emote(mama, "heart", 1340, 1420)
sfx(1320, "baa")
SN = camera("SN", [(1300, (141.0, 4.8, 1.3), (141.0, 9.6, 0.8)), (1500, (141.0, 5.4, 1.25), (141.0, 9.6, 0.8))], lens=32)
cut(1300, SN)

# --- 1500-1680: outro
roll_wheels(pol, 0, N)
roll_wheels(car, 0, N)
outro_cam("G", 1500, 1680, (139.6, 7.0, 1.6), (139.8, 9.3, 0.9))
finish(N, "k_ep4")
