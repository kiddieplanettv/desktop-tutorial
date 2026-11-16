"""Make the ready-to-render Blender 5.2 package: run with Blender 5.2's Python after building the scenes with --hd.
python pack52.py <out dir>      (reads build/<seg>.blend, writes <out>/<n>_<name>.blend and 7_birlestir.blend)"""
import bpy, sys, os, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[-1]
SEGS = [("t_intro", "1_giris", 240), ("t_ep1", "2_bolum1", 1800), ("t_ep2", "3_bolum2", 2040), ("t_ep3", "4_bolum3", 2040),
        ("t_ep4", "5_bolum4", 2040), ("t_outro", "6_kapanis", 480)]
os.makedirs(os.path.join(OUT, "ses"), exist_ok=True)
shutil.copy(os.path.join(HERE, "ses", "Minik_Ustalar_ses.m4a"), os.path.join(OUT, "ses"))
for seg, name, n in SEGS:
    bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "build", seg + ".blend"))
    s = bpy.context.scene
    assert s.frame_end == n - 1, (seg, s.frame_end)
    s.eevee.taa_render_samples = 32
    s.render.image_settings.file_format = "PNG"
    s.render.filepath = f"//kareler/{name}/f_"
    s.render.use_overwrite = False; s.render.use_placeholder = True
    bpy.ops.file.pack_all()
    dst = os.path.join(OUT, name + ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=dst, compress=True)
    print("SAVED", name, round(os.path.getsize(dst) / 1e6), "MB")

# ---- the last file joins the rendered frames and the soundtrack into one MP4
bpy.ops.wm.read_factory_settings(use_empty=True)
s = bpy.context.scene
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1920, 1080, 100
s.render.fps = 24
s.view_settings.view_transform = "Standard"; s.view_settings.look = "None"
total = sum(n for _, _, n in SEGS)
s.frame_start, s.frame_end = 0, total - 1
se = s.sequence_editor_create()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "7_birlestir.blend"))      # so that // paths resolve
t = 0
for seg, name, n in SEGS:
    st = se.strips.new_image(name, f"//kareler/{name}/f_0000.png", 1, t)
    for i in range(1, n):
        st.elements.append(f"f_{i:04d}.png")
    for f, v in ((t, 0.0), (t + 10, 1.0), (t + n - 11, 1.0), (t + n - 1, 0.0)):
        st.blend_alpha = v; st.keyframe_insert("blend_alpha", frame=f)
    t += n
se.strips.new_sound("ses", "//ses/Minik_Ustalar_ses.m4a", 2, 0)
r = s.render
r.image_settings.media_type = "VIDEO"
r.image_settings.file_format = "FFMPEG"
r.ffmpeg.format = "MPEG4"; r.ffmpeg.codec = "H264"; r.ffmpeg.constant_rate_factor = "HIGH"
r.ffmpeg.audio_codec = "AAC"; r.ffmpeg.audio_bitrate = 192
r.filepath = "//Minik_Ustalar_6dk.mp4"
bpy.ops.wm.save_mainfile()
print("SAVED 7_birlestir", len(se.strips))
