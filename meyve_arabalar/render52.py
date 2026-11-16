"""Render the animation of a .blend with Blender 5.2's Python (skips frames that already exist):  python render52.py <file.blend>"""
import bpy, sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
bpy.ops.render.render(animation=True)
