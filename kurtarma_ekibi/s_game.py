"""'Bu kim?' oyunu (40 s): a silhouette + its sound, then the lights reveal who it is."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from lib import *
from vehicles import *
import cards as cd
from story import driver_card

N = 960
PER = 192
s = reset(N)
cd.reset_cards()
world(top=(0.02, 0.02, 0.05), horizon=(0.05, 0.03, 0.1), light=0.0)
bd = box("backdrop", (40, 1, 18), (0, 8, 7), None, bevel=0)
bm = bpy.data.materials.new("backdrop"); bm.use_nodes = True
nt = bm.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission")
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (1.0, 0.75, 0.25, 1); ramp.color_ramp.elements[1].color = (0.55, 0.25, 0.95, 1)
ramp.color_ramp.elements[0].position = 0.25; ramp.color_ramp.elements[1].position = 0.75
nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], ramp.inputs[0])
nt.links.new(ramp.outputs[0], em.inputs[0]); em.inputs[1].default_value = 1.6; nt.links.new(em.outputs[0], out.inputs[0])
bd.data.materials.append(bm)
box("floor", (60, 30, 0.2), (0, 0, -0.1), mat("stagefloor", (0.25, 0.12, 0.4), rough=0.5), bevel=0)
cyl("podium", 4.2, 0.4, (0, 0, 0.2), mat("podium", (0.95, 0.3, 0.5), rough=0.3), verts=48, bevel=0.08)
cyl("podium_rim", 4.3, 0.12, (0, 0, 0.06), mat("podrim", (1, 0.85, 0.2), rough=0.3, emit=0.6), verts=48)
for i in range(14):
    a = i / 14 * math.pi
    sphere("bulb", 0.18, (math.cos(a) * 9.5, 7.3, 1.0 + math.sin(a) * 7.5), mat("bulb", (1, 0.95, 0.7), emit=4.0))
sd = bpy.data.lights.new("Spot", "SPOT"); sd.energy = 0.0; sd.spot_size = math.radians(55); sd.spot_blend = 0.4
spot = bpy.data.objects.new("Spot", sd); spot.location = (0, -9, 9); bpy.context.scene.collection.objects.link(spot)
tg = empty("spot_tgt", (0, 0, 1.2)); c = spot.constraints.new("TRACK_TO"); c.target = tg; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
fd = bpy.data.lights.new("Fill", "SUN"); fd.energy = 0.0
fill = bpy.data.objects.new("Fill", fd); fill.rotation_euler = (math.radians(55), 0, math.radians(-20)); bpy.context.scene.collection.objects.link(fill)


def light_key(f, on):
    sd.energy = 4000.0 if on else 0.0; sd.keyframe_insert("energy", frame=f)
    fd.energy = 2.5 if on else 0.0; fd.keyframe_insert("energy", frame=f)


light_key(0, False)
cam = camera("cam", [(0, (0, -13.5, 3.6), (0, 0, 2.4)), (N, (0, -12.5, 3.5), (0, 0, 2.4))], lens=30)
cut(0, cam)
qm = mat("qmark", (1.0, 0.85, 0.1), rough=0.2, emit=1.2)
nm = mat("nametext", (1, 1, 1), rough=0.3, emit=0.6)
items = [("veh", make_police, "burak", "POLİS ARABASI", "siren_police"),
         ("veh", make_firetruck, "kemal", "İTFAİYE", "siren_fire"),
         ("veh", make_recycler, "murat", "GERİ DÖNÜŞÜM KAMYONU", "truck_beep"),
         ("card", "pamuk", None, "PAMUK", "baa"),
         ("card", "cimcime", None, "CİMCİME", "monkey")]
for i, (kind, what, drv, name, snd) in enumerate(items):
    f0 = i * PER
    if kind == "veh":
        v = what()
        dc = driver_card(v, drv)
        dc.silhouette(f0, f0 + 120)
        v.root.rotation_euler.z = math.radians(-20)
        keys(v.root, "location", [(0, (18, 0, 0.4)), (f0, (18, 0, 0.4)), (f0 + 24, (0, 0, 0.4)), (f0 + 172, (0, 0, 0.4)), (f0 + 190, (-18, 0, 0.4))])
        roll_wheels(v, f0, f0 + PER - 1)
        wiggle_happy(v, f0 + 136, n=3, h=0.3)
        for k, m in enumerate(v.lights):
            flash(m, f0 + 122, f0 + 180, period=10, on=9, phase=k)
        dc.wiggle(f0 + 130, f0 + 180, a=6)
    else:
        cc = cd.char(what, (18, 0, 0.4), height=2.2)
        cc.at(f0, 18, 0).walk_to(f0, f0 + 24, 0, -0.4)
        cc.silhouette(f0, f0 + 120)
        cc.cheer(f0 + 128, n=3)
        cc.walk_to(f0 + 172, f0 + 190, -18, -0.4)
        cc.zpath = [(0, 0.4)]
    sfx(f0 + 2, "whoosh", vol=0.7)
    q = text(f"q{i}", "?", 2.0, (0, -0.5, 4.0), qm, font=FONT_SYM, extrude=0.25, bevel=0.06)
    key(q, "scale", 0, (0.001,) * 3)
    pop_in(q, f0 + 28, 8)
    for ff in range(f0 + 40, f0 + 112, 16):
        keys(q, "rotation_euler", [(ff, (math.radians(90), 0, math.radians(-12))), (ff + 8, (math.radians(90), 0, math.radians(12))), (ff + 16, (math.radians(90), 0, math.radians(-12)))])
    pop_out(q, f0 + 118, 6)
    sfx(f0 + 28, "question")
    sfx(f0 + 42, snd, dur=2.0)
    sfx(f0 + 84, snd, dur=2.0)
    light_key(f0 + 119, False); light_key(f0 + 121, True); light_key(f0 + 178, True); light_key(f0 + 186, False)
    sfx(f0 + 121, "tada")
    stars_burst((0, -1.0, 3.2), f0 + 123, n=10, face_rot=math.radians(-90), radius=3.0)
    confetti((0, -1.0, 4.5), f0 + 123, n=40, spread=4.5, height=3.0, seed=i + 40)
    sfx(f0 + 125, "confetti")
    t = text(f"name{i}", name, 0.95 if len(name) < 14 else 0.7, (0, -2.6, 4.15), nm, extrude=0.12, bevel=0.03)
    key(t, "scale", 0, (0.001,) * 3)
    pop_in(t, f0 + 128, 8)
    pop_out(t, f0 + 172, 6)
    sfx(f0 + 140, snd, dur=1.2, vol=0.6)
cd.finish_all(N)
render("k_game")
