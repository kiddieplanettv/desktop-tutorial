import bpy, sys, os
a = sys.argv[sys.argv.index("--")+1:]
out, w, h, spp = a[0], int(a[1]), int(a[2]), int(a[3]); frames = (list(range(int(a[4].split("-")[0]), int(a[4].split("-")[1]) + 1)) if "-" in a[4] else [int(x) for x in a[4].split(",")])
s = bpy.data.scenes["Sahne3D"]
if "Montaj" in bpy.data.scenes: bpy.data.scenes.remove(bpy.data.scenes["Montaj"])
bpy.context.window_manager.windows[0].scene = s if bpy.context.window_manager.windows else None
s.render.engine = "CYCLES"; s.cycles.device = "CPU"; s.cycles.samples = spp
s.cycles.use_denoising = True; s.cycles.max_bounces = 4; s.cycles.use_adaptive_sampling = True
s.render.resolution_x, s.render.resolution_y = w, h
s.render.use_persistent_data = True
s.render.image_settings.file_format = "PNG"
for f in frames:
    s.frame_set(f); s.render.filepath = os.path.join(out, "f%04d.png" % f)
    if os.path.exists(s.render.filepath): continue
    bpy.ops.render.render(write_still=True, scene=s.name)
