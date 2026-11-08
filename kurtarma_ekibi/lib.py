"""Shared Blender building blocks for the "Kurtarma Ekibi" kids video.

Everything is procedural: run segment scripts with
    blender -b -P seg_xxx.py -- <args>
"""
import bpy, bmesh, math, random, json, os
from mathutils import Vector, Euler

FPS = 24
HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")
FONT_TEXT = "/usr/share/fonts/truetype/comfortaa/Comfortaa-Bold.ttf"
FONT_SYM = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ----------------------------------------------------------------------------
# scene / render setup
# ----------------------------------------------------------------------------

def reset(frames, res=(960, 540), samples=8):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = "BLENDER_EEVEE"
    s.render.resolution_x, s.render.resolution_y = res
    s.render.resolution_percentage = 100
    s.render.fps = FPS
    s.frame_start, s.frame_end = 0, frames - 1
    e = s.eevee
    e.taa_render_samples = samples
    e.use_gtao = True
    e.gtao_distance = 1.5
    e.use_bloom = True
    e.bloom_intensity = 0.04
    e.bloom_threshold = 1.2
    e.use_soft_shadows = True
    e.shadow_cascade_size = "2048"
    e.shadow_cube_size = "512"
    s.view_settings.view_transform = "Standard"
    s.view_settings.look = "None"
    s.view_settings.exposure = 0.0
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_mode = "RGB"
    _MATS.clear()
    EVENTS.clear()
    return s


def world(top=(0.12, 0.42, 0.95), horizon=(0.62, 0.84, 1.0), light=0.55):
    w = bpy.data.worlds.new("World")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*horizon, 1)
    ramp.color_ramp.elements[1].position = 0.45
    ramp.color_ramp.elements[1].color = (*top, 1)
    bg_cam = nt.nodes.new("ShaderNodeBackground")
    bg_light = nt.nodes.new("ShaderNodeBackground")
    bg_light.inputs[0].default_value = (0.85, 0.92, 1.0, 1)
    bg_light.inputs[1].default_value = light
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(ramp.outputs[0], bg_cam.inputs[0])
    nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(bg_light.outputs[0], mix.inputs[1])
    nt.links.new(bg_cam.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    # Generated Z for the world goes from 0.5 at horizon up to 1 at zenith;
    # remap: use a math node so the gradient fills the visible sky.
    m = nt.nodes.new("ShaderNodeMapRange")
    m.inputs["From Min"].default_value = 0.5
    m.inputs["From Max"].default_value = 1.0
    nt.links.new(sep.outputs["Z"], m.inputs["Value"])
    nt.links.new(m.outputs[0], ramp.inputs[0])
    return w


def sun(energy=5.0, rot=(math.radians(50), math.radians(10), math.radians(35)), angle=6):
    d = bpy.data.lights.new("Sun", "SUN")
    d.energy = energy
    d.angle = math.radians(angle)
    d.color = (1.0, 0.96, 0.88)
    o = bpy.data.objects.new("Sun", d)
    o.rotation_euler = rot
    bpy.context.scene.collection.objects.link(o)
    return o

# ----------------------------------------------------------------------------
# materials
# ----------------------------------------------------------------------------
_MATS = {}


def mat(name, color, rough=0.4, emit=0.0, alpha=1.0, spec=0.4, unique=False):
    key = name
    if not unique and key in _MATS:
        return _MATS[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    c = (*color, 1) if len(color) == 3 else color
    p.inputs["Base Color"].default_value = c
    p.inputs["Roughness"].default_value = rough
    p.inputs["Specular IOR Level"].default_value = spec
    p.inputs["Emission Color"].default_value = c
    p.inputs["Emission Strength"].default_value = emit
    if alpha < 1.0:
        p.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
        m.shadow_method = "NONE"
    m.diffuse_color = c
    if not unique:
        _MATS[key] = m
    return m


def emit_key(m, frame, strength):
    p = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    p.default_value = strength
    p.keyframe_insert("default_value", frame=frame)


def flash(m, f0, f1, period=8, on=8.0, off=0.0, phase=0):
    """Square-wave flash of an emissive material between f0 and f1."""
    emit_key(m, f0 - 1, off)
    f = f0
    i = phase
    while f < f1:
        emit_key(m, f, on if i % 2 == 0 else off)
        f += period // 2
        i += 1
    emit_key(m, f1, off)
    _constant(m.node_tree.animation_data.action)


def _constant(action):
    for fc in action.fcurves:
        for k in fc.keyframe_points:
            k.interpolation = "CONSTANT"

# palette
C = dict(
    red=(0.9, 0.08, 0.06), blue=(0.05, 0.3, 0.95), white=(0.95, 0.95, 0.95),
    yellow=(1.0, 0.78, 0.05), orange=(1.0, 0.42, 0.02), green=(0.25, 0.75, 0.15),
    grass=(0.32, 0.72, 0.18), dark=(0.04, 0.04, 0.05), road=(0.16, 0.16, 0.19),
    glass=(0.55, 0.85, 1.0), pink=(1.0, 0.45, 0.6), purple=(0.55, 0.2, 0.85),
    brown=(0.45, 0.24, 0.1), cream=(1.0, 0.92, 0.75), teal=(0.1, 0.7, 0.7),
    gray=(0.55, 0.55, 0.6), lightgray=(0.85, 0.85, 0.88), skin=(1.0, 0.75, 0.6),
)

# ----------------------------------------------------------------------------
# geometry helpers
# ----------------------------------------------------------------------------

def _link(o, parent=None):
    bpy.context.scene.collection.objects.link(o)
    if parent is not None:
        o.parent = parent
    return o


def empty(name, loc=(0, 0, 0), parent=None, rot=(0, 0, 0)):
    o = bpy.data.objects.new(name, None)
    o.location = loc
    o.rotation_euler = rot
    o.empty_display_size = 0.5
    return _link(o, parent)


def _mesh_obj(name, bm, m, parent, loc, rot=(0, 0, 0), smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        me.shade_smooth()
    o = bpy.data.objects.new(name, me)
    o.location = loc
    o.rotation_euler = rot
    if m is not None:
        me.materials.append(m)
    return _link(o, parent)


def box(name, size, loc=(0, 0, 0), m=None, parent=None, bevel=0.08, rot=(0, 0, 0), segs=3):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    o = _mesh_obj(name, bm, m, parent, loc, rot, smooth=False)
    if bevel > 0:
        b = o.modifiers.new("bev", "BEVEL")
        b.width = min(bevel, min(size) * 0.49)
        b.segments = segs
        b.limit_method = "NONE"
        b.harden_normals = False
        o.data.shade_smooth()
        o.data.use_auto_smooth = True
        o.data.auto_smooth_angle = math.radians(40)
    return o


def sphere(name, r=1.0, loc=(0, 0, 0), m=None, parent=None, scale=(1, 1, 1), segs=24, rings=14, rot=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    o = _mesh_obj(name, bm, m, parent, loc, rot)
    o.scale = scale
    return o


def cyl(name, r=1.0, depth=1.0, loc=(0, 0, 0), m=None, parent=None, rot=(0, 0, 0), verts=24, r2=None, bevel=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts,
                          radius1=r, radius2=r if r2 is None else r2, depth=depth)
    o = _mesh_obj(name, bm, m, parent, loc, rot, smooth=True)
    o.data.use_auto_smooth = True
    o.data.auto_smooth_angle = math.radians(40)
    if bevel > 0:
        b = o.modifiers.new("bev", "BEVEL")
        b.width = bevel
        b.segments = 3
        b.limit_method = "ANGLE"
    return o


def torus(name, R=1.0, r=0.1, loc=(0, 0, 0), m=None, parent=None, rot=(0, 0, 0), half=None):
    """half: None | 'low' (smile) | 'high' (frown); arc lies in local XZ plane."""
    bm = bmesh.new()
    seg, mseg = 32, 10
    verts = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        ring = []
        for j in range(mseg):
            b = 2 * math.pi * j / mseg
            x = (R + r * math.cos(b)) * math.cos(a)
            z = (R + r * math.cos(b)) * math.sin(a)
            y = r * math.sin(b)
            ring.append(bm.verts.new((x, y, z)))
        verts.append(ring)
    for i in range(seg):
        for j in range(mseg):
            a = verts[i][j]; b2 = verts[(i + 1) % seg][j]
            c = verts[(i + 1) % seg][(j + 1) % mseg]; d = verts[i][(j + 1) % mseg]
            bm.faces.new((a, b2, c, d))
    if half:
        kill = [v for v in bm.verts if (v.co.z > -R * 0.25 if half == "low" else v.co.z < R * 0.25)]
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
    return _mesh_obj(name, bm, m, parent, loc, rot)


def cone(name, r=1.0, depth=1.0, loc=(0, 0, 0), m=None, parent=None, rot=(0, 0, 0), verts=24):
    return cyl(name, r, depth, loc, m, parent, rot, verts, r2=0.0)


def text(name, body, size=1.0, loc=(0, 0, 0), m=None, parent=None, rot=(math.radians(90), 0, 0),
         extrude=0.08, bevel=0.03, font=FONT_TEXT, align="CENTER"):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.font = bpy.data.fonts.load(font, check_existing=True)
    cu.size = size
    cu.extrude = extrude
    cu.bevel_depth = bevel
    cu.bevel_resolution = 2
    cu.align_x = align
    cu.align_y = "CENTER"
    o = bpy.data.objects.new(name, cu)
    o.location = loc
    o.rotation_euler = rot
    if m is not None:
        cu.materials.append(m)
    return _link(o, parent)

# ----------------------------------------------------------------------------
# animation helpers
# ----------------------------------------------------------------------------

def key(o, path, f, v, interp=None):
    setattr(o, path, v)
    o.keyframe_insert(path, frame=f)
    if interp:
        for fc in o.animation_data.action.fcurves:
            if fc.data_path == path:
                for k in fc.keyframe_points:
                    if abs(k.co[0] - f) < 0.01:
                        k.interpolation = interp


def keys(o, path, seq, interp=None):
    for f, v in seq:
        key(o, path, f, v, interp)


def bake(o, path, frames, values):
    """Fast bulk keyframing: values is list of tuples (or floats)."""
    if o.animation_data is None:
        o.animation_data_create()
    if o.animation_data.action is None:
        o.animation_data.action = bpy.data.actions.new(o.name + "Act")
    act = o.animation_data.action
    n = len(values[0]) if hasattr(values[0], "__len__") else 1
    for i in range(n):
        fc = act.fcurves.find(path, index=i)
        if fc is None:
            fc = act.fcurves.new(path, index=i)
        existing = [(k.co[0], k.co[1]) for k in fc.keyframe_points
                    if not (frames[0] <= k.co[0] <= frames[-1])]
        pts = existing + [(f, (v[i] if n > 1 else v)) for f, v in zip(frames, values)]
        pts.sort()
        fc.keyframe_points.clear()
        fc.keyframe_points.add(len(pts))
        flat = [c for p in pts for c in p]
        fc.keyframe_points.foreach_set("co", flat)
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR"
        fc.update()


def evalv(o, path, f, n=3):
    """Evaluate animated vector property without depsgraph."""
    base = list(getattr(o, path))
    ad = o.animation_data
    if ad and ad.action:
        for i in range(n):
            fc = ad.action.fcurves.find(path, index=i)
            if fc:
                base[i] = fc.evaluate(f)
    return Vector(base)


def world_pos(o, f):
    """Approximate world position (supports one level of animated parent)."""
    loc = evalv(o, "location", f)
    rot = evalv(o, "rotation_euler", f)
    p = o.parent
    if p is None:
        return loc, rot
    ploc, prot = world_pos(p, f)
    loc.rotate(Euler(prot))
    return ploc + loc, Vector(prot) + rot


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return Vector(a).lerp(Vector(b), t)


def pop_in(o, f, dur=8, s=1.0):
    keys(o, "scale", [(f - 1, (0.001,) * 3), (f + dur, (s * 1.2,) * 3), (f + dur + 4, (s,) * 3)])


def pop_out(o, f, dur=6, s=1.0):
    keys(o, "scale", [(f, (s,) * 3), (f + dur, (0.001,) * 3)])


def hidden(o, f0=None):
    """Start an object invisible (scale ~0)."""
    key(o, "scale", 0, (0.001,) * 3)


def _kz(o, f, z):
    o.location.z = z
    o.keyframe_insert("location", index=2, frame=f)


EVENTS = []


def sfx(frame, name, **kw):
    EVENTS.append(dict(frame=int(frame), name=name, **kw))


def save_events(seg):
    os.makedirs(BUILD, exist_ok=True)
    with open(os.path.join(BUILD, seg + "_events.json"), "w") as fh:
        json.dump(dict(frames=bpy.context.scene.frame_end + 1, events=EVENTS), fh, indent=1)

# ----------------------------------------------------------------------------
# cameras
# ----------------------------------------------------------------------------

def camera(name, keys_, lens=35):
    """keys_: list of (frame, cam_loc, target_loc)."""
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_end = 600
    c = bpy.data.objects.new(name, cd)
    _link(c)
    t = empty(name + "_tgt")
    for f, cl, tl in keys_:
        key(c, "location", f, cl)
        key(t, "location", f, tl)
    con = c.constraints.new("TRACK_TO")
    con.target = t
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    return c


def cut(frame, cam):
    m = bpy.context.scene.timeline_markers.new(cam.name, frame=frame)
    m.camera = cam
    if frame == 0:
        bpy.context.scene.camera = cam


def follow_cam(name, target, f0, f1, offset, look_offset=(0, 0, 1), step=2, lens=35):
    """Camera that follows an animated object."""
    ks = []
    for f in range(f0, f1 + 1, step):
        p, _ = world_pos(target, f)
        ks.append((f, p + Vector(offset), p + Vector(look_offset)))
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_end = 600
    c = bpy.data.objects.new(name, cd)
    _link(c)
    t = empty(name + "_tgt")
    frames = [k[0] for k in ks]
    bake(c, "location", frames, [tuple(k[1]) for k in ks])
    bake(t, "location", frames, [tuple(k[2]) for k in ks])
    con = c.constraints.new("TRACK_TO")
    con.target = t
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    return c

# ----------------------------------------------------------------------------
# faces
# ----------------------------------------------------------------------------

def eyes(parent, center, spacing=0.5, size=0.28, look=(1, 0, 0), name="eye"):
    """Cartoon eyes facing +X of parent. Returns list of eye empties (for blinking)."""
    out = []
    white = mat("eyewhite", C["white"], rough=0.2)
    black = mat("pupil", C["dark"], rough=0.15)
    for side in (-1, 1):
        e = empty(f"{name}{side}", (center[0], center[1] + side * spacing / 2, center[2]), parent)
        sphere(f"{name}W{side}", size, (0, 0, 0), white, e, scale=(0.45, 0.85, 1.0))
        p = sphere(f"{name}P{side}", size * 0.55, (size * 0.32, 0.0, -size * 0.05), black, e, scale=(0.45, 1, 1))
        sphere(f"{name}H{side}", size * 0.16, (size * 0.5, -size * 0.12, size * 0.18), white, e)
        out.append(e)
    return out


def blink(eye_list, frames):
    for f in frames:
        for e in eye_list:
            keys(e, "scale", [(f, (1, 1, 1)), (f + 2, (1, 1, 0.08)), (f + 5, (1, 1, 1))])


def auto_blink(eye_list, f0, f1, seed=1):
    r = random.Random(seed)
    f = f0 + r.randint(20, 60)
    fs = []
    while f < f1 - 6:
        fs.append(f)
        f += r.randint(55, 110)
    blink(eye_list, fs)


def mouth(parent, loc, R=0.2, r=0.035, happy=True, name="mouth", rot=(0, 0, 0)):
    m = mat("mouth", (0.35, 0.02, 0.05), rough=0.3)
    # arc in local XZ plane, rotate so it faces +X
    return torus(name, R, r, loc, m, parent, rot=(rot[0], rot[1], rot[2] + math.radians(90)),
                 half="low" if happy else "high")


def swap_mouth(happy_obj, sad_obj, f):
    keys(sad_obj, "scale", [(f - 1, (1, 1, 1)), (f + 3, (0.001,) * 3)])
    keys(happy_obj, "scale", [(f - 1, (0.001,) * 3), (f + 4, (1.2, 1.2, 1.2)), (f + 7, (1, 1, 1))])

# ----------------------------------------------------------------------------
# vehicles (all face +X, origin on ground at center)
# ----------------------------------------------------------------------------

class Vehicle:
    def __init__(self, kind):
        self.kind = kind
        self.root = None
        self.body = None
        self.wheels = []
        self.wheel_r = 0.45
        self.lights = []      # emissive materials that flash
        self.eyes = []
        self.parts = {}


def _wheels(v, xs, half_w, r=0.45, w=0.38):
    tire = mat("tire", (0.06, 0.06, 0.07), rough=0.7)
    hub = mat("hub", C["lightgray"], rough=0.25)
    for x in xs:
        for s in (-1, 1):
            wh = empty(f"{v.kind}_wheel", (x, s * half_w, r), v.body)
            cyl("tire", r, w, (0, 0, 0), tire, wh, rot=(math.radians(90), 0, 0), bevel=0.08)
            cyl("hub", r * 0.5, w + 0.04, (0, 0, 0), hub, wh, rot=(math.radians(90), 0, 0), bevel=0.03)
            v.wheels.append(wh)
    v.wheel_r = r


def _lightbar(v, x, z, w=1.0, name="bar", colors=("red", "blue")):
    base = mat("barbase", C["lightgray"], rough=0.3)
    box(f"{v.kind}_barbase", (0.5, w + 0.2, 0.12), (x, 0, z), base, v.body, bevel=0.05)
    for i, cn in enumerate(colors):
        m = mat(f"{v.kind}_{cn}_light{i}", C[cn], rough=0.2, emit=0.0, unique=True)
        y = (-1 if i == 0 else 1) * w / 4
        box(f"{v.kind}_light{i}", (0.42, w / 2 - 0.05, 0.3), (x, y, z + 0.18), m, v.body, bevel=0.1)
        v.lights.append(m)


def _headlights(v, x, y, z, r=0.14):
    m = mat("headlight", (1, 0.95, 0.7), rough=0.1, emit=1.5)
    for s in (-1, 1):
        sphere("headlight", r, (x, s * y, z), m, v.body, scale=(0.5, 1, 1))


def make_police():
    v = Vehicle("police")
    v.root = empty("police")
    v.body = empty("police_body", parent=v.root)
    blue = mat("police_blue", (0.06, 0.25, 0.85), rough=0.3)
    white = mat("police_white", C["white"], rough=0.3)
    glass = mat("glass", C["glass"], rough=0.05, spec=0.8)
    box("p_low", (3.4, 1.8, 0.75), (0, 0, 0.78), blue, v.body, bevel=0.28)
    box("p_door", (1.6, 1.84, 0.45), (-0.15, 0, 0.82), white, v.body, bevel=0.15)
    box("p_cab", (1.9, 1.6, 0.85), (-0.25, 0, 1.5), white, v.body, bevel=0.3)
    box("p_wind", (0.12, 1.4, 0.68), (0.66, 0, 1.52), glass, v.body, bevel=0.05, rot=(0, math.radians(-12), 0))
    for s in (-1, 1):
        box("p_sidewin", (1.2, 0.06, 0.5), (-0.35, s * 0.8, 1.55), glass, v.body, bevel=0.04)
    v.eyes = eyes(v.body, (0.78, 0, 1.55), spacing=0.62, size=0.3)
    mouth(v.body, (1.72, 0, 0.72), R=0.28, r=0.045)
    _headlights(v, 1.68, 0.62, 0.9)
    _lightbar(v, -0.25, 1.98, w=1.3)
    _wheels(v, (1.05, -1.1), 0.88)
    text("p_txt", "POLİS", 0.32, (-0.15, -0.93, 0.85), white, v.body, rot=(math.radians(90), 0, 0), extrude=0.02, bevel=0.0)
    text("p_txt2", "POLİS", 0.32, (-0.15, 0.93, 0.85), white, v.body, rot=(math.radians(90), 0, math.radians(180)), extrude=0.02, bevel=0.0)
    return v


def make_ambulance():
    v = Vehicle("ambulance")
    v.root = empty("ambulance")
    v.body = empty("ambulance_body", parent=v.root)
    white = mat("amb_white", (0.97, 0.97, 0.97), rough=0.3)
    red = mat("amb_red", C["red"], rough=0.3)
    glass = mat("glass", C["glass"], rough=0.05, spec=0.8)
    box("a_box", (2.5, 2.0, 2.0), (-0.65, 0, 1.55), white, v.body, bevel=0.3)
    box("a_cab", (1.3, 1.9, 1.25), (1.1, 0, 1.15), white, v.body, bevel=0.32)
    box("a_wind", (0.12, 1.6, 0.6), (1.72, 0, 1.45), glass, v.body, bevel=0.05, rot=(0, math.radians(-15), 0))
    for s in (-1, 1):
        box("a_stripe", (3.75, 0.04, 0.22), (0.0, s * 1.0, 0.95), red, v.body, bevel=0.02)
        e = empty("cross", (-0.65, s * 1.02, 1.85), v.body)
        box("crossA", (0.75, 0.05, 0.22), (0, 0, 0), red, e, bevel=0.03)
        box("crossB", (0.22, 0.05, 0.75), (0, 0, 0), red, e, bevel=0.03)
    v.eyes = eyes(v.body, (1.83, 0, 1.47), spacing=0.68, size=0.3)
    mouth(v.body, (1.78, 0, 0.75), R=0.28, r=0.045)
    _headlights(v, 1.74, 0.68, 0.95)
    _lightbar(v, 0.3, 2.6, w=1.4, colors=("red", "red"))
    _wheels(v, (1.05, -1.25), 0.95)
    return v


def make_firetruck():
    v = Vehicle("fire")
    v.root = empty("fire")
    v.body = empty("fire_body", parent=v.root)
    red = mat("fire_red", (0.92, 0.07, 0.05), rough=0.28)
    silver = mat("silver", (0.8, 0.82, 0.86), rough=0.2, spec=0.8)
    glass = mat("glass", C["glass"], rough=0.05, spec=0.8)
    yel = mat("fire_yel", C["yellow"], rough=0.3)
    box("f_base", (4.8, 2.0, 0.9), (-0.3, 0, 0.95), red, v.body, bevel=0.25)
    box("f_cab", (1.5, 1.95, 1.3), (1.25, 0, 1.85), red, v.body, bevel=0.32)
    box("f_wind", (0.12, 1.65, 0.62), (1.98, 0, 2.05), glass, v.body, bevel=0.05, rot=(0, math.radians(-12), 0))
    box("f_rear", (2.9, 1.9, 0.55), (-1.05, 0, 1.65), red, v.body, bevel=0.2)
    for s in (-1, 1):
        box("f_stripe", (4.85, 0.04, 0.16), (-0.3, s * 1.01, 1.05), yel, v.body, bevel=0.02)
    v.eyes = eyes(v.body, (2.1, 0, 2.08), spacing=0.7, size=0.32)
    mouth(v.body, (2.08, 0, 0.88), R=0.3, r=0.05)
    _headlights(v, 2.05, 0.7, 1.1)
    _lightbar(v, 1.15, 2.55, w=1.4)
    _wheels(v, (1.3, -0.6, -1.75), 0.95, r=0.5)
    # ladder: pivot at rear top; rails run toward +X when lowered
    piv = empty("ladder_pivot", (-2.2, 0, 2.05), v.body)
    cyl("lad_turret", 0.45, 0.3, (0, 0, -0.05), silver, piv, verts=20)
    lad = empty("ladder_main", (0, 0, 0.15), piv)
    lad2 = empty("ladder_ext", (0, 0, 0.12), lad)
    for L, parent, w in ((3.6, lad, 0.75), (3.4, lad2, 0.6)):
        for s in (-1, 1):
            box("rail", (L, 0.09, 0.12), (L / 2, s * w / 2, 0), silver, parent, bevel=0.03)
        n = int(L / 0.4)
        for i in range(n):
            cyl("rung", 0.035, w, (0.2 + i * 0.4, 0, 0), silver, parent, rot=(math.radians(90), 0, 0), verts=8)
    v.parts.update(ladder_pivot=piv, ladder=lad, ladder_ext=lad2)
    # water cannon
    noz = empty("nozzle_piv", (0.25, 0.75, 2.0), v.body)
    cyl("noz_base", 0.18, 0.25, (0, 0, 0), silver, noz, verts=16)
    cyl("noz", 0.09, 0.8, (0.35, 0, 0.2), silver, noz, rot=(0, math.radians(70), 0), verts=12)
    v.parts["nozzle"] = noz
    return v


def make_towtruck():
    v = Vehicle("tow")
    v.root = empty("tow")
    v.body = empty("tow_body", parent=v.root)
    org = mat("tow_orange", (1.0, 0.45, 0.03), rough=0.3)
    gray = mat("tow_gray", (0.35, 0.37, 0.42), rough=0.4)
    glass = mat("glass", C["glass"], rough=0.05, spec=0.8)
    dark = mat("hookdark", (0.15, 0.15, 0.17), rough=0.3, spec=0.8)
    box("t_base", (4.0, 1.9, 0.8), (0, 0, 0.9), org, v.body, bevel=0.25)
    box("t_cab", (1.5, 1.85, 1.25), (0.95, 0, 1.8), org, v.body, bevel=0.32)
    box("t_wind", (0.12, 1.55, 0.6), (1.68, 0, 1.98), glass, v.body, bevel=0.05, rot=(0, math.radians(-12), 0))
    box("t_bed", (2.2, 1.8, 0.25), (-0.9, 0, 1.4), gray, v.body, bevel=0.06)
    v.eyes = eyes(v.body, (1.8, 0, 2.0), spacing=0.68, size=0.31)
    mouth(v.body, (1.68, 0, 0.8), R=0.28, r=0.045)
    _headlights(v, 1.64, 0.66, 1.0)
    _lightbar(v, 0.85, 2.48, w=1.3, colors=("orange", "yellow"))
    _wheels(v, (1.1, -1.15), 0.9)
    piv = empty("crane_pivot", (-0.6, 0, 1.6), v.body, rot=(0, math.radians(35), 0))
    box("boom", (2.6, 0.32, 0.32), (-1.3, 0, 0), gray, piv, bevel=0.08)
    tip = empty("crane_tip", (-2.55, 0, 0), piv)
    hk = empty("hook_root", (0, 0, 0), tip)  # counter-rotated to hang down
    cable = cyl("cable", 0.04, 1.0, (0, 0, -0.5), dark, hk, verts=8)
    hook = empty("hook", (0, 0, -1.0), hk)
    torus("hookT", 0.18, 0.05, (0, 0, -0.15), dark, hook, rot=(0, 0, 0), half="low")
    cyl("hookS", 0.05, 0.2, (0, 0, 0), dark, hook, verts=8)
    v.parts.update(crane=piv, tip=tip, hook_root=hk, cable=cable, hook=hook)
    hk.rotation_euler = (0, math.radians(-35), 0)
    return v


def make_helicopter():
    v = Vehicle("heli")
    v.root = empty("heli")
    v.body = empty("heli_body", parent=v.root)
    yel = mat("heli_yel", (1.0, 0.72, 0.02), rough=0.25)
    glass = mat("glass", C["glass"], rough=0.05, spec=0.8)
    dark = mat("heli_dark", (0.2, 0.2, 0.25), rough=0.3)
    red = mat("heli_red", C["red"], rough=0.3)
    sphere("h_body", 1.0, (0, 0, 1.55), yel, v.body, scale=(1.6, 1.05, 1.0))
    sphere("h_glass", 0.85, (0.85, 0, 1.75), glass, v.body, scale=(0.75, 0.95, 0.75))
    cyl("h_tail", 0.28, 3.2, (-2.6, 0, 1.75), yel, v.body, rot=(0, math.radians(90), 0), r2=0.14)
    box("h_fin", (0.6, 0.1, 0.9), (-4.1, 0, 2.1), red, v.body, bevel=0.08)
    trot = empty("tail_rotor", (-4.1, 0.15, 2.1), v.body)
    for a in (0, 90):
        box("tr_blade", (0.08, 0.04, 1.0), (0, 0, 0), dark, trot, bevel=0.02, rot=(0, math.radians(a), 0))
    v.eyes = eyes(v.body, (1.25, 0, 1.85), spacing=0.62, size=0.3)
    mouth(v.body, (1.55, 0, 1.3), R=0.25, r=0.045, rot=(0, math.radians(25), 0))
    cyl("h_mast", 0.12, 0.5, (0, 0, 2.7), dark, v.body, verts=12)
    rot = empty("rotor", (0, 0, 2.95), v.body)
    cyl("hub", 0.22, 0.14, (0, 0, 0), red, rot, verts=16)
    for a in (0, 90):
        box("blade", (6.2, 0.32, 0.05), (0, 0, 0), dark, rot, bevel=0.03, rot=(0, 0, math.radians(a)))
    for s in (-1, 1):
        cyl("skid", 0.07, 3.0, (0, s * 0.85, 0.12), dark, v.body, rot=(0, math.radians(90), 0), verts=10)
        for x in (-0.6, 0.6):
            cyl("strut", 0.05, 0.8, (x, s * 0.7, 0.5), dark, v.body, rot=(s * math.radians(-15), 0, 0), verts=8)
    sphere("h_light", 0.12, (0, 0, 0.6), mat("heli_red_light", C["red"], emit=0, unique=True), v.body)
    v.lights.append(bpy.data.materials["heli_red_light"])
    v.parts.update(rotor=rot, tail_rotor=trot)
    return v


def make_bubblecar(color=(0.6, 0.25, 0.9)):
    v = Vehicle("bubble")
    v.root = empty("bubble")
    v.body = empty("bubble_body", parent=v.root)
    c = mat("bubble_col", color, rough=0.3)
    glass = mat("glass", C["glass"], rough=0.05, spec=0.8)
    box("b_low", (2.4, 1.6, 0.7), (0, 0, 0.7), c, v.body, bevel=0.3)
    sphere("b_top", 0.85, (-0.15, 0, 1.15), c, v.body, scale=(1.1, 0.9, 0.75))
    box("b_wind", (0.1, 1.1, 0.45), (0.65, 0, 1.3), glass, v.body, bevel=0.04, rot=(0, math.radians(-30), 0))
    v.eyes = eyes(v.body, (0.78, 0, 1.33), spacing=0.55, size=0.26)
    v.parts["happy"] = mouth(v.body, (1.22, 0, 0.66), R=0.24, r=0.04, happy=True, name="b_happy")
    v.parts["sad"] = mouth(v.body, (1.22, 0, 0.56), R=0.2, r=0.04, happy=False, name="b_sad")
    v.parts["happy"].scale = (0.001,) * 3
    _headlights(v, 1.18, 0.5, 0.82, r=0.12)
    _wheels(v, (0.75, -0.75), 0.75, r=0.36, w=0.3)
    return v


def roll_wheels(v, f0, f1):
    """Bake wheel rotation + small body bounce from root motion."""
    frames = list(range(f0, f1 + 1))
    dist = 0.0
    prev, prot = world_pos(v.root, f0)
    rots, bounce = [], []
    for f in frames:
        p, r = world_pos(v.root, f)
        d = (p - prev)
        fwd = Vector((math.cos(r.z), math.sin(r.z), 0))
        dist += d.dot(fwd)
        speed = d.length
        prev = p
        rots.append((0.0, dist / v.wheel_r, 0.0))
        base = evalv(v.body, "location", f)
        bounce.append((base.x, base.y, base.z + 0.04 * min(1.0, speed * 4) * abs(math.sin(f * 0.6))))
    for w in v.wheels:
        bake(w, "rotation_euler", frames, rots)
    bake(v.body, "location", frames, bounce)


def drive(v, seq):
    """seq: list of (frame, (x,y), heading_deg). Eased motion."""
    for f, (x, y), h in seq:
        key(v.root, "location", f, (x, y, v.root.location.z))
        key(v.root, "rotation_euler", f, (0, 0, math.radians(h)))


def spin(o, f0, f1, turns_per_sec, axis=2):
    frames = [f0, f1]
    val = 2 * math.pi * turns_per_sec * (f1 - f0) / FPS
    r0 = list(o.rotation_euler)
    r1 = list(r0)
    r1[axis] += val
    bake(o, "rotation_euler", frames, [tuple(r0), tuple(r1)])


def wiggle_happy(v, f0, n=3, h=0.35):
    """Vehicle 'jumps' with joy."""
    for i in range(n):
        f = f0 + i * 14
        keys(v.body, "location", [(f, (0, 0, 0)), (f + 7, (0, 0, h)), (f + 14, (0, 0, 0))])

# ----------------------------------------------------------------------------
# animals (face +X)
# ----------------------------------------------------------------------------

class Animal:
    def __init__(self):
        self.root = None
        self.eyes = []
        self.happy = None
        self.sad = None
        self.tears = []


def make_animal(kind, scale=1.0, name=None):
    a = Animal()
    name = name or kind
    a.root = empty(name)
    b = empty(name + "_b", parent=a.root)
    a.body = b
    if kind == "puppy":
        fur = mat("puppy_fur", (0.75, 0.48, 0.25), rough=0.6)
        fur2 = mat("puppy_ear", (0.45, 0.25, 0.1), rough=0.6)
        light = mat("puppy_light", (1.0, 0.9, 0.75), rough=0.6)
        sphere("pb", 0.55, (0, 0, 0.6), fur, b, scale=(1.2, 0.85, 0.85))
        head = empty("ph", (0.55, 0, 1.25), b)
        sphere("phd", 0.5, (0, 0, 0), fur, head)
        sphere("psn", 0.25, (0.38, 0, -0.12), light, head, scale=(1, 1.1, 0.8))
        sphere("pnose", 0.09, (0.6, 0, -0.04), mat("nose", C["dark"], rough=0.2), head)
        for s in (-1, 1):
            sphere("pear", 0.22, (-0.05, s * 0.45, 0.05), fur2, head, scale=(0.6, 0.6, 1.4), rot=(s * 0.35, 0, 0))
            for x in (0.35, -0.35):
                sphere("pleg", 0.17, (x, s * 0.3, 0.17), fur, b, scale=(1, 1, 1.3))
        tail = sphere("ptail", 0.12, (-0.7, 0, 0.85), fur, b, scale=(1, 1, 2.0), rot=(0, -0.6, 0))
        a.tail = tail
        a.eyes = eyes(head, (0.41, 0, 0.13), spacing=0.4, size=0.2, name=name + "e")
        a.happy = mouth(head, (0.48, 0, -0.27), R=0.1, r=0.025, happy=True, name=name + "hm")
        a.sad = mouth(head, (0.48, 0, -0.33), R=0.09, r=0.025, happy=False, name=name + "sm")
        a.head = head
    elif kind == "kitten":
        fur = mat("kit_fur", (1.0, 0.55, 0.15), rough=0.6)
        light = mat("kit_light", (1.0, 0.9, 0.8), rough=0.6)
        pinkm = mat("kit_pink", C["pink"], rough=0.5)
        sphere("kb", 0.45, (0, 0, 0.5), fur, b, scale=(1.15, 0.85, 0.9))
        head = empty("kh", (0.45, 0, 1.08), b)
        sphere("khd", 0.42, (0, 0, 0), fur, head)
        sphere("ksn", 0.18, (0.33, 0, -0.1), light, head, scale=(0.8, 1.2, 0.8))
        sphere("knose", 0.06, (0.47, 0, -0.03), pinkm, head)
        for s in (-1, 1):
            cone("kear", 0.17, 0.35, (0, s * 0.25, 0.38), fur, head, rot=(s * -0.35, 0, 0))
            for x in (0.3, -0.3):
                sphere("kleg", 0.13, (x, s * 0.25, 0.13), fur, b, scale=(1, 1, 1.3))
        a.tail = cyl("ktail", 0.07, 0.9, (-0.6, 0, 0.9), fur, b, rot=(0, -0.5, 0), verts=10)
        a.eyes = eyes(head, (0.35, 0, 0.09), spacing=0.34, size=0.18, name=name + "e")
        a.happy = mouth(head, (0.4, 0, -0.22), R=0.08, r=0.02, happy=True, name=name + "hm")
        a.sad = mouth(head, (0.4, 0, -0.27), R=0.07, r=0.02, happy=False, name=name + "sm")
        a.head = head
    elif kind == "bunny":
        fur = mat("bun_fur", (0.97, 0.97, 1.0), rough=0.6)
        pinkm = mat("bun_pink", C["pink"], rough=0.5)
        sphere("bb", 0.5, (0, 0, 0.55), fur, b, scale=(1.0, 0.9, 1.05))
        head = empty("bh", (0.3, 0, 1.25), b)
        sphere("bhd", 0.42, (0, 0, 0), fur, head)
        sphere("bnose", 0.07, (0.42, 0, -0.05), pinkm, head)
        for s in (-1, 1):
            e = empty("bear", (-0.05, s * 0.17, 0.35), head, rot=(s * -0.2, -0.15, 0))
            sphere("bearO", 0.15, (0, 0, 0.35), fur, e, scale=(0.6, 1, 2.6))
            sphere("bearI", 0.1, (0.05, 0, 0.35), pinkm, e, scale=(0.5, 0.8, 2.3))
            sphere("bleg", 0.17, (0.25, s * 0.28, 0.14), fur, b, scale=(1.5, 1, 0.8))
        sphere("btail", 0.16, (-0.5, 0, 0.5), fur, b)
        a.eyes = eyes(head, (0.35, 0, 0.08), spacing=0.34, size=0.18, name=name + "e")
        a.happy = mouth(head, (0.37, 0, -0.2), R=0.1, r=0.02, happy=True, name=name + "hm")
        a.sad = mouth(head, (0.37, 0, -0.25), R=0.07, r=0.02, happy=False, name=name + "sm")
        a.head = head
        # the "ouch" bump and bandage on the front-right leg
        a.bump = sphere("bump", 0.09, (0.42, -0.3, 0.25), mat("bump", (1.0, 0.25, 0.25), rough=0.4), b)
        a.bandage = cyl("bandage", 0.2, 0.16, (0.25, -0.28, 0.14), mat("bandage", C["white"], rough=0.5), b,
                        rot=(0, math.radians(90), 0), verts=16)
        a.bandage.scale = (0.001,) * 3
    elif kind == "lamb":
        wool = mat("wool", (0.98, 0.98, 0.95), rough=0.8)
        face = mat("lambface", (0.3, 0.27, 0.27), rough=0.6)
        r = random.Random(7)
        for i in range(14):
            sphere("wool", 0.28, (r.uniform(-0.4, 0.4), r.uniform(-0.25, 0.25), 0.6 + r.uniform(-0.15, 0.2)), wool, b)
        head = empty("lh", (0.55, 0, 1.0), b)
        sphere("lhd", 0.3, (0, 0, 0), face, head, scale=(1.2, 0.95, 1))
        sphere("ltuft", 0.2, (-0.05, 0, 0.25), wool, head)
        for s in (-1, 1):
            sphere("lear", 0.1, (-0.05, s * 0.32, 0.05), face, head, scale=(0.6, 1.6, 0.6))
            for x in (0.3, -0.3):
                cyl("lleg", 0.07, 0.4, (x, s * 0.2, 0.2), face, b, verts=10)
        a.eyes = eyes(head, (0.33, 0, 0.07), spacing=0.3, size=0.15, name=name + "e")
        a.happy = mouth(head, (0.33, 0, -0.14), R=0.07, r=0.018, happy=True, name=name + "hm")
        a.sad = mouth(head, (0.33, 0, -0.18), R=0.06, r=0.018, happy=False, name=name + "sm")
        a.head = head
    a.root.scale = (scale,) * 3
    # tears (blue drops under eyes)
    tm = mat("tear", (0.3, 0.6, 1.0), rough=0.05, emit=0.3)
    for e in a.eyes:
        t = sphere("tear", 0.05, (e.location.x + 0.04, e.location.y, e.location.z - 0.12), tm, a.head, scale=(0.001,) * 3)
        a.tears.append(t)
    return a


def set_mood(a, f, happy):
    if happy:
        swap_mouth(a.happy, a.sad, f)
    else:
        swap_mouth(a.sad, a.happy, f)


def cry(a, f0, f1, period=18):
    """Animate falling tears in a loop."""
    for t in a.tears:
        z0 = t.location.z
        frames, locs, scs = [], [], []
        for f in range(f0, f1 + 1, 2):
            ph = ((f - f0) % period) / period
            frames.append(f)
            locs.append((t.location.x, t.location.y, z0 - ph * 0.35))
            s = 1.0 if ph < 0.85 else 0.001
            scs.append((s, s, s * 1.4))
        frames.append(f1 + 2); locs.append(locs[-1]); scs.append((0.001,) * 3)
        frames.insert(0, f0 - 1); locs.insert(0, locs[0]); scs.insert(0, (0.001,) * 3)
        bake(t, "location", frames, locs)
        bake(t, "scale", frames, scs)


def sad_pose(a, f0, f1):
    keys(a.head, "rotation_euler", [(f0, (0, math.radians(18), 0)), (f1, (0, math.radians(18), 0))])


def happy_pose(a, f):
    keys(a.head, "rotation_euler", [(f, (0, math.radians(18), 0)), (f + 8, (0, math.radians(-8), 0))])


def jump(o, f0, n=3, h=0.8, period=14):
    z0 = o.location.z
    for i in range(n):
        f = f0 + i * period
        _kz(o, f, z0)
        _kz(o, f + period // 2, z0 + h)
    _kz(o, f0 + n * period, z0)


def wag(a, f0, f1):
    if not hasattr(a, "tail"):
        return
    base = tuple(a.tail.rotation_euler)
    frames = list(range(f0, f1 + 1, 3))
    vals = [(base[0] + 0.5 * math.sin(f * 0.9), base[1], base[2]) for f in frames]
    bake(a.tail, "rotation_euler", frames, vals)

# ----------------------------------------------------------------------------
# effects
# ----------------------------------------------------------------------------

def heart(name, loc, size=0.5, parent=None):
    m = mat("heart", (1.0, 0.15, 0.35), rough=0.25, emit=0.4)
    return text(name, "♥", size, loc, m, parent, rot=(math.radians(90), 0, math.radians(90)), font=FONT_SYM, extrude=0.12, bevel=0.04)


def star(name, loc, size=0.6, parent=None, color=(1.0, 0.85, 0.1)):
    m = mat("star" + str(color), color, rough=0.2, emit=1.5)
    return text(name, "★", size, loc, m, parent, rot=(math.radians(90), 0, math.radians(90)), font=FONT_SYM, extrude=0.1, bevel=0.03)


def hearts_burst(center, f0, n=6, seed=3, face_rot=0.0, spread=1.6, rise=2.5):
    r = random.Random(seed)
    for i in range(n):
        h = heart(f"heart{f0}_{i}", center, size=r.uniform(0.4, 0.7))
        h.rotation_euler.z = math.radians(90) + face_rot
        dx = r.uniform(-spread, spread)
        dy = r.uniform(-spread, spread) * 0.3
        fs = f0 + i * 5
        frames = list(range(fs, fs + 61, 3))
        locs, scs = [], []
        for f in frames:
            t = (f - fs) / 60
            locs.append((center[0] + dx * t + 0.2 * math.sin(t * 9 + i), center[1] + dy * t, center[2] + rise * t))
            s = min(1, t * 6) * (1 if t < 0.8 else max(0.001, (1 - t) * 5))
            scs.append((max(s, 0.001),) * 3)
        key(h, "scale", 0, (0.001,) * 3)
        bake(h, "location", frames, locs)
        bake(h, "scale", [0] + frames + [frames[-1] + 1], [(0.001,) * 3] + scs + [(0.001,) * 3])


def stars_burst(center, f0, n=8, seed=5, face_rot=0.0, radius=2.0):
    r = random.Random(seed)
    cols = [(1, 0.85, 0.1), (1, 0.5, 0.8), (0.4, 0.9, 1.0), (0.6, 1, 0.4)]
    for i in range(n):
        s = star(f"star{f0}_{i}", center, size=r.uniform(0.35, 0.6), color=cols[i % 4])
        s.rotation_euler.z = math.radians(90) + face_rot
        a = 2 * math.pi * i / n
        target = Vector(center) + Vector((math.cos(a) * radius * 0.3, math.cos(a) * radius, math.sin(a) * radius * 0.8 + 0.5))
        target = Vector(center) + (target - Vector(center))
        frames = [f0 - 1, f0, f0 + 12, f0 + 30, f0 + 38]
        locs = [center, center, tuple(target), tuple(target + Vector((0, 0, 0.3))), tuple(target + Vector((0, 0, 0.4)))]
        scs = [(0.001,) * 3, (0.2,) * 3, (1.1,) * 3, (1.0,) * 3, (0.001,) * 3]
        bake(s, "location", frames, locs)
        bake(s, "scale", [0] + frames, [(0.001,) * 3] + scs)
        spin(s, f0, f0 + 38, 0.0)


def confetti(center, f0, n=50, seed=9, spread=4.0, height=5.0, dur=72):
    r = random.Random(seed)
    cols = [C["red"], C["yellow"], C["blue"], C["green"], C["pink"], C["orange"], C["purple"], C["teal"]]
    ms = [mat(f"conf{i}", c, rough=0.4, emit=0.3) for i, c in enumerate(cols)]
    for i in range(n):
        p = box(f"conf{f0}_{i}", (0.18, 0.12, 0.02), center, ms[i % len(ms)], bevel=0)
        vx, vy = r.uniform(-1, 1) * spread, r.uniform(-1, 1) * spread
        vz = r.uniform(0.7, 1.0) * height
        frames = list(range(f0, f0 + dur + 1, 3))
        locs, rots = [], []
        for f in frames:
            t = (f - f0) / dur
            up = vz * (4 * t * (1 - t)) if t < 0.5 else vz - (vz + 1.5) * ((t - 0.5) * 2) ** 1.3
            locs.append((center[0] + vx * t, center[1] + vy * t, center[2] + up))
            rots.append((t * r.uniform(5, 15), t * r.uniform(5, 15), t * 6))
        bake(p, "location", frames, locs)
        bake(p, "rotation_euler", frames, rots)
        bake(p, "scale", [0, f0 - 1, f0, f0 + dur, f0 + dur + 1],
             [(0.001,) * 3, (0.001,) * 3, (1, 1, 1), (1, 1, 1), (0.001,) * 3])


def smoke(center, f0, f1, n=6, seed=2, color=(0.6, 0.6, 0.62), rise=2.5, period=36):
    r = random.Random(seed)
    m = mat("smoke" + str(color), color, rough=0.9, alpha=0.75)
    out = []
    for i in range(n):
        s = sphere(f"smoke{f0}_{i}", 0.35, center, m, segs=12, rings=8)
        off = i * period / n
        frames, locs, scs = [], [], []
        dx = r.uniform(-0.3, 0.3)
        for f in range(f0, f1 + 1, 2):
            ph = ((f - f0 + off) % period) / period
            frames.append(f)
            locs.append((center[0] + dx + ph * 0.6, center[1] + r.uniform(-0.02, 0.02), center[2] + ph * rise))
            k = 0.3 + ph * 1.2
            if ph > 0.8:
                k *= (1 - ph) * 5
            scs.append((max(k, 0.001),) * 3)
        bake(s, "location", frames, locs)
        pre_f, pre_v = ([0, f0 - 1], [(0.001,) * 3] * 2) if f0 > 2 else ([], [])
        bake(s, "scale", pre_f + frames + [f1 + 1], pre_v + scs + [(0.001,) * 3])
        out.append(s)
    return out


def flames(center, f0, f_out, n=5, seed=4, size=1.0):
    """Small cartoon fire that shrinks away at f_out."""
    r = random.Random(seed)
    m1 = mat("flameO", (1.0, 0.35, 0.02), rough=0.3, emit=3.0)
    m2 = mat("flameY", (1.0, 0.85, 0.1), rough=0.3, emit=3.5)
    objs = []
    for i in range(n):
        dx, dy = r.uniform(-0.35, 0.35) * size, r.uniform(-0.35, 0.35) * size
        h = r.uniform(0.7, 1.2) * size
        o = cone(f"flame{i}", 0.28 * size, h, (center[0] + dx, center[1] + dy, center[2] + h / 2), m1 if i % 2 else m2)
        frames = list(range(0, f_out + 13, 3))
        sc = []
        for f in frames:
            k = 1 + 0.25 * math.sin(f * 0.8 + i * 2)
            if f < f0:
                k = 0.001
            if f >= f_out:
                k *= max(0.001, 1 - (f - f_out) / 12)
            sc.append((max(k * 0.9, 0.001), max(k * 0.9, 0.001), max(k, 0.001)))
        bake(o, "scale", frames, sc)
        objs.append(o)
    return objs


def water_spray(start, end, f0, f1, n=14, arc=2.5, period=16):
    m = mat("water", (0.35, 0.7, 1.0), rough=0.05, emit=0.4, alpha=0.8)
    s, e = Vector(start), Vector(end)
    for i in range(n):
        d = sphere(f"drop{f0}_{i}", 0.16, start, m, segs=10, rings=6)
        frames, locs, scs = [], [], []
        for f in range(f0, f1 + 1, 2):
            ph = ((f - f0) / period + i / n) % 1.0
            p = s.lerp(e, ph)
            p.z += arc * 4 * ph * (1 - ph)
            frames.append(f)
            locs.append(tuple(p))
            k = 0.6 + ph * 0.9
            scs.append((k,) * 3)
        bake(d, "location", frames, locs)
        bake(d, "scale", [0, f0 - 1] + frames + [f1 + 1], [(0.001,) * 3, (0.001,) * 3] + scs + [(0.001,) * 3])


def alert_bubble(loc, f0, f1, face_rot=0.0, name="alert"):
    """Big red '!' bubble that pops and pulses."""
    root = empty(name, loc)
    root.rotation_euler.z = face_rot
    sphere(name + "_bg", 0.9, (0, 0, 0), mat("alertbg", (1, 1, 1), rough=0.3), root, scale=(0.3, 1, 1))
    text(name + "_t", "!", 1.3, (0.3, 0, 0), mat("alertred", C["red"], emit=1.0), root,
         rot=(math.radians(90), 0, math.radians(90)), font=FONT_SYM, extrude=0.08)
    S = 1.8
    key(root, "scale", 0, (0.001,) * 3)
    pop_in(root, f0, 6, s=S)
    for f in range(f0 + 12, f1 - 8, 16):
        keys(root, "scale", [(f, (S,) * 3), (f + 8, (S * 1.15,) * 3), (f + 16, (S,) * 3)])
    pop_out(root, f1, 6, s=S)
    return root

# ----------------------------------------------------------------------------
# environment
# ----------------------------------------------------------------------------
DOOR_X = [2.5, 6.7, 10.9, 15.1, 19.3]
STATION_Y = 9.0  # front facade y


def ground(size=500):
    g = box("ground", (size, size, 0.2), (40, 0, -0.1), mat("grass", C["grass"], rough=0.9, spec=0.2), bevel=0)
    return g


def road(x0=-60, x1=200):
    asphalt = mat("asphalt", C["road"], rough=0.8, spec=0.2)
    line = mat("roadline", (1, 1, 1), rough=0.5)
    side = mat("sidewalk", (0.82, 0.8, 0.76), rough=0.8, spec=0.2)
    L = x1 - x0
    box("road", (L, 7.0, 0.06), ((x0 + x1) / 2, 0, 0.03), asphalt, bevel=0)
    for s in (-1, 1):
        box("curb", (L, 1.4, 0.16), ((x0 + x1) / 2, s * 4.2, 0.08), side, bevel=0.03)
    x = x0
    i = 0
    while x < x1:
        box(f"dash{i}", (1.6, 0.18, 0.02), (x, 0, 0.07), line, bevel=0)
        x += 4
        i += 1
    # station apron
    box("apron", (22.5, 4.5, 0.05), (10.9, 6.6, 0.03), mat("apron", (0.7, 0.7, 0.72), rough=0.8, spec=0.2), bevel=0)


def house(loc, rot=0.0, wall=(1, 0.85, 0.6), roof=(0.85, 0.2, 0.15), w=4.0, d=4.0, h=3.0, seed=0):
    r = random.Random(seed)
    root = empty("house", loc, rot=(0, 0, rot))
    box("hwall", (w, d, h), (0, 0, h / 2), mat(f"wall{wall}", wall, rough=0.7, spec=0.2), root, bevel=0.12)
    # pyramid roof (4-sided cone)
    rf = cone("hroof", (max(w, d) * 0.78), h * 0.7, (0, 0, h + h * 0.35), mat(f"roof{roof}", roof, rough=0.5), root, verts=4)
    rf.rotation_euler.z = math.radians(45)
    rf.scale = (w / max(w, d), d / max(w, d), 1)
    win = mat("window", (0.6, 0.85, 1.0), rough=0.1, emit=0.15)
    frame = mat("winframe", (1, 1, 1), rough=0.4)
    for sx in (-w * 0.25, w * 0.25):
        box("hwinf", (0.06, 0.95, 0.95), (w / 2 + 0.01, sx, h * 0.6), frame, root, bevel=0.03)
        box("hwin", (0.08, 0.8, 0.8), (w / 2 + 0.02, sx, h * 0.6), win, root, bevel=0.02)
    box("hdoor", (0.08, 0.8, 1.4), (w / 2 + 0.02, 0, 0.7), mat("door", (0.55, 0.3, 0.15), rough=0.6), root, bevel=0.04)
    return root


def tree(loc, s=1.0, seed=0):
    r = random.Random(seed)
    root = empty("tree", loc)
    cyl("trunk", 0.25 * s, 2.0 * s, (0, 0, 1.0 * s), mat("trunk", (0.45, 0.27, 0.12), rough=0.8), root, verts=12)
    g = [(0.2, 0.65, 0.15), (0.3, 0.75, 0.2), (0.15, 0.55, 0.12)]
    for i in range(4):
        sphere("leaf", r.uniform(0.9, 1.25) * s,
               (r.uniform(-0.5, 0.5) * s, r.uniform(-0.5, 0.5) * s, (2.5 + r.uniform(0, 0.9)) * s),
               mat(f"leaf{i % 3}", g[i % 3], rough=0.7, spec=0.2), root, segs=16, rings=10)
    return root


def cloud(loc, s=1.0, seed=0):
    r = random.Random(seed)
    root = empty("cloud", loc)
    m = mat("cloud", (1, 1, 1), rough=0.9, emit=0.35, spec=0.1)
    for i in range(5):
        sphere("cl", r.uniform(1.0, 1.6) * s, (r.uniform(-2, 2) * s, r.uniform(-0.6, 0.6) * s, r.uniform(-0.3, 0.5) * s),
               m, root, segs=16, rings=10, scale=(1, 1, 0.8))
    return root


def flower_patch(loc, n=10, seed=0):
    r = random.Random(seed)
    cols = [C["pink"], C["yellow"], C["white"], (0.6, 0.4, 1.0), C["red"]]
    for i in range(n):
        p = (loc[0] + r.uniform(-1.5, 1.5), loc[1] + r.uniform(-1.5, 1.5), 0.25)
        sphere("flower", 0.15, p, mat(f"flower{i % 5}", cols[i % 5], rough=0.5), segs=10, rings=6)


def hills():
    m = [mat("hill1", (0.25, 0.62, 0.2), rough=0.9, spec=0.1), mat("hill2", (0.35, 0.7, 0.25), rough=0.9, spec=0.1)]
    r = random.Random(11)
    for i in range(14):
        a = i / 14 * 2 * math.pi
        x = 50 + math.cos(a) * 150
        y = math.sin(a) * 150
        sphere("hill", r.uniform(25, 40), (x, y, -10), m[i % 2], scale=(1.5, 1, 0.6), segs=24, rings=12)


def station(alarm=True):
    root = empty("station")
    wall = mat("st_wall", (1.0, 0.93, 0.8), rough=0.6, spec=0.2)
    trim = mat("st_trim", (0.9, 0.12, 0.1), rough=0.4)
    inner = mat("st_inner", (0.35, 0.35, 0.4), rough=0.8, spec=0.1)
    x0, x1 = 0.0, 21.8
    y0, y1 = STATION_Y, STATION_Y + 7.5
    H = 5.6
    cx = (x0 + x1) / 2
    box("st_back", (x1 - x0, 0.4, H), (cx, y1, H / 2), wall, root, bevel=0.1)
    for x in (x0, x1):
        box("st_side", (0.4, y1 - y0, H), (x, (y0 + y1) / 2, H / 2), wall, root, bevel=0.1)
    box("st_roof", (x1 - x0 + 1.2, y1 - y0 + 1.2, 0.5), (cx, (y0 + y1) / 2, H + 0.2), trim, root, bevel=0.15)
    box("st_floor", (x1 - x0, y1 - y0, 0.04), (cx, (y0 + y1) / 2, 0.02), inner, root, bevel=0)
    box("st_inwall", (x1 - x0 - 0.5, 0.1, H - 0.2), (cx, y1 - 0.25, H / 2), inner, root, bevel=0)
    door_h = 3.6
    box("st_header", (x1 - x0, 0.45, H - door_h), (cx, y0, door_h + (H - door_h) / 2), wall, root, bevel=0.1)
    for i in range(6):
        x = 0.4 + i * 4.2
        box("st_pillar", (0.8, 0.5, door_h), (x, y0, door_h / 2), wall, root, bevel=0.1)
    for i in range(5):  # inner dividers
        pass
    box("st_band", (x1 - x0 + 0.2, 0.5, 0.3), (cx, y0 - 0.05, door_h + 0.15), trim, root, bevel=0.05)
    sign = text("st_sign", "KURTARMA EKİBİ", 0.75, (cx, y0 - 0.3, 4.7), mat("signtxt", (0.1, 0.25, 0.8), rough=0.3), root,
                rot=(math.radians(90), 0, 0), extrude=0.06)
    door_cols = [(0.08, 0.3, 0.9), (0.95, 0.95, 0.95), (0.9, 0.1, 0.08), (1.0, 0.45, 0.03), (1.0, 0.75, 0.05)]
    doors = []
    for i, x in enumerate(DOOR_X):
        d = empty(f"door{i}", (x, y0 - 0.05, 0), root)
        m = mat(f"doorc{i}", door_cols[i], rough=0.35)
        box("doorpanel", (3.3, 0.12, door_h - 0.05), (0, 0, door_h / 2), m, d, bevel=0.06)
        for k in range(4):
            box("doorline", (3.32, 0.14, 0.05), (0, 0, 0.6 + k * 0.8), mat("doorline", (1, 1, 1), rough=0.4), d, bevel=0)
        doors.append(d)
    lamp_m = mat("alarm_lamp", C["red"], rough=0.15, emit=0.0, unique=True)
    cyl("lampbase", 0.6, 0.3, (cx, y0 + 0.5, H + 0.6), mat("lampbase", (0.3, 0.3, 0.35), rough=0.4), root)
    sphere("lamp", 0.7, (cx, y0 + 0.5, H + 0.9), lamp_m, root, scale=(1, 1, 0.85))
    return dict(root=root, doors=doors, lamp=lamp_m)


def open_door(st, i, f0, dur=30):
    """Roll-up door: panel squashes up into the header (never pokes above the roof)."""
    d = st["doors"][i]
    keys(d, "location", [(f0, (d.location.x, d.location.y, 0)), (f0 + dur, (d.location.x, d.location.y, 3.35))])
    keys(d, "scale", [(f0, (1, 1, 1)), (f0 + dur, (1, 1, 0.06))])
    sfx(f0, "door", dur=dur / FPS)


def set_door_open(st, i):
    d = st["doors"][i]
    d.location.z = 3.35
    d.scale = (1, 1, 0.06)


def letters_row(msg, size, center_x, y, z, mats, gap=0.06, prefix="L"):
    """Create one text object per letter, laid out with real glyph widths."""
    objs = []
    for i, ch in enumerate(msg):
        if ch == " ":
            objs.append(None)
            continue
        objs.append(text(f"{prefix}{i}", ch, size, (0, y, z), mats[i % len(mats)], extrude=0.2, bevel=0.05, align="LEFT"))
    bpy.context.view_layer.update()
    widths = [size * 0.4 if o is None else o.dimensions.x for o in objs]
    total = sum(widths) + gap * size * (len(objs) - 1)
    x = center_x - total / 2
    for o, w in zip(objs, widths):
        if o is not None:
            o.location.x = x
        x += w + gap * size
    return [o for o in objs if o is not None]


def town(skip_zones=(), seed=1):
    """Houses, trees, flowers, clouds around the main road."""
    r = random.Random(seed)
    walls = [(1, 0.85, 0.6), (0.7, 0.85, 1.0), (1, 0.7, 0.75), (0.8, 1.0, 0.7), (1.0, 0.95, 0.6)]
    roofs = [(0.85, 0.2, 0.15), (0.2, 0.4, 0.85), (0.55, 0.25, 0.7), (0.95, 0.5, 0.1)]

    def free(x, y):
        for (ax, ay, bx, by) in skip_zones:
            if ax <= x <= bx and ay <= y <= by:
                return False
        return True

    i = 0
    for x in range(-40, 190, 9):
        for side, y in ((1, 14), (-1, -24)):
            if side == 1 and -4 < x < 26:
                continue
            yy = y + side * r.uniform(0, 3)
            if free(x, yy):
                house((x + r.uniform(-1, 1), yy, 0), rot=math.radians(-90 if side == 1 else 90),
                      wall=walls[i % 5], roof=roofs[i % 4], seed=i, h=r.uniform(2.6, 3.6))
            i += 1
    for k in range(70):
        x = r.uniform(-40, 190)
        y = r.uniform(7, 32) if k % 2 else -r.uniform(22, 40)
        if (-3 < x < 25 and 6 < y < 20) or not free(x, y):
            continue
        tree((x, y, 0), s=r.uniform(0.8, 1.2), seed=k)
    for k in range(25):
        x = r.uniform(-40, 190)
        y = r.choice([1, -1]) * r.uniform(6, 9)
        if (-3 < x < 25 and y > 0) or not free(x, y):
            continue
        flower_patch((x, y, 0), n=6, seed=k)
    clouds = []
    for k in range(16):
        c = cloud((r.uniform(-40, 200), r.uniform(-60, 80), r.uniform(18, 30)), s=r.uniform(1.2, 2.2), seed=k)
        for ch in c.children:
            ch.visible_shadow = False
        clouds.append(c)
    return clouds


def drift_clouds(clouds, frames):
    for c in clouds:
        keys(c, "location", [(0, tuple(c.location)), (frames, tuple(c.location + Vector((frames / FPS * 0.5, 0, 0))))])
        for fc in c.animation_data.action.fcurves:
            for k in fc.keyframe_points:
                k.interpolation = "LINEAR"


def standard_world(frames, skip_zones=(), alarm=True):
    world()
    sun()
    ground()
    road()
    hills()
    clouds = town(skip_zones)
    drift_clouds(clouds, frames)
    st = station(alarm)
    return st


def park_vehicles(st, which=None):
    """Create the five rescue vehicles parked in their garages (facing -Y)."""
    makers = [make_police, make_ambulance, make_firetruck, make_towtruck, make_helicopter]
    vs = []
    for i, mk in enumerate(makers):
        if which is not None and i not in which:
            vs.append(None)
            continue
        v = mk()
        v.root.location = (DOOR_X[i], STATION_Y + 3.6, 0)
        v.root.rotation_euler = (0, 0, math.radians(-90))
        if v.kind == "heli":
            v.root.scale = (0.8, 0.8, 0.8)
            v.parts["rotor"].scale = (0.5, 0.5, 1)
        vs.append(v)
    return vs


def render(seg):
    s = bpy.context.scene
    out = os.path.join(BUILD, seg, "f_")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    s.render.filepath = out
    s.render.use_overwrite = False
    s.render.use_placeholder = True
    save_events(seg)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BUILD, seg + ".blend"))


# ----------------------------------------------------------------------------
# extra props
# ----------------------------------------------------------------------------

def balloons(center, f0, n=7, seed=12, rise=12, dur=150):
    r = random.Random(seed)
    cols = [C["red"], C["yellow"], C["blue"], C["green"], C["pink"], C["orange"], C["purple"]]
    strm = mat("string", (0.9, 0.9, 0.9), rough=0.5)
    for i in range(n):
        root = empty(f"balloon{f0}_{i}", center)
        sphere("bl", 0.45, (0, 0, 0.55), mat(f"ball{i % 7}", cols[i % 7], rough=0.15, spec=0.8), root, scale=(1, 1, 1.2))
        cone("bknot", 0.08, 0.12, (0, 0, 0.0), mat(f"ball{i % 7}", cols[i % 7]), root, rot=(math.pi, 0, 0), verts=8)
        cyl("bstr", 0.012, 1.2, (0, 0, -0.65), strm, root, verts=6)
        dx, dy = r.uniform(-3, 3), r.uniform(-2, 2)
        fs = f0 + i * 6
        frames = list(range(fs, fs + dur + 1, 4))
        locs = []
        for f in frames:
            t = (f - fs) / dur
            locs.append((center[0] + dx * t + 0.3 * math.sin(f * 0.1 + i), center[1] + dy * t, center[2] + rise * t * t + 0.5 * t))
        bake(root, "location", frames, locs)
        bake(root, "scale", [0, fs - 1, fs, fs + 8], [(0.001,) * 3, (0.001,) * 3, (0.3,) * 3, (1, 1, 1)])


def doghouse(loc, rot=0.0):
    root = empty("doghouse", loc, rot=(0, 0, rot))
    box("dh_wall", (1.8, 1.8, 1.4), (0, 0, 0.7), mat("dh_wall", (0.95, 0.75, 0.3), rough=0.6), root, bevel=0.08)
    rf = cone("dh_roof", 1.55, 1.0, (0, 0, 1.9), mat("dh_roof", (0.2, 0.45, 0.9), rough=0.5), root, verts=4)
    rf.rotation_euler.z = math.radians(45)
    sphere("dh_hole", 0.45, (0.9, 0, 0.55), mat("dh_hole", (0.1, 0.06, 0.04), rough=0.9), root, scale=(0.15, 1, 1.2))
    sphere("bone", 0.12, (1.4, 0.6, 0.1), mat("bone", (1, 1, 0.95), rough=0.5), root, scale=(2.5, 1, 1))
    return root


def repair_shop(loc, rot=0.0):
    root = empty("shop", loc, rot=(0, 0, rot))
    box("sh_wall", (8, 6, 4.5), (0, 0, 2.25), mat("sh_wall", (0.75, 0.9, 1.0), rough=0.6), root, bevel=0.15)
    box("sh_roof", (8.6, 6.6, 0.4), (0, 0, 4.6), mat("sh_roof", (0.15, 0.6, 0.35), rough=0.5), root, bevel=0.12)
    box("sh_door", (0.1, 4.0, 3.0), (4.0, 0, 1.5), mat("sh_door", (0.3, 0.32, 0.38), rough=0.6), root, bevel=0.05)
    text("sh_sign", "TAMİR", 0.9, (4.08, 0, 3.7), mat("sh_sign", (1, 0.45, 0.03), rough=0.3), root,
         rot=(math.radians(90), 0, math.radians(90)), extrude=0.06)
    return root


def wrench(name, loc, size=1.0, parent=None):
    root = empty(name, loc, parent=parent)
    m = mat("wrench", (0.82, 0.84, 0.9), rough=0.15, spec=0.9, emit=0.2)
    box("wr_handle", (0.22 * size, 0.08 * size, 1.4 * size), (0, 0, 0), m, root, bevel=0.04)
    torus("wr_head", 0.25 * size, 0.08 * size, (0, 0, 0.82 * size), m, root, rot=(math.radians(90), 0, math.radians(90)), half="low")
    return root


def mountain(loc, r=16, h=20):
    root = empty("mountain", loc)
    cone("mt", r, h, (0, 0, h / 2), mat("rock", (0.55, 0.5, 0.48), rough=0.9, spec=0.1), root, verts=9)
    cone("snow", r * 0.3, h * 0.3, (0, 0, h * 0.85 + 0.05), mat("snow", (1, 1, 1), rough=0.6), root, verts=9)
    cyl("mtgrass", r * 1.04, h * 0.3, (0, 0, h * 0.15), mat("hill2", (0.35, 0.7, 0.25), rough=0.9, spec=0.1), root, verts=9, r2=r * 0.72)
    return root


def barn(loc, rot=0.0):
    root = empty("barn", loc, rot=(0, 0, rot))
    box("bn_wall", (6, 5, 4), (0, 0, 2), mat("bn_wall", (0.85, 0.15, 0.12), rough=0.6), root, bevel=0.12)
    rf = cyl("bn_roof", 3.0, 5.2, (0, 0, 4.0), mat("bn_roof", (0.4, 0.25, 0.2), rough=0.6), root, rot=(math.radians(90), 0, 0), verts=3)
    rf.rotation_euler = (math.radians(90), 0, math.radians(90))
    rf.rotation_euler.y = math.radians(30)
    box("bn_door", (0.1, 2.4, 2.8), (3.0, 0, 1.4), mat("bn_trim", (1, 1, 1), rough=0.5), root, bevel=0.05)
    for i in range(10):
        x = -6 + i * 1.4
        box("fence", (0.15, 0.15, 1.1), (x, 5.5, 0.55), mat("fence", (1, 0.95, 0.85), rough=0.6), root, bevel=0.03)
    box("fencebar", (13, 0.1, 0.12), (0.3, 5.5, 0.85), mat("fence", (1, 0.95, 0.85)), root, bevel=0.02)
    return root


def big_tree(loc, branch_side=-1):
    """Tree with a sturdy branch for the kitten; returns (root, branch_tip_world)."""
    root = empty("bigtree", loc)
    trunk = mat("trunk", (0.45, 0.27, 0.12), rough=0.8)
    cyl("btrunk", 0.45, 5.0, (0, 0, 2.5), trunk, root, verts=14)
    cyl("bbranch", 0.16, 2.0, (0, branch_side * 0.9, 4.0), trunk, root, rot=(math.radians(-70 * branch_side), 0, 0), verts=10)
    g = [(0.2, 0.65, 0.15), (0.3, 0.75, 0.2), (0.15, 0.55, 0.12)]
    r = random.Random(3)
    for i in range(6):
        sphere("bleaf", r.uniform(1.3, 1.8), (r.uniform(-1, 1), r.uniform(-0.5, 1.5) * -branch_side, 5.6 + r.uniform(0, 1.2)),
               mat(f"leaf{i % 3}", g[i % 3], rough=0.7, spec=0.2), root, segs=16, rings=10)
    return root, Vector(loc) + Vector((0, branch_side * 1.7, 4.4))


def medkit(name, loc):
    root = empty(name, loc)
    box("mk_box", (0.7, 0.9, 0.55), (0, 0, 0.27), mat("mk_white", (1, 1, 1), rough=0.3), root, bevel=0.08)
    lid = empty("mk_lidpiv", (-0.35, 0, 0.55), root)
    box("mk_lid", (0.7, 0.9, 0.12), (0.35, 0, 0.06), mat("mk_white", (1, 1, 1)), lid, bevel=0.05)
    red = mat("amb_red", C["red"], rough=0.3)
    box("mk_c1", (0.06, 0.45, 0.13), (0.36, 0, 0.27), red, root, bevel=0.02)
    box("mk_c2", (0.06, 0.13, 0.45), (0.36, 0, 0.27), red, root, bevel=0.02)
    return root, lid
