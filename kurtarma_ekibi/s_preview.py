"""30 sn önizleme: iskeletli (kol/bacak/kafa hareketli) karakterlerle park sahnesi."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from story import *
import puppet as pp

N = 720
W = build_world(N, farm=False)
emir = cd.char("emir", (64.6, 10.0, 0))
ada = cd.char("ada", (67.6, 10.4, 0))
sami = cd.char("sami", (74.5, 12.6, 0))
tree((72.6, 12.9, 0), s=1.3, seed=77)
pol = make_police()
pol.root.location = (40.0, NORTH_LANE, 0)
bur = driver_card(pol, "burak")
PE, PA, PS, PB = pp.Puppet(emir, "emir"), pp.Puppet(ada, "ada"), pp.Puppet(sami, "sami"), pp.Puppet(bur, "burak")
for k, P in enumerate((PE, PA, PS, PB)):
    P.add(pp.idle(phase=k * 1.7))
b = cd.ball()
sfx(0, "birds", dur=N / FPS)

# 0-96: hello!
PE.add(pp.wave(10, 90, "L")); PA.add(pp.wave(16, 92, "L"))
emir.hop(40, n=1, h=0.25); ada.hop(52, n=1, h=0.25)
sfx(20, "giggle"); sfx(52, "boing", vol=0.5)
C1 = camera("C1", [(0, (66.0, 2.0, 1.5), (66.1, 10.2, 0.85)), (96, (66.0, 4.4, 1.25), (66.1, 10.2, 0.8))], lens=32)
cut(0, C1)

# 96-240: walk in, kick the ball back and forth
emir.walk_to(96, 136, 65.4, 10.1); PE.add(pp.walk(96, 136))
ada.walk_to(100, 140, 67.0, 10.3); PA.add(pp.walk(100, 140))
pts = [(0, (66.2, 10.0), 0), (150, (66.0, 9.8), 0)]
f = 150
for k in range(4):
    side = (66.9, 10.25) if k % 2 == 0 else (65.6, 10.05)
    who = PE if k % 2 == 0 else PA
    who.add(pp.kick(f - 6, "L" if who is PE else "R"))
    sfx(f, "kick", vol=0.6)
    f += 22
    pts.append((f, side, 0.4))
PA.add(pp.cheer(232, 250)); ada.hop(234, n=1, h=0.3)
PE.add(pp.nod(236, 256, amp=8))
sfx(234, "giggle")
C2 = camera("C2", [(96, (66.2, 6.2, 1.05), (66.2, 10.2, 0.7)), (240, (66.2, 6.7, 1.0), (66.2, 10.2, 0.7))], lens=30)
cut(96, C2)

# 240-360: Sami sneaks in and snatches the ball
sfx(240, "sneak", dur=5.0)
sami.walk_to(244, 300, 68.4, 10.9); PS.add(pp.walk(244, 300, period=22, amp=16))
pts += [(268, (68.2, 10.6), 0.5)]
PS.add(pp.nod(300, 330, amp=6))
keys(b, "scale", [(304, (1, 1, 1)), (310, (0.001,) * 3), (575, (0.001,) * 3), (580, (1, 1, 1))])
sfx(305, "pop")
sami.face(312, -1).walk_to(316, 360, 74.0, 11.6); PS.add(pp.walk(316, 360, period=12, amp=24))
C3 = camera("C3", [(240, (67.6, 5.0, 1.25), (68.0, 10.7, 0.8)), (360, (69.0, 5.2, 1.25), (70.0, 11.0, 0.8))], lens=28)
cut(240, C3)

# 360-450: the kids notice
cd.emote(emir, "!", 364, 410); cd.emote(ada, "!", 368, 410)
PE.add(pp.point(372, 440, "L", deg=20)); PA.add(pp.point(372, 440, "L", deg=15))
PE.add(pp.nod(410, 446, amp=-10, period=40)); PA.add(pp.nod(410, 446, amp=10, period=40))
cd.emote(ada, "tear", 412, 450)
sfx(366, "oops"); sfx(412, "sad")
C4 = camera("C4", [(360, (66.2, 7.0, 1.0), (66.2, 10.2, 0.8)), (450, (66.2, 7.6, 0.95), (66.2, 10.2, 0.8))], lens=28)
cut(360, C4)

# 450-570: Polis Burak arrives
drive(pol, [(440, (40.0, NORTH_LANE), 0), (540, (66.0, NORTH_LANE), 0)])
roll_wheels(pol, 0, N)
flash_lights(pol, 450, 720)
sfx(452, "siren_police", dur=90 / FPS)
PB.add(pp.nod(548, 568, amp=12, period=14))
cd.emote(bur, "!", 545, 575, dz=0.12, size=0.38)
C5 = track_cam("C5", lambda f: pol.root.location if f < 440 else evalv(pol.root, "location", f), 450, 520,
               offset=(5.5, -6.5, 1.6), look=(0, 0.3, 1.4), lens=30)
cut(450, C5)
C6 = camera("C6", [(520, (69.2, -0.4, 1.7), (66.3, NORTH_LANE + 0.2, 1.6)), (570, (69.0, -0.2, 1.7), (66.3, NORTH_LANE + 0.2, 1.6))], lens=32)
cut(520, C6)

# 570-660: Sami gives the ball back, everyone cheers
sami.face(568, 1).at(570, 69.0, 10.9)
PS.add(pp.nod(580, 610, amp=10, period=20))
sami.bow(585, n=2, a=20)
cd.emote(sami, "heart", 600, 650)
pts += [(578, (68.7, 10.7), 0.0), (605, (67.4, 10.3), 0.9)]
sfx(600, "kick", vol=0.5)
PE.add(pp.cheer(612, 700)); PA.add(pp.cheer(612, 700)); PS.add(pp.cheer(620, 700, up_L=30, up_R=0))
for c in (emir, ada):
    c.hop(614, n=4, h=0.35)
sami.hop(624, n=3, h=0.3)
celebrate((66.8, 9.6, 0), 612, n_conf=45)
PB.add(pp.nod(615, 700, amp=8, period=18))
C7 = camera("C7", [(570, (67.2, 4.0, 1.4), (67.4, 10.4, 0.9)), (660, (67.2, 4.8, 1.35), (67.4, 10.4, 0.9))], lens=28)
cut(570, C7)

# 660-720: goodbye wave, camera rises
PE.add(pp.wave(660, 716, "L", raise_deg=10)); PA.add(pp.wave(662, 716, "L", raise_deg=10)); PS.add(pp.wave(664, 716, "L", raise_deg=10))
outro_cam("G", 660, 720, (67.2, 4.8, 1.35), (67.4, 10.4, 0.9), up=(0, -2.0, 2.2), look_up=(0, 0, 0.9))
cd.ball_path(b, sorted(pts))
cd.finish_all(N)
for P in (PE, PA, PS, PB):
    P.bake(N)
render("k_preview")
