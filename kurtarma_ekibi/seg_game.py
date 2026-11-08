"""Sound game (45 s): a dark silhouette + its sound, guess, then the lights reveal it."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
from lib import *
from vehicles import *
import people as pp

N = 1080
PER = 216
s = reset(N)
world(top=(0.02, 0.02, 0.05), horizon=(0.05, 0.03, 0.1), light=0.0)
s.eevee.use_soft_shadows = True

# stage: glowing backdrop + podium
bd = box("backdrop", (40, 1, 18), (0, 8, 7), None, bevel=0)
bm = bpy.data.materials.new("backdrop")
bm.use_nodes = True
nt = bm.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
em = nt.nodes.new("ShaderNodeEmission")
tc = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color = (1.0, 0.75, 0.25, 1)
ramp.color_ramp.elements[1].color = (0.55, 0.25, 0.95, 1)
ramp.color_ramp.elements[0].position = 0.25
ramp.color_ramp.elements[1].position = 0.75
nt.links.new(tc.outputs["Generated"], sep.inputs[0])
nt.links.new(sep.outputs["Z"], ramp.inputs[0])
nt.links.new(ramp.outputs[0], em.inputs[0])
em.inputs[1].default_value = 1.6
nt.links.new(em.outputs[0], out.inputs[0])
bd.data.materials.append(bm)
floor = box("floor", (60, 30, 0.2), (0, 0, -0.1), mat("stagefloor", (0.25, 0.12, 0.4), rough=0.5), bevel=0)
pod = cyl("podium", 4.2, 0.4, (0, 0, 0.2), mat("podium", (0.95, 0.3, 0.5), rough=0.3), verts=48, bevel=0.08)
cyl("podium_rim", 4.3, 0.12, (0, 0, 0.06), mat("podrim", (1, 0.85, 0.2), rough=0.3, emit=0.6), verts=48)
for i in range(14):
    a = i / 14 * math.pi
    sphere("bulb", 0.18, (math.cos(a) * 9.5, 7.3, 1.0 + math.sin(a) * 7.5), mat("bulb", (1, 0.95, 0.7), emit=4.0))

# lights: everything is dark until the reveal
sd = bpy.data.lights.new("Spot", "SPOT")
sd.energy = 0.0
sd.spot_size = math.radians(55)
sd.spot_blend = 0.4
sd.shadow_soft_size = 1.0
spot = bpy.data.objects.new("Spot", sd)
spot.location = (0, -9, 9)
bpy.context.scene.collection.objects.link(spot)
tgt = empty("spot_tgt", (0, 0, 1.2))
c = spot.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
fill_d = bpy.data.lights.new("Fill", "SUN")
fill_d.energy = 0.0
fill = bpy.data.objects.new("Fill", fill_d)
fill.rotation_euler = (math.radians(55), 0, math.radians(-20))
bpy.context.scene.collection.objects.link(fill)

def light_key(f, on):
    sd.energy = 4000.0 if on else 0.0
    sd.keyframe_insert("energy", frame=f)
    fill_d.energy = 2.5 if on else 0.0
    fill_d.keyframe_insert("energy", frame=f)

light_key(0, False)

cam = camera("cam", [(0, (0, -13.5, 3.6), (0, 0, 2.5)), (N, (0, -12.5, 3.5), (0, 0, 2.5))], lens=30)
cut(0, cam)

makers = [make_police, make_ambulance, make_firetruck, make_towtruck, make_helicopter]
names = ["POLİS ARABASI", "AMBULANS", "İTFAİYE", "ÇEKİCİ", "HELİKOPTER"]
sounds = ["siren_police", "siren_ambulance", "siren_fire", "siren_tow", "heli"]
qm = mat("qmark", (1.0, 0.85, 0.1), rough=0.2, emit=1.2)
nm = mat("nametext", (1, 1, 1), rough=0.3, emit=0.6)
headlight = bpy.data.materials.get("headlight")

for i, mk in enumerate(makers):
    f0 = i * PER
    v = mk()
    hm = bpy.data.materials["headlight"]
    v.root.rotation_euler.z = math.radians(-20)
    on_x, z = 0.0, 0.4
    if v.kind == "heli":
        z = 0.4
        keys(v.root, "location", [(0, (16, 0, 6)), (f0, (16, 0, 6)), (f0 + 26, (on_x, 0, z)), (f0 + 194, (on_x, 0, z)), (f0 + 214, (-16, 0, 6))])
        spin(v.parts["rotor"], f0, f0 + PER, 2.4)
        spin(v.parts["tail_rotor"], f0, f0 + PER, 4.0, axis=1)
    else:
        keys(v.root, "location", [(0, (18, 0, z)), (f0, (18, 0, z)), (f0 + 26, (on_x, 0, z)), (f0 + 194, (on_x, 0, z)), (f0 + 214, (-18, 0, z))])
        keys(v.root, "rotation_euler", [(f0 + 26, (0, 0, math.radians(-20))), (f0 + 194, (0, 0, math.radians(-20))), (f0 + 196, (0, 0, math.radians(0)))])
        roll_wheels(v, f0, f0 + PER - 1)
    sfx(f0 + 2, "whoosh", vol=0.7)
    q = text(f"q{i}", "?", 2.2, (0, -0.5, 4.7), qm, font=FONT_SYM, extrude=0.25, bevel=0.06)
    key(q, "scale", 0, (0.001,) * 3)
    pop_in(q, f0 + 30, 8)
    for ff in range(f0 + 44, f0 + 124, 16):
        keys(q, "rotation_euler", [(ff, (math.radians(90), 0, math.radians(-12))), (ff + 8, (math.radians(90), 0, math.radians(12))), (ff + 16, (math.radians(90), 0, math.radians(-12)))])
    pop_out(q, f0 + 130, 6)
    sfx(f0 + 30, "question")
    sfx(f0 + 46, sounds[i], dur=2.2)
    sfx(f0 + 92, sounds[i], dur=2.2)
    # reveal
    light_key(f0 + 129, False)
    light_key(f0 + 132, True)
    light_key(f0 + 200, True)
    light_key(f0 + 208, False)
    sfx(f0 + 132, "tada")
    stars_burst((0, -1.0, 3.2), f0 + 134, n=10, face_rot=math.radians(-90), radius=3.0)
    confetti((0, -1.0, 4.5), f0 + 134, n=45, spread=4.5, height=3.0, seed=i + 40)
    sfx(f0 + 136, "confetti")
    t = text(f"name{i}", names[i], 0.95, (0, -2.6, 4.9), nm, extrude=0.12, bevel=0.03)
    key(t, "scale", 0, (0.001,) * 3)
    pop_in(t, f0 + 140, 8)
    pop_out(t, f0 + 194, 6)
    for e in v.eyes:
        keys(e, "scale", [(0, (1, 1, 1)), (f0 + 128, (1, 1, 1)), (f0 + 131, (1, 1, 0.08)), (f0 + 136, (1, 1, 1))])
    auto_blink(v.eyes, f0 + 140, f0 + PER, seed=i + 60)
    wiggle_happy(v, f0 + 146, n=3, h=0.35)
    pp.wave(v.driver, f0 + 140, f0 + 196, side="r", seated=True)
    pp.auto_blink(v.driver, f0 + 130, f0 + PER, i + 70)
    sfx(f0 + 150, sounds[i], dur=1.3, vol=0.6)
    for k, m in enumerate(v.lights):
        flash(m, f0 + 132, f0 + 200, period=10, on=9, phase=k)
render("game")
