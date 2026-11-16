"""One single Blender 5.2 file for the whole video: all six scenes + a master scene whose sequencer plays them with the
soundtrack and writes one MP4.   python pack52_tek.py <package dir made by pack52.py> <out.blend>"""
import bpy, sys, os
PKG, OUT = sys.argv[-2], sys.argv[-1]
SEGS = [("1_giris", 240), ("2_bolum1", 1800), ("3_bolum2", 2040), ("4_bolum3", 2040), ("5_bolum4", 2040), ("6_kapanis", 480)]
bpy.ops.wm.read_factory_settings(use_empty=True)
m = bpy.context.scene
m.name = "VIDEO"
scenes = []
for name, n in SEGS:
    with bpy.data.libraries.load(os.path.join(PKG, name + ".blend"), link=False) as (src, dst):
        dst.scenes = list(src.scenes)
    sc = dst.scenes[0]; sc.name = name
    assert sc.frame_end == n - 1
    scenes.append(sc)
m.render.resolution_x, m.render.resolution_y, m.render.resolution_percentage = 1920, 1080, 100
m.render.fps = 24
m.view_settings.view_transform = "Standard"; m.view_settings.look = "None"
m.frame_start, m.frame_end = 0, sum(n for _, n in SEGS) - 1
se = m.sequence_editor_create()
t = 0
for sc, (name, n) in zip(scenes, SEGS):
    st = se.strips.new_scene(name, sc, 1, t)
    for f, v in ((t, 0.0), (t + 10, 1.0), (t + n - 11, 1.0), (t + n - 1, 0.0)):
        st.blend_alpha = v; st.keyframe_insert("blend_alpha", frame=f)
    t += n
snd = se.strips.new_sound("ses", os.path.join(PKG, "ses", "Minik_Ustalar_ses.m4a"), 2, 0)
snd.sound.pack()
r = m.render
r.image_settings.media_type = "VIDEO"; r.image_settings.file_format = "FFMPEG"
r.ffmpeg.format = "MPEG4"; r.ffmpeg.codec = "H264"; r.ffmpeg.constant_rate_factor = "HIGH"
r.ffmpeg.audio_codec = "AAC"; r.ffmpeg.audio_bitrate = 192
r.filepath = "//Minik_Ustalar_6dk.mp4"
bpy.context.window.scene = m if bpy.context.window else m
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SAVED", OUT, round(os.path.getsize(OUT) / 1e6), "MB", [s.name for s in bpy.data.scenes])
