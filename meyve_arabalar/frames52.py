"""Render single frames of a .blend for checking:  python frames52.py <file.blend> <out dir> f1,f2,..."""
import bpy, sys, time
bpy.ops.wm.open_mainfile(filepath=sys.argv[1]); s = bpy.context.scene
s.render.image_settings.file_format = "JPEG"
for f in [int(x) for x in sys.argv[3].split(",")]:
    s.frame_set(f); s.render.filepath = f"{sys.argv[2]}/t_{f:04d}.jpg"
    t = time.time(); bpy.ops.render.render(write_still=True); print("FRAME", f, round(time.time() - t, 1))
