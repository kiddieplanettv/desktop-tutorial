"""Skeletal 'puppet' rigs for the user's 2D character art (Live2D-style mesh deformation in Blender).

The character image becomes a dense grid mesh driven by an armature (torso, head, arms, legs),
so arms wave, legs step and the head nods while the art stays exactly as drawn.
Joint positions are given in normalised image coordinates (u: 0 left → 1 right, v: 0 feet → 1 top).
"""
import math
import bpy, bmesh
from mathutils import Vector, Quaternion
import cards as cd
from lib import bake

# ---------------------------------------------------------------- joint maps (from the user's art)
RIGS = {
    "emir": dict(neck=(0.50, 0.49), top=(0.48, 0.98), hip=(0.50, 0.27),
                 armR=[(0.34, 0.44), (0.25, 0.34), (0.21, 0.27)],          # image-left arm (down)
                 armL=[(0.69, 0.45), (0.82, 0.47), (0.92, 0.53)],          # image-right arm (waving)
                 legR=[(0.41, 0.23), (0.37, 0.13), (0.34, 0.03)],
                 legL=[(0.58, 0.23), (0.60, 0.13), (0.63, 0.03)], limb=0.075),
    "ada": dict(neck=(0.56, 0.50), top=(0.55, 0.98), hip=(0.56, 0.26),
                armR=[(0.43, 0.45), (0.34, 0.37), (0.22, 0.33)],
                armL=[(0.67, 0.48), (0.75, 0.55), (0.81, 0.63)],
                legR=[(0.48, 0.22), (0.47, 0.12), (0.45, 0.03)],
                legL=[(0.61, 0.22), (0.63, 0.12), (0.66, 0.03)], limb=0.065),
    "sami": dict(neck=(0.56, 0.56), top=(0.60, 0.98), hip=(0.52, 0.23),
                 armL=[(0.63, 0.49), (0.71, 0.39), (0.80, 0.36)],
                 legR=[(0.43, 0.21), (0.34, 0.12), (0.25, 0.04)],
                 legL=[(0.58, 0.21), (0.60, 0.11), (0.61, 0.03)], limb=0.07),
    "burak": dict(neck=(0.50, 0.53), top=(0.50, 0.98), hip=(0.50, 0.02), limb=0.08),
}


def _seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-9)))
    return (p - (a + ab * t)).length, t


class Puppet:
    """Replaces a Card's flat plane with a rigged grid mesh."""

    def __init__(self, card, key, nx=44, ny=60):
        self.card = card
        J = RIGS[key]
        w, h = card.w, card.h
        P = lambda uv: Vector(((uv[0] - 0.5) * w, 0.0, uv[1] * h))
        mat = card.plane.data.materials[0]
        old = card.plane
        # dense grid
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new()
        vs = [[bm.verts.new(((i / nx - 0.5) * w, 0, j / ny * h)) for i in range(nx + 1)] for j in range(ny + 1)]
        for j in range(ny):
            for i in range(nx):
                f = bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
                for lp in f.loops:
                    lp[uvl].uv = (lp.vert.co.x / w + 0.5, lp.vert.co.z / h)
        me = bpy.data.meshes.new(card.name + "_pmesh")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mat)
        ob = bpy.data.objects.new(card.name + "_puppet", me)
        bpy.context.scene.collection.objects.link(ob)
        ob.visible_shadow = False
        # armature
        ad = bpy.data.armatures.new(card.name + "_arm")
        arm = bpy.data.objects.new(card.name + "_rig", ad)
        bpy.context.scene.collection.objects.link(arm)
        arm.parent = card.sq
        ob.parent = arm
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode="EDIT")
        eb = ad.edit_bones
        bones = {}

        def mk(name, a, b, parent=None):
            bn = eb.new(name)
            bn.head, bn.tail = a, b
            bn.roll = 0.0
            if parent:
                bn.parent = bones[parent]
            bones[name] = bn
            return bn

        mk("torso", P(J["hip"]), P(J["neck"]))
        mk("head", P(J["neck"]), P(J["top"]), "torso")
        segs = {"torso": (P(J["hip"]), P(J["neck"])), "head": (P(J["neck"]), P(J["top"]))}
        for limb in ("armL", "armR", "legL", "legR"):
            if limb in J:
                a, b, c = (P(x) for x in J[limb])
                mk(limb + "1", a, b, "torso")
                mk(limb + "2", b, c, limb + "1")
                segs[limb + "1"] = (a, b)
                segs[limb + "2"] = (b, c)
        bpy.ops.object.mode_set(mode="OBJECT")
        self.arm = arm
        self.axes = {}
        for b in ad.bones:
            self.axes[b.name] = (b.matrix_local.to_3x3().inverted() @ Vector((0, -1, 0))).normalized()
        # weights: limbs own vertices within their thickness, head owns everything above the neck line
        groups = {n: ob.vertex_groups.new(name=n) for n in segs}
        R = J["limb"] * w
        h_ = h
        neck_z = P(J["neck"]).z
        joints = {}
        for limb in ("armL", "armR", "legL", "legR"):
            if limb in J:
                joints[limb] = [P(x) for x in J[limb]]
        for v in me.vertices:
            p = v.co
            ws = {}
            for limb, (a, b, c) in joints.items():
                # region of the limb: past the shoulder/hip line, within the limb thickness
                d1, t1 = _seg_dist(p, a, b)
                d2, t2 = _seg_dist(p, b, c)
                ab = (b - a).normalized()
                along = (p - a).dot(ab)
                if along < -0.02 * h:
                    continue
                d = min(d1, d2)
                if d > R * 1.25:
                    continue
                k = 1.0 if d < R else 1.0 - (d - R) / (R * 0.25)
                k *= min(1.0, (along + 0.02 * h) / (0.05 * h))     # soft joint at the shoulder/hip
                # elbow/knee blend
                bc = (c - b).normalized()
                past = (p - b).dot(bc)
                u = min(1.0, max(0.0, (past + 0.03 * h) / (0.06 * h)))
                ws[limb + "1"] = k * (1 - u)
                ws[limb + "2"] = k * u
            limb_total = min(1.0, sum(ws.values()))
            body = 1.0 - limb_total
            k = min(1.0, max(0.0, (p.z - (neck_z - 0.03 * h)) / (0.06 * h)))
            ws["head"] = body * k
            ws["torso"] = body * (1 - k)
            s = sum(ws.values()) or 1.0
            armw = sum(wv for n, wv in ws.items() if n.startswith("arm"))
            legw = sum(wv for n, wv in ws.items() if n.startswith("leg"))
            v.co.y = -0.012 * armw / s - 0.004 * legw / s   # limbs draw in front of the body
            for n, wv in ws.items():
                if wv > 1e-4:
                    groups[n].add([v.index], wv / s, "REPLACE")
        mod = ob.modifiers.new("arm", "ARMATURE")
        mod.object = arm
        # move the old card plane out of the way
        old.hide_render = True
        old.hide_viewport = True
        card.puppet = self
        self.poses = []   # functions f -> {bone: degrees}

    def add(self, fn):
        self.poses.append(fn)
        return self

    def bake(self, N, step=1):
        frames = list(range(0, N + 1, step))
        names = list(self.axes)
        vals = {n: [] for n in names}
        for f in frames:
            ang = {n: 0.0 for n in names}
            for fn in self.poses:
                for n, a in fn(f).items():
                    if n in ang:
                        ang[n] += a
            for n in names:
                q = Quaternion(self.axes[n], math.radians(ang[n]))
                vals[n].append(tuple(q))
        ob = self.arm
        if ob.animation_data is None:
            ob.animation_data_create()
        if ob.animation_data.action is None:
            ob.animation_data.action = bpy.data.actions.new(ob.name + "Pose")
        act = ob.animation_data.action
        for n in names:
            pb = ob.pose.bones[n]
            pb.rotation_mode = "QUATERNION"
            path = f'pose.bones["{n}"].rotation_quaternion'
            for i in range(4):
                fc = act.fcurves.find(path, index=i) or act.fcurves.new(path, index=i, action_group=n)
                fc.keyframe_points.clear()
                fc.keyframe_points.add(len(frames))
                fc.keyframe_points.foreach_set("co", [c for f, q in zip(frames, vals[n]) for c in (f, q[i])])
                for k in fc.keyframe_points:
                    k.interpolation = "LINEAR"
                fc.update()


# ---------------------------------------------------------------- motion helpers (degrees, +CCW as seen by camera)

def env(f, f0, f1, ramp=8):
    if f < f0 - ramp or f > f1 + ramp:
        return 0.0
    a = min(1.0, (f - (f0 - ramp)) / ramp) if f < f0 else 1.0
    b = min(1.0, ((f1 + ramp) - f) / ramp) if f > f1 else 1.0
    return cd.smooth(min(a, b))


def idle(phase=0.0):
    def fn(f):
        s = math.sin(2 * math.pi * f / 60 + phase)
        return {"head": 3.5 * math.sin(2 * math.pi * f / 90 + phase), "torso": 1.5 * s,
                "armL1": 4 * s, "armR1": -4 * s, "armL2": 3 * s, "armR2": -3 * s}
    return fn


def wave(f0, f1, side="L", raise_deg=None):
    """Wave the hand. Default raises the arm on the given side and swings the forearm."""
    sgn = 1 if side == "L" else -1
    up = (12 if raise_deg is None else raise_deg) * sgn

    def fn(f):
        e = env(f, f0, f1)
        return {f"arm{side}1": up * e, f"arm{side}2": sgn * 28 * math.sin(2 * math.pi * (f - f0) / 14) * e}
    return fn


def walk(f0, f1, period=16, amp=20):
    def fn(f):
        e = env(f, f0, f1, ramp=6)
        s = math.sin(2 * math.pi * (f - f0) / period)
        c = math.cos(2 * math.pi * (f - f0) / period)
        return {"legL1": amp * s * e, "legR1": -amp * s * e,
                "legL2": -max(0, c) * amp * 0.8 * e, "legR2": -max(0, -c) * amp * 0.8 * e,
                "armL1": -amp * 0.7 * s * e, "armR1": amp * 0.7 * s * e, "torso": 2.5 * c * e,
                "head": -2 * c * e}
    return fn


def cheer(f0, f1, up_L=20, up_R=-50):
    """Arms up (angles depend on the drawn pose), little wiggle; combine with card.hop for jumping."""
    def fn(f):
        e = env(f, f0, f1)
        s = math.sin(2 * math.pi * (f - f0) / 12)
        return {"armL1": (up_L + 6 * s) * e, "armR1": (up_R - 6 * s) * e, "armL2": 10 * e, "armR2": -10 * e,
                "legL1": 5 * s * e, "legR1": -5 * s * e, "head": 4 * s * e}
    return fn


def kick(f0, side="L"):
    def fn(f):
        e = env(f, f0, f0 + 6, ramp=5)
        return {f"leg{side}1": (35 if side == "L" else -35) * e, f"leg{side}2": -10 * e, "torso": (-4 if side == "L" else 4) * e}
    return fn


def nod(f0, f1, amp=10, period=16):
    def fn(f):
        e = env(f, f0, f1)
        return {"head": amp * math.sin(2 * math.pi * (f - f0) / period) * e}
    return fn


def point(f0, f1, side="L", deg=55):
    sgn = 1 if side == "L" else -1

    def fn(f):
        e = env(f, f0, f1)
        return {f"arm{side}1": sgn * deg * e, f"arm{side}2": sgn * 10 * e}
    return fn
