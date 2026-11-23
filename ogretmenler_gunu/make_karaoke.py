# -*- coding: utf-8 -*-
"""Karaoke söz görselleri (şeffaf PNG, 1920x1080) + zamanlama listesi üretir.
Kullanım: python3 make_karaoke.py  ->  assets/karaoke/*.png ve karaoke.json"""
import json, os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "assets")
OUT = os.path.join(A, "karaoke")
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))
FPS = 30
W, H = 1920, 1080
SIZE = 86
FONT = ImageFont.truetype(os.path.join(A, "Baloo2-ExtraBold.ttf"), SIZE)
WHITE, SUNG, STROKE = (255, 255, 255, 255), (255, 217, 61, 255), (43, 27, 74, 255)
ROWS_Y = [858, 976]


def F(t):
    return int(round(t * FPS)) + 1


words = json.load(open(os.path.join(A, "words.json"), encoding="utf-8"))
# blokları kur: [satır A kelimeleri], [Canım, öğretmenim!]
blocks, cur = [], None
for i, (w, a, b) in enumerate(words):
    if w in ("Öğretmenler", "Kalbin", "Sevgin", "Her"):
        cur = [[], []]; blocks.append(cur)
    cur[1 if w in ("Canım", "öğretmenim!") else 0].append((w, a, b))


def draw_state(rows, n_sung):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    k = 0
    for r, row in enumerate(rows):
        texts = [w for w, _, _ in row]
        space = FONT.getlength(" ")
        widths = [FONT.getlength(t) for t in texts]
        total = sum(widths) + space * (len(texts) - 1)
        x = (W - total) / 2
        y = ROWS_Y[r]
        pad_x, pad_y = 34, 6
        top, bot = y - SIZE * 0.62 - pad_y, y + SIZE * 0.5 + pad_y
        d.rounded_rectangle((x - pad_x, top, x + total + pad_x, bot), radius=40, fill=(20, 10, 40, 92))
        for t, wd in zip(texts, widths):
            col = SUNG if k < n_sung else WHITE
            d.text((x, y), t, font=FONT, fill=col, anchor="ls", stroke_width=8, stroke_fill=STROKE)
            x += wd + space
            k += 1
    return im


entries = []
for bi, (ra, rb) in enumerate(blocks):
    allw = ra + rb
    show = allw[0][1] - 0.7
    if bi > 0:
        show = max(show, blocks[bi - 1][1][-1][2] + 0.35)
    end = allw[-1][2] + 0.5
    if bi + 1 < len(blocks):
        end = min(end, blocks[bi + 1][0][0][1] - 0.75)
    times = [show] + [w[1] for w in allw] + [end]
    for n in range(len(allw) + 1):
        f0, f1 = F(times[n]), F(times[n + 1])
        if f1 <= f0:
            continue
        name = "soz_%02d_%02d.png" % (bi + 1, n)
        draw_state([ra, rb], n).save(os.path.join(OUT, name), optimize=True)
        entries.append(dict(file=name, f0=f0, f1=f1, t0=round(times[n], 2), t1=round(times[n + 1], 2)))
# çakışma kontrolü
for a, b in zip(entries, entries[1:]):
    assert a["f1"] <= b["f0"], (a, b)
json.dump(entries, open(os.path.join(OUT, "karaoke.json"), "w"), ensure_ascii=False, indent=1)
print(len(entries), "görsel;", "ilk", entries[0], "son", entries[-1])
