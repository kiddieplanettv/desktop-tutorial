"""2.5D cut-out characters: the user's own 2D character art on camera-facing cards.

A Card is  root (ground position, turns to face the camera)
             └ bob (hop height, tilt / bow)
                 └ sq (squash & stretch, mirror, spin)
                     └ image plane (bottom-centre origin)
           + a soft blob shadow on the ground.
All motion is described with high-level calls (walk_to, hop, cheer, fall, ...) and
baked once per frame by finish(), so effects can overlap freely.
"""
import math, os, random
import bpy, bmesh
from mathutils import Vector
from lib import (empty, sphere, cyl, box, cone, torus, text, mat, bake, key, keys, pop_in, pop_out,
                 FONT_SYM, FONT_TEXT, C, FPS, ease, _link)

CHARS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chars")
ALL = []          # every card (for camera facing + baking)
FACERS = []       # every object that must turn toward the active camera


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def _img_mat(name, path):
    m = bpy.data.materials.new("card_" + name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path, check_existing=True)
    tex.interpolation = "Cubic"
    tex.extension = "CLIP"
    sil = nt.nodes.new("ShaderNodeMix")
    sil.data_type = "RGBA"
    sil.inputs["Factor"].default_value = 0.0
    sil.inputs[7].default_value = (0.02, 0.02, 0.05, 1)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.0
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tex.outputs["Color"], sil.inputs[6])
    nt.links.new(sil.outputs[2], em.inputs["Color"])
    nt.links.new(tex.outputs["Alpha"], mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    m.blend_method = "CLIP"
    m.alpha_threshold = 0.4
    m.shadow_method = "NONE"
    return m, sil, tex.image


class Card:
    def __init__(self, name, img, height, loc=(0, 0, 0), crop_bottom=False, shadow=True, parent=None):
        self.name = name
        self.h = height
        m, self.sil, image = _img_mat(name, os.path.join(CHARS, img + ".png"))
        w0, h0 = image.size
        self.w = height * w0 / h0
        self.root = empty(name, loc, parent)
        self.bob = empty(name + "_bob", parent=self.root)
        self.sq = empty(name + "_sq", parent=self.bob)
        bm = bmesh.new()
        uv = bm.loops.layers.uv.new()
        nx, nz = 4, 6
        verts = [[bm.verts.new(((i / nx - 0.5) * self.w, 0, j / nz * height)) for i in range(nx + 1)] for j in range(nz + 1)]
        for j in range(nz):
            for i in range(nx):
                f = bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]))
                for lp in f.loops:
                    lp[uv].uv = (lp.vert.co.x / self.w + 0.5, lp.vert.co.z / height)
        me = bpy.data.meshes.new(name + "_card")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(m)
        self.plane = bpy.data.objects.new(name + "_card", me)
        _link(self.plane, self.sq)
        self.plane.visible_shadow = False
        self.shadow = None
        if shadow:
            sm = mat("blobshadow", (0.0, 0.0, 0.05), rough=1.0, alpha=0.35)
            self.shadow = sphere(name + "_shadow", 1.0, (0, 0, 0.03), sm, self.root, scale=(self.w * 0.42, self.w * 0.3, 0.01), segs=24, rings=6)
            self.shadow.visible_shadow = False
        self.path = [(0, Vector(loc))]
        self.zpath = [(0, loc[2])]
        self.ops = []
        self.mirror_keys = [(0, 1)]
        self.phase = random.random() * 10
        self.visible = [(0, True)]
        self.walk_fs = []
        ALL.append(self)
        FACERS.append(self.root)

    # ---------------------------------------------------------------- movement
    def at(self, f, x, y):
        """Teleport (between shots): hold until f-1, jump at f."""
        p = self._pos(f - 1)
        self.path.append((f - 1, Vector((p.x, p.y, 0))))
        self.path.append((f, Vector((x, y, 0))))
        return self

    def walk_to(self, f0, f1, x, y, bounce=True):
        """Hold the current spot until f0, then move to (x, y) by f1 with a waddle."""
        p = self._pos(f0)
        self.path.append((f0, Vector((p.x, p.y, 0))))
        self.path.append((f1, Vector((x, y, 0))))
        if bounce:
            self.walk_fs.append((f0, f1))
        return self

    def z_to(self, f0, f1, z):
        zz = self._z(f0)
        self.zpath += [(f0, zz), (f1, z)]
        return self

    def face(self, f, sign):
        self.mirror_keys.append((f, sign))
        return self

    def show(self, f, on=True):
        self.visible.append((f, on))
        return self

    # ---------------------------------------------------------------- effects
    def hop(self, f0, n=1, h=None, period=14):
        self.ops.append(("hop", f0, f0 + n * period, dict(h=h or self.h * 0.35, period=period)))
        return self

    def cheer(self, f0, n=3, period=14):
        self.ops.append(("hop", f0, f0 + n * period, dict(h=self.h * 0.4, period=period)))
        self.ops.append(("wiggle", f0, f0 + n * period, dict(a=10, period=period * 2)))
        return self

    def wiggle(self, f0, f1, a=8, period=20):
        self.ops.append(("wiggle", f0, f1, dict(a=a, period=period)))
        return self

    def tilt(self, f0, f1, a, ramp=8):
        self.ops.append(("tilt", f0, f1, dict(a=a, ramp=ramp)))
        return self

    def bow(self, f0, n=2, a=28, period=20):
        self.ops.append(("bow", f0, f0 + n * period, dict(a=a, period=period)))
        return self

    def shake(self, f0, f1, amp=0.03):
        self.ops.append(("shake", f0, f1, dict(amp=amp)))
        return self

    def spin(self, f0, dur=18, turns=1):
        self.ops.append(("spin", f0, f0 + dur, dict(turns=turns)))
        return self

    def fall(self, f0, f1, side=1):
        """Slip: tip over onto the ground at f0, lie until f1, then pop back up."""
        self.ops.append(("fall", f0, f1, dict(side=side)))
        return self

    def pop(self, f, out=False):
        self.ops.append(("popout" if out else "popin", f, f + 10, {}))
        return self

    def squash(self, f0):
        self.ops.append(("squash", f0, f0 + 10, {}))
        return self

    def silhouette(self, f_on, f_off):
        s = self.sil.inputs["Factor"]
        for f, v in ((0, 0.0), (f_on - 1, 0.0), (f_on, 1.0), (f_off, 1.0), (f_off + 4, 0.0)):
            s.default_value = v
            s.keyframe_insert("default_value", frame=f)
        return self

    # ---------------------------------------------------------------- evaluation
    def _interp(self, pts, f):
        pts = sorted(pts, key=lambda p: p[0])
        if f <= pts[0][0]:
            return pts[0][1]
        for (a, va), (b, vb) in zip(pts, pts[1:]):
            if a <= f <= b:
                if b == a:
                    return vb
                t = smooth((f - a) / (b - a))
                return va + (vb - va) * t
        return pts[-1][1]

    def _pos(self, f):
        return self._interp(self.path, f)

    def _z(self, f):
        return self._interp(self.zpath, f)

    def finish(self, N):
        frames = list(range(0, N + 1))
        root_l, bob_l, bob_r, sq_s, sq_r, sh_s = [], [], [], [], [], []
        mk = sorted(self.mirror_keys, key=lambda p: p[0])
        vis = sorted(self.visible, key=lambda p: p[0])
        for f in frames:
            p = self._pos(f)
            z = self._z(f)
            hop = 0.0; tilt = 0.0; bow = 0.0; spin = 0.0; dx = 0.0
            sx = sz = 1.0
            sc = 1.0
            # idle breathing + sway
            sz *= 1 + 0.015 * math.sin(2 * math.pi * f / 46 + self.phase)
            tilt += 1.5 * math.sin(2 * math.pi * f / 68 + self.phase)
            for f0, f1 in self.walk_fs:
                if f0 <= f <= f1:
                    k = min(1, (f - f0) / 6, (f1 - f) / 6)
                    hop += k * self.h * 0.06 * abs(math.sin(math.pi * (f - f0) / 7))
                    tilt += k * 6 * math.sin(math.pi * (f - f0) / 7)
            for kind, f0, f1, d in self.ops:
                if not (f0 - 1 <= f <= f1 + 12):
                    continue
                t = (f - f0)
                if kind == "hop" and f0 <= f <= f1:
                    ph = (t % d["period"]) / d["period"]
                    hop += d["h"] * math.sin(math.pi * ph)
                    if ph < 0.15:
                        sz *= 1 - 0.18 * (1 - ph / 0.15)
                        sx *= 1 + 0.12 * (1 - ph / 0.15)
                elif kind == "wiggle" and f0 <= f <= f1:
                    tilt += d["a"] * math.sin(2 * math.pi * t / d["period"])
                elif kind == "tilt":
                    k = smooth(min((f - f0) / d["ramp"], (f1 + d["ramp"] - f) / d["ramp"], 1.0))
                    tilt += d["a"] * k
                elif kind == "bow" and f0 <= f <= f1:
                    bow += d["a"] * max(0, math.sin(2 * math.pi * t / d["period"]))
                elif kind == "shake" and f0 <= f <= f1:
                    dx += d["amp"] * math.sin(f * 2.7) * self.h
                    tilt += 3 * math.sin(f * 3.1)
                elif kind == "spin" and f0 <= f <= f1:
                    spin += 360 * d["turns"] * smooth(t / (f1 - f0))
                elif kind == "fall":
                    if f0 <= f <= f1:
                        k = smooth(t / 6)
                        tilt += d["side"] * 82 * k
                        hop += self.h * 0.25 * math.sin(math.pi * min(1, t / 6)) * (1 - k)
                    elif f1 < f <= f1 + 10:
                        k = 1 - smooth((f - f1) / 10)
                        tilt += d["side"] * 82 * k
                elif kind == "popin":
                    if f < f0:
                        sc = 0.0
                    elif f <= f1:
                        u = t / 10
                        sc *= min(1.15, smooth(u * 1.6)) if u < 0.6 else 1.15 - 0.15 * smooth((u - 0.6) / 0.4)
                elif kind == "popout":
                    if f >= f0:
                        sc *= max(0.0, 1 - smooth(t / 8))
                elif kind == "squash" and f0 <= f <= f1:
                    u = t / 10
                    sz *= 1 - 0.25 * math.sin(math.pi * u)
                    sx *= 1 + 0.2 * math.sin(math.pi * u)
            mirror = [s for ff, s in mk if ff <= f][-1] if mk else 1
            # flip squash for 4 frames around a mirror change
            for ff, s in mk[1:]:
                if 0 <= f - ff < 5:
                    sx *= abs(math.cos(math.pi * (f - ff) / 5 / 2 + math.pi / 2)) + 0.05
            v = [on for ff, on in vis if ff <= f][-1]
            if not v:
                sc = 0.0
            sc = max(sc, 0.001)
            root_l.append((p.x, p.y, z))
            bob_l.append((dx, 0, hop))
            bob_r.append((math.radians(-bow), math.radians(tilt), 0))
            sq_s.append((sx * sc * mirror, sc, sz * sc))
            sq_r.append((0, 0, math.radians(spin)))
            shs = max(0.001, (1 - min(0.6, hop / (self.h + 1e-6))) * sc * (1 if z < 0.2 else 0.001))
            sh_s.append((self.w * 0.42 * shs, self.w * 0.3 * shs, 0.01))
        bake(self.root, "location", frames, root_l)
        bake(self.bob, "location", frames, bob_l)
        bake(self.bob, "rotation_euler", frames, bob_r)
        bake(self.sq, "scale", frames, sq_s)
        bake(self.sq, "rotation_euler", frames, sq_r)
        if self.shadow:
            bake(self.shadow, "scale", frames, sh_s)


# ---------------------------------------------------------------------------- emotes

def emote(card, kind, f0, f1, dz=0.35, size=0.55):
    """Speech-bubble style emotion above a card: ! ? heart star tear zzz."""
    root = empty(f"emote_{card.name}_{f0}", (0, 0, card.h + dz + size * 0.5), card.root)
    FACERS.append(root)
    if kind == "tear":
        m = mat("teardrop", (0.35, 0.65, 1.0), rough=0.05, emit=0.6)
        d = empty("drop", (card.w * 0.18, 0, -size * 1.1 - dz), root)
        sphere("drop_b", size * 0.16, (0, 0, 0), m, d)
        cone("drop_t", size * 0.155, size * 0.26, (0, 0, size * 0.17), m, d, verts=16)
        keys(d, "location", [(f0, (card.w * 0.18, -0.05, -size * 1.1 - dz)), (f1, (card.w * 0.18, -0.05, -size * 1.6 - dz))])
    else:
        bg = mat("bubble_bg", (1, 1, 1), rough=0.3, emit=0.4)
        sphere("bub", size * 0.62, (0, 0.02, 0), bg, root, scale=(1, 0.25, 1))
        cone("bubtail", size * 0.18, size * 0.35, (-size * 0.25, 0.02, -size * 0.62), bg, root, rot=(0, math.radians(200), 0), verts=10)
        sym, col = {"!": ("!", C["red"]), "?": ("?", (0.2, 0.4, 1.0)), "heart": ("♥", (1.0, 0.2, 0.45)),
                    "star": ("★", (1.0, 0.75, 0.05)), "zzz": ("z", (0.4, 0.4, 0.9)), "note": ("♪", (0.6, 0.2, 0.9))}[kind]
        text("emo", sym, size * 0.95, (0, -0.06, -size * 0.02), mat("emo" + kind, col, rough=0.3, emit=0.8), root,
             rot=(math.radians(90), 0, 0), font=FONT_SYM, extrude=0.03, bevel=0.0)
    key(root, "scale", 0, (0.001,) * 3)
    keys(root, "scale", [(f0 - 1, (0.001,) * 3), (f0 + 5, (1.25,) * 3), (f0 + 9, (1, 1, 1))])
    for f in range(f0 + 12, f1 - 10, 16):
        keys(root, "scale", [(f, (1, 1, 1)), (f + 8, (1.1, 1.1, 1.1)), (f + 16, (1, 1, 1))])
    keys(root, "scale", [(f1, (1, 1, 1)), (f1 + 6, (0.001,) * 3)])
    return root


# ---------------------------------------------------------------------------- camera facing

def face_cameras(scene=None, extra=()):
    """Each facer gets one Locked-Track constraint per camera, active only during that camera's shot."""
    scene = scene or bpy.context.scene
    marks = sorted(scene.timeline_markers, key=lambda m: m.frame)
    shots = []
    for i, m in enumerate(marks):
        end = marks[i + 1].frame if i + 1 < len(marks) else scene.frame_end + 1
        shots.append((m.camera, m.frame, end))
    for o in list(FACERS) + list(extra):
        for cam, a, b in shots:
            c = o.constraints.new("LOCKED_TRACK")
            c.target = cam
            c.track_axis = "TRACK_NEGATIVE_Y"
            c.lock_axis = "LOCK_Z"
            for f, v in ((0, 0.0), (a - 1, 0.0), (a, 1.0), (b - 1, 1.0), (b, 0.0)):
                if f < 0:
                    continue
                c.influence = v
                c.keyframe_insert("influence", frame=f)
            fc = o.animation_data.action.fcurves
            for fcu in fc:
                if fcu.data_path.endswith(".influence"):
                    for k in fcu.keyframe_points:
                        k.interpolation = "CONSTANT"


def finish_all(N):
    for c in ALL:
        c.finish(N)
    face_cameras()


def reset_cards():
    ALL.clear()
    FACERS.clear()


# ---------------------------------------------------------------------------- characters

ROSTER = {
    # name: (image, height in metres, full body?)
    "ada": ("ada", 1.15, True), "emir": ("emir", 1.15, True), "elif": ("elif", 1.15, True),
    "deniz": ("deniz", 1.15, True), "sami": ("sami", 1.45, True), "pamuk": ("pamuk", 0.95, True),
    "cimcime": ("cimcime", 0.95, True),
    "burak": ("burak", 1.2, False), "kemal": ("kemal", 1.2, False), "murat": ("murat", 1.2, False),
}


def char(name, loc=(0, 0, 0), height=None, tag=None, parent=None, shadow=None):
    img, h, full = ROSTER[name]
    return Card(tag or name, img, height or h, loc, shadow=full if shadow is None else shadow, parent=parent)


# ---------------------------------------------------------------------------- props

def ball(name="ball", r=0.22):
    root = empty(name)
    sphere(name + "_b", r, (0, 0, 0), mat("ballred", (0.95, 0.12, 0.1), rough=0.2, spec=0.7), root, segs=28, rings=16)
    torus(name + "_st", r * 1.0, r * 0.12, (0, 0, 0), mat("ballwhite", (1, 1, 1), rough=0.3), root, rot=(math.radians(90), 0, 0))
    torus(name + "_st2", r * 1.0, r * 0.12, (0, 0, 0), mat("ballyel", (1, 0.85, 0.1), rough=0.3), root, rot=(0, 0, 0))
    return root


def ball_path(b, pts, r=0.22):
    """pts: list of (frame, (x,y), arc_height). Bouncing arcs between points; spins while flying."""
    frames, locs, rots = [], [], []
    ang = 0.0
    for (f0, p0, h0), (f1, p1, h1) in zip(pts, pts[1:]):
        for f in range(f0, f1):
            t = (f - f0) / max(1, f1 - f0)
            x = p0[0] + (p1[0] - p0[0]) * t
            y = p0[1] + (p1[1] - p0[1]) * t
            z = r + h1 * 4 * t * (1 - t)
            ang += 0.35 if h1 > 0 or (p1 != p0) else 0
            frames.append(f); locs.append((x, y, z)); rots.append((ang, ang * 0.3, 0))
    f, p, _ = pts[-1]
    frames.append(f); locs.append((p[0], p[1], r)); rots.append((ang, ang * 0.3, 0))
    bake(b, "location", frames, locs)
    bake(b, "rotation_euler", frames, rots)


def bench(loc, rot=0.0):
    root = empty("bench", loc, rot=(0, 0, rot))
    wood = mat("benchwood", (0.75, 0.45, 0.2), rough=0.6)
    iron = mat("benchiron", (0.2, 0.25, 0.3), rough=0.4)
    for k in range(3):
        box("slat", (0.18, 1.8, 0.06), (k * 0.2 - 0.2, 0, 0.5), wood, root, bevel=0.02)
    for k in range(2):
        box("back", (0.06, 1.8, 0.14), (-0.33, 0, 0.72 + k * 0.2), wood, root, bevel=0.02)
    for y in (-0.8, 0.8):
        box("leg", (0.5, 0.08, 0.5), (0, y, 0.25), iron, root, bevel=0.03)
    return root


def playground(loc):
    root = empty("playground", loc)
    red, blue, yel, grn = (mat("pg_red", (0.95, 0.2, 0.2), rough=0.3), mat("pg_blue", (0.15, 0.45, 0.95), rough=0.3),
                           mat("pg_yel", (1.0, 0.8, 0.1), rough=0.3), mat("pg_grn", (0.2, 0.75, 0.3), rough=0.3))
    # slide tower
    for x in (-0.7, 0.7):
        for y in (-0.7, 0.7):
            cyl("post", 0.08, 2.6, (x, y, 1.3), blue, root, verts=12)
    box("deck", (1.6, 1.6, 0.15), (0, 0, 1.6), yel, root, bevel=0.05)
    cone("roof", 1.3, 0.9, (0, 0, 3.05), red, root, verts=4).rotation_euler.z = math.radians(45)
    box("slide", (3.2, 0.8, 0.08), (2.3, 0, 0.85), red, root, bevel=0.03, rot=(0, math.radians(28), 0))
    for s in (-1, 1):
        box("slrail", (3.2, 0.06, 0.18), (2.3, s * 0.42, 0.97), red, root, bevel=0.02, rot=(0, math.radians(28), 0))
        box("ladrail", (0.06, 0.06, 1.8), (-1.1, s * 0.4, 0.8), grn, root, bevel=0.02, rot=(0, math.radians(-15), 0))
    for k in range(5):
        cyl("ladrung", 0.04, 0.8, (-1.02 - k * 0.07, 0, 0.25 + k * 0.32), grn, root, rot=(math.radians(90), 0, 0), verts=8)
    # swings
    sw = empty("swingset", (0, -4.5, 0), root)
    for y in (-1.6, 1.6):
        for x in (-0.8, 0.8):
            cyl("swleg", 0.07, 2.9, (x * 0.5, y, 1.35), yel, sw, rot=(0, math.radians(15 if x > 0 else -15), 0), verts=10)
    cyl("swbar", 0.08, 3.4, (0, 0, 2.75), blue, sw, rot=(math.radians(90), 0, 0), verts=12)
    seats = []
    for k, y in enumerate((-0.75, 0.75)):
        piv = empty("swpiv", (0, y, 2.7), sw)
        for s in (-1, 1):
            cyl("rope", 0.02, 1.9, (0, s * 0.25, -0.95), mat("chain", (0.7, 0.7, 0.75), rough=0.3, spec=0.8), piv, verts=6)
        box("seat", (0.35, 0.6, 0.06), (0, 0, -1.9), [red, grn][k], piv, bevel=0.02)
        seats.append(piv)
    # seesaw
    ss = empty("seesaw", (0, 4.5, 0), root)
    cone("ssbase", 0.35, 0.6, (0, 0, 0.3), blue, ss, verts=3)
    plank = empty("ssplank", (0, 0, 0.62), ss)
    box("ssboard", (3.2, 0.35, 0.08), (0, 0, 0), grn, plank, bevel=0.03)
    for x in (-1.4, 1.4):
        box("sshandle", (0.06, 0.35, 0.3), (x, 0, 0.18), red, plank, bevel=0.02)
    return dict(root=root, swings=seats, seesaw=plank)


def swing_anim(piv, f0, f1, amp=22, period=60, phase=0.0):
    frames = list(range(f0, f1 + 1, 2))
    bake(piv, "rotation_euler", frames, [(0, math.radians(amp * math.sin(2 * math.pi * (f - f0) / period + phase)), 0) for f in frames])


def seesaw_anim(plank, f0, f1, amp=12, period=70):
    frames = list(range(f0, f1 + 1, 2))
    bake(plank, "rotation_euler", frames, [(0, math.radians(amp * math.sin(2 * math.pi * (f - f0) / period)), 0) for f in frames])


def park(x0, x1, y0, y1):
    """Green park block north of the road with path, fence, flowers, benches."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    from lib import noise_mat, tree, lamp_post, flower_patch
    box("parklawn", (x1 - x0, y1 - y0, 0.06), (cx, cy, 0.03), noise_mat("lawn", (0.35, 0.78, 0.22), (0.5, 0.88, 0.3), 1.2, rough=0.8), bevel=0)
    box("parkpath", (x1 - x0 - 2, 2.2, 0.04), (cx, y0 + 3.2, 0.07), noise_mat("path", (0.95, 0.85, 0.65), (1.0, 0.92, 0.75), 3.0, rough=0.7), bevel=0)
    fence_m = mat("fencew", (1, 1, 1), rough=0.5)
    x = x0
    while x <= x1:
        box("fpost", (0.12, 0.12, 0.8), (x, y0 + 0.3, 0.4), fence_m, bevel=0.03)
        x += 1.2
    box("frail", (x1 - x0, 0.08, 0.08), (cx, y0 + 0.3, 0.6), fence_m, bevel=0.02)
    for k in range(10):
        flower(((x0 + 2 + k * (x1 - x0 - 4) / 9), y0 + 1.0, 0), seed=300 + k)
    return (cx, cy)


def bins(loc, rot=0.0):
    """Three recycling bins: blue paper, yellow plastic, green glass."""
    root = empty("bins", loc, rot=(0, 0, rot))
    out = []
    for k, (col, sym) in enumerate([((0.15, 0.45, 0.95), "▤"), ((1.0, 0.8, 0.1), "◉"), ((0.2, 0.7, 0.3), "▲")]):
        b = empty(f"bin{k}", (0, (k - 1) * 1.0, 0), root)
        m = mat(f"bin{k}", col, rough=0.35)
        box("binbody", (0.75, 0.8, 1.05), (0, 0, 0.53), m, b, bevel=0.08)
        lid = empty("lidpiv", (-0.38, 0, 1.08), b)
        box("lid", (0.8, 0.85, 0.1), (0.4, 0, 0.03), m, lid, bevel=0.04)
        text("binsym", "♻", 0.45, (0.38, 0, 0.6), mat("binsym", (1, 1, 1), emit=0.4), b,
             rot=(math.radians(90), 0, math.radians(90)), font=FONT_SYM, extrude=0.02, bevel=0)
        out.append(dict(root=b, lid=lid, top=None))
    return root, out


def litter(kind, loc):
    if kind == "bottle":
        o = empty("bottle", loc)
        cyl("bt", 0.08, 0.3, (0, 0, 0.15), mat("bottle", (0.3, 0.75, 1.0), rough=0.05, spec=0.9, alpha=0.7), o, verts=12)
        cyl("bcap", 0.04, 0.06, (0, 0, 0.33), mat("bcap", (1, 0.3, 0.3)), o, verts=8)
        o.rotation_euler = (math.radians(90), 0, random.random() * 6)
        return o
    if kind == "paper":
        o = empty("paper", loc)
        sphere("pp", 0.12, (0, 0, 0.1), mat("paper", (0.97, 0.97, 0.92), rough=0.9), o, segs=7, rings=5)
        return o
    o = empty("jar", loc)
    cyl("jr", 0.09, 0.22, (0, 0, 0.11), mat("glassjar", (0.4, 0.8, 0.4), rough=0.05, spec=0.9, alpha=0.75), o, verts=12)
    return o


def throw(o, f0, f1, dest, h=1.6):
    a = Vector(o.location)
    b = Vector(dest)
    frames = list(range(f0, f1 + 1, 1))
    locs = []
    for f in frames:
        t = (f - f0) / (f1 - f0)
        p = a.lerp(b, t)
        p.z += h * 4 * t * (1 - t)
        locs.append(tuple(p))
    bake(o, "location", frames, locs)
    keys(o, "scale", [(f1 - 1, (1, 1, 1)), (f1 + 3, (0.001,) * 3)])


def puddle(loc, r=0.9):
    return sphere("puddle", r, loc, mat("puddle", (0.35, 0.65, 1.0), rough=0.02, spec=1.0, alpha=0.8), scale=(1.4, 1, 0.02), segs=24, rings=6)


def banana(loc):
    o = empty("banana", loc)
    torus("ban", 0.15, 0.05, (0, 0, 0), mat("banana", (1.0, 0.85, 0.1), rough=0.4), o, half="low")
    return o


def flower(loc, seed=0, n=5):
    """Small flower bush: stems + coloured petals (not ball-like)."""
    r = random.Random(seed)
    cols = [C["pink"], C["yellow"], (0.6, 0.4, 1.0), C["red"], (1, 1, 1)]
    root = empty("flowerbush", loc)
    sphere("bush", 0.45, (0, 0, 0.2), mat("bushg", (0.25, 0.65, 0.2), rough=0.7), root, scale=(1.4, 1, 0.6), segs=14, rings=8)
    for k in range(n):
        x, y = r.uniform(-0.5, 0.5), r.uniform(-0.25, 0.25)
        c = mat(f"petal{k % 5}", cols[(k + seed) % 5], rough=0.5)
        for a in range(5):
            ang = a / 5 * 2 * math.pi
            sphere("petal", 0.07, (x + math.cos(ang) * 0.07, y + math.sin(ang) * 0.07, 0.5), c, root, scale=(1, 1, 0.4), segs=8, rings=5)
        sphere("pcenter", 0.045, (x, y, 0.52), mat("pcenter", (1, 0.8, 0.1), rough=0.5), root, segs=8, rings=5)
    return root


# ---------------------------------------------------------------------------- multi-pose characters (character sheets)
CHARS2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chars2")
# which sheet cell is which view, per character (screen direction the character faces)
VIEWS = {
    "default": dict(front="v0", q_r="v1", side_l="v2", back_l="v3", back="v4", back_r="v5", side_r="v6", q_l="v7"),
    "sami": dict(front="v0", q_r="v1", side_r="v2", back_l="v3", back="v4", back_r="v5", side_l="v6", q_l="v7"),
    "burak": dict(front="v0", q_r="v1", side_r="v2", back_l="v3", back="v4", back_r="v5", side_l="v6", q_l="v7"),
}
HEIGHTS2 = {"ada": 1.15, "emir": 1.15, "elif": 1.15, "deniz": 1.15, "sami": 1.4, "burak": 1.75, "kemal": 1.75,
            "murat": 1.75, "pamuk": 0.95, "inek": 1.3, "cimcime": 1.0}


class Sprite(Card):
    """A card that can switch between the views/expressions of a character sheet."""

    def __init__(self, who, loc=(0, 0, 0), height=None, tag=None, parent=None, shadow=True):
        self.who = who
        h = height or HEIGHTS2[who]
        folder = os.path.join(CHARS2, who)
        names = sorted(os.path.splitext(n)[0] for n in os.listdir(folder) if n.endswith(".png"))
        global CHARS
        old = CHARS
        CHARS = folder
        try:
            super().__init__(tag or who, "v0", h, loc, shadow=shadow, parent=parent)
        finally:
            CHARS = old
        ref_px = next(n.image for n in self.plane.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE").size[1]
        self.planes = {"v0": self.plane}
        for n in names:
            if n == "v0":
                continue
            m, sil, image = _img_mat(f"{self.name}_{n}", os.path.join(folder, n + ".png"))
            w0, h0 = image.size
            ph = h * h0 / ref_px
            pw = ph * w0 / h0
            bm = bmesh.new()
            uv = bm.loops.layers.uv.new()
            vs = [bm.verts.new(c) for c in ((-pw / 2, 0, 0), (pw / 2, 0, 0), (pw / 2, 0, ph), (-pw / 2, 0, ph))]
            f = bm.faces.new(vs)
            for lp, (u, v) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
                lp[uv].uv = (u, v)
            me = bpy.data.meshes.new(f"{self.name}_{n}")
            bm.to_mesh(me)
            bm.free()
            me.materials.append(m)
            ob = bpy.data.objects.new(f"{self.name}_{n}", me)
            _link(ob, self.sq)
            ob.visible_shadow = False
            self.planes[n] = ob
        self.map = dict(VIEWS.get(who, VIEWS["default"]))
        for e in ("happy", "angry", "surprised", "sad"):
            self.map[e] = e
        self.pose_keys = [(0, "front")]

    def pose(self, f, name):
        """Show a view ('front', 'side_r', 'q_l', 'back' ...) or expression ('happy', 'sad' ...) from frame f."""
        self.pose_keys.append((f, name))
        return self

    def turn(self, f, *names, step=3):
        for i, n in enumerate(names):
            self.pose(f + i * step, n)
        return self

    def finish(self, N):
        super().finish(N)
        keys_ = sorted(self.pose_keys, key=lambda p: p[0])
        for img, ob in self.planes.items():
            ob.hide_render = True
            ob.keyframe_insert("hide_render", frame=0)
        for f, name in keys_:
            img = self.map.get(name, name)
            for k, ob in self.planes.items():
                ob.hide_render = (k != img)
                ob.keyframe_insert("hide_render", frame=f)


def sprite(who, loc=(0, 0, 0), **kw):
    return Sprite(who, loc, **kw)
