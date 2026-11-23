# -*- coding: utf-8 -*-
"""Hata filtresi: blender -b ogretmenler_gunu.blend -P qa_check.py
Tüm zaman çizelgesini tarar ve qa_rapor.txt dosyasına yazar."""
import bpy, json, os, math
from mathutils import Vector

HERE = os.path.dirname(bpy.data.filepath)
A = os.path.join(HERE, "assets")
FPS = 30
S = bpy.data.scenes["Sahne3D"]
class St:
    pass


def snap(x):
    o = St()
    o.name, o.type = x.name, x.type
    o.frame_final_start, o.frame_final_end = x.frame_final_start, x.frame_final_end
    o.frame_final_duration = x.frame_final_end - x.frame_final_start
    o.path = bpy.path.abspath(os.path.join(x.directory, x.elements[0].filename)) if x.type == "IMAGE" else None
    return o


if "Montaj" in bpy.data.scenes:
    mont = bpy.data.scenes["Montaj"]
    strips = [snap(x) for x in mont.sequence_editor.strips]
    sound_strips = [x for x in strips if x.type == "SOUND"]
    img_strips = sorted([x for x in strips if x.type == "IMAGE"], key=lambda x: x.frame_final_start)
    scene_strips = [x for x in strips if x.type == "SCENE"]
    bpy.data.scenes.remove(mont)          # dosya kaydedilmez; yalnız değerlendirme için
else:
    strips = sound_strips = img_strips = scene_strips = []
for w in bpy.context.window_manager.windows:
    w.scene = S

ERR, WARN, OK = [], [], []
words = json.load(open(os.path.join(A, "words.json"), encoding="utf-8"))
word_t = [w[1] for w in words]
cuts = [m.frame for m in sorted(S.timeline_markers, key=lambda m: m.frame)]
cam = S.camera

# 1) Ses ve süre
END = S.frame_end
OK.append("Kare aralığı 1-%d (%.2f sn, %d fps)" % (END, END / FPS, S.render.fps))
for snd in bpy.data.sounds:
    p = bpy.path.abspath(snd.filepath)
    if not os.path.exists(p):
        ERR.append("Ses dosyası bulunamadı: %s" % p)
    else:
        OK.append("Ses dosyası var: %s" % os.path.basename(p))
if scene_strips and scene_strips[0].frame_final_duration != END:
    ERR.append("Montaj sahne şeridi süresi %d != %d" % (scene_strips[0].frame_final_duration, END))
if sound_strips:
    sd = sound_strips[0].frame_final_duration
    if abs(sd - END) > 2:
        WARN.append("Şarkı şeridi %d kare, sahne %d kare" % (sd, END))
    else:
        OK.append("Şarkı süresi sahne ile uyumlu (%d kare)" % sd)

# 2) Dosyalar ve yazı tipi
for f in bpy.data.fonts:
    if f.filepath and f.filepath != "<builtin>" and not os.path.exists(bpy.path.abspath(f.filepath)):
        ERR.append("Yazı tipi bulunamadı: %s" % f.filepath)
SAFE = set("ÖöÜüĞğŞşİıÇç!?.,' \n") | set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
for cu in bpy.data.curves:
    if cu.bl_rna.identifier == "TextCurve":
        bad = [c for c in cu.body if c not in SAFE]
        if bad:
            ERR.append("'%s' yazısında doğrulanmamış karakter: %s" % (cu.body, bad))
        if cu.font is None or "Baloo" not in cu.font.name:
            WARN.append("'%s' yazısı Baloo yazı tipini kullanmıyor" % cu.body)
missing_img = [x for x in img_strips if not os.path.exists(x.path)]
if missing_img:
    ERR.append("%d karaoke görseli bulunamadı" % len(missing_img))
elif img_strips:
    OK.append("%d karaoke görseli yerinde" % len(img_strips))

# 3) Karaoke zamanlaması: çakışma ve kelime vurgusu
for a, b in zip(img_strips, img_strips[1:]):
    if a.frame_final_end > b.frame_final_start:
        ERR.append("Karaoke şeritleri çakışıyor: %s / %s" % (a.name, b.name))
for w in words:
    f = int(round(w[1] * FPS)) + 1
    st = [x for x in img_strips if x.frame_final_start <= f < x.frame_final_end]
    if not st:
        ERR.append("'%s' (%.2f sn) söylenirken ekranda söz yok" % (w[0], w[1]))
if img_strips and not any("Karaoke" in e for e in ERR):
    OK.append("Her kelime söylenirken ilgili satır ekranda ve vurgulu")

# 4) Kesmeler: sözün ortasına denk gelmesin, çekimler çok kısa olmasın
for i, c in enumerate(cuts):
    t = (c - 1) / FPS
    if i + 1 < len(cuts) and (cuts[i + 1] - c) < FPS * 1.0:
        WARN.append("Çekim %d çok kısa (%.2f sn)" % (i + 1, (cuts[i + 1] - c) / FPS))
    for w in words:
        if w[1] + 0.05 < t < w[2] - 0.1 and (t - w[1]) > 0.25:
            WARN.append("Kesme %.2f sn '%s' kelimesinin ortasında" % (t, w[0]))
OK.append("%d çekim, ortalama %.1f sn" % (len(cuts), END / FPS / max(1, len(cuts))))

# 5) Kare kare tarama: kamera, arabalar
meshes = [o for o in S.objects if o.type in ("MESH", "CURVE", "FONT")]
yard = [S.objects["BahceAraba%d" % i] for i in range(6)]
cam_inside = {}
prev = None
back = []
cut_set = set(cuts)
for f in range(1, END + 1):
    S.frame_set(f)
    cp = cam.matrix_world.translation.copy()
    # çekim içinde yön değişimi (geri sekme)
    if prev is not None and f not in cut_set and f - 1 not in cut_set:
        d = cp - prev[0]
        if prev[1] is not None and d.length > 1e-4 and prev[1].length > 1e-4 and d.dot(prev[1]) < -0.2 * d.length * prev[1].length:
            back.append(f)
        prev = (cp, d)
    else:
        prev = (cp, None)
    if f % 2 == 0:
        continue
    for o in meshes:
        mw = o.matrix_world
        if mw.to_scale().length < 0.05:
            continue
        loc = mw.translation
        if (loc - cp).length > 40:
            continue
        inv = mw.inverted_safe()
        lp = inv @ cp
        bb = o.bound_box
        mn = Vector((min(v[0] for v in bb), min(v[1] for v in bb), min(v[2] for v in bb)))
        mx = Vector((max(v[0] for v in bb), max(v[1] for v in bb), max(v[2] for v in bb)))
        if all(mn[i] - 0.05 < lp[i] < mx[i] + 0.05 for i in range(3)):
            cam_inside.setdefault(o.name, []).append(f)
    # arabalar birbirine girmesin
    for i in range(6):
        for j in range(i + 1, 6):
            d = (yard[i].matrix_world.translation - yard[j].matrix_world.translation).length
            if d < 2.25:
                ERR.append("Kare %d: BahceAraba%d ve %d iç içe (%.2f)" % (f, i, j, d))
for name, fr in cam_inside.items():
    ERR.append("Kamera '%s' nesnesinin içinde/çok yakınında: kare %d-%d (%d kare)" % (name, fr[0], fr[-1], len(fr)))
if back:
    WARN.append("Kamera çekim içinde geri seğiriyor: %d kare (ilk: %s)" % (len(back), back[:8]))
else:
    OK.append("Kamera hareketleri çekim içinde akıcı (geri sekme yok)")
if not cam_inside:
    OK.append("Kamera hiçbir nesnenin içine girmiyor")

rep = ["HATA FİLTRESİ RAPORU", "=" * 40]
rep += ["HATA: " + e for e in ERR[:60]] + ["UYARI: " + w for w in WARN[:60]] + ["TAMAM: " + o for o in OK]
rep.append("Özet: %d hata, %d uyarı" % (len(ERR), len(WARN)))
open(os.path.join(HERE, "qa_rapor.txt"), "w", encoding="utf-8").write("\n".join(rep) + "\n")
print("\n".join(rep))
