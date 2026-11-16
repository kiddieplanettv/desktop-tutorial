"""Join the rendered frames of the toy video into one MP4 with the ready-made soundtrack (needs ffmpeg on the PATH).
blender -b -P birlestir.py      or      python birlestir.py"""
import os, subprocess, glob
HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(HERE, "build")
SEGS = ["t_intro", "t_ep1", "t_ep2", "t_ep3", "t_ep4", "t_outro"]
lst = os.path.join(B, "_pc_concat.txt")
with open(lst, "w") as f:
    for seg in SEGS:
        n = len(glob.glob(os.path.join(B, seg, "f_*.png")))
        out = os.path.join(B, seg + ".mp4")
        subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-framerate", "24", "-i", os.path.join(B, seg, "f_%04d.png"),
                               "-vf", f"fade=in:0:10,fade=out:{n - 10}:10", "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", out])
        f.write(f"file '{seg}.mp4'\n")
        print("OK", seg, n, "kare")
final = os.path.join(HERE, "Minik_Ustalar_6dk.mp4")
subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                       "-i", os.path.join(HERE, "ses", "Minik_Ustalar_ses.m4a"), "-c:v", "copy", "-c:a", "copy", "-shortest", final])
print("HAZIR:", final)
