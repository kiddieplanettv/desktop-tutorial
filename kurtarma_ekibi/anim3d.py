"""Real 3D characters (rigged meshes from chars3d/) and natural body animation.

All angles are degrees. Characters face -Y in rest pose; 'forward' = -Y.
Actions are layered: each is a function f -> {bone: (axis, degrees)} summed per frame, then baked.
"""
import bpy, math, os
from mathutils import Vector, Quaternion, Euler
from lib import bake, key, keys, ease

HERE = os.path.dirname(os.path.abspath(__file__))
CH3 = os.path.join(HERE, "chars3d")
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def env(f, f0, f1, ramp=8):
    if f < f0 - ramp or f > f1 + ramp:
        return 0.0
    a = 1.0 if f >= f0 else smooth((f - (f0 - ramp)) / ramp)
    b = 1.0 if f <= f1 else smooth(((f1 + ramp) - f) / ramp)
    return min(a, b)


ALL = []


class Char3D:
    def __init__(self, who, loc=(0, 0, 0), heading=0.0, tag=None):
        path = os.path.join(CH3, who + ".blend")
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            dst.collections = list(src.collections[:1])
        col = dst.collections[0]
        if tag:
            col.name = tag
        bpy.context.scene.collection.children.link(col)
        self.rig = next(o for o in col.objects if o.type == "ARMATURE")
        self.body = next(o for o in col.objects if o.type == "MESH")
        self.tag_copy = bool(tag)
        self.root = bpy.data.objects.new((tag or who) + "_mover", None)
        bpy.context.scene.collection.objects.link(self.root)
        self.rig.parent = self.root
        self.root.location = loc
        self.root.rotation_euler.z = math.radians(heading)
        self.H = max(v.co.z for v in self.body.data.vertices)
        self.acts = []
        self.expr_keys = [(0, "neutral", 0)]
        self.path = [(0, Vector(loc), heading)]
        rest = {b.name: b.matrix_local.to_3x3() for b in self.rig.data.bones}
        self.rest = rest
        self.body.visible_shadow = True
        ALL.append(self)

    # ------------------------------------------------------------ root motion
    def move(self, f0, f1, x, y, heading=None):
        """Travel to (x, y) between f0 and f1; heading defaults to the travel direction."""
        p0 = self._at(f0)
        d = Vector((x, y, 0)) - Vector((p0[0].x, p0[0].y, 0))
        h = heading if heading is not None else (math.degrees(math.atan2(-d.x, d.y)) + 180 if d.length > 1e-3 else p0[1])
        # turn first (quickly), then walk
        self.path.append((f0, p0[0], p0[1]))
        self.path.append((min(f1, f0 + 8), p0[0] + d * 0.02, h))
        self.path.append((f1, Vector((x, y, 0)), h))
        return self

    def face(self, f, heading, dur=8):
        p = self._at(f)
        self.path.append((f, p[0], p[1]))
        self.path.append((f + dur, p[0], heading))
        return self

    def _at(self, f):
        pts = sorted(self.path, key=lambda p: p[0])
        if f <= pts[0][0]:
            return pts[0][1], pts[0][2]
        for (a, pa, ha), (b, pb, hb) in zip(pts, pts[1:]):
            if a <= f <= b:
                t = (f - a) / max(1e-6, b - a)
                dh = (hb - ha + 180) % 360 - 180
                return pa.lerp(pb, t), ha + dh * smooth(t)
        return pts[-1][1], pts[-1][2]

    def expr(self, f, name, ramp=4):
        """Switch facial expression at frame f: 'neutral', 'happy', 'sad', 'surprised', 'angry'."""
        self.expr_keys.append((f, name, ramp))
        return self

    def add(self, fn):
        self.acts.append(fn)
        return self

    # ------------------------------------------------------------ bake
    def bake(self, N):
        frames = list(range(0, N + 1))
        loc, rot = [], []
        bones = {b.name: [] for b in self.rig.data.bones}
        hip_off = []
        for f in frames:
            p, h = self._at(f)
            ang = {}
            lift = 0.0
            for fn in self.acts:
                r = fn(f)
                lift += r.pop("_lift", 0.0)
                for bn, (axis, deg) in r.items():
                    ang.setdefault(bn, []).append((axis, deg))
            loc.append((p.x, p.y, p.z + lift))
            rot.append((0, 0, math.radians(h)))
            for bn in bones:
                q = Quaternion()
                for axis, deg in ang.get(bn, []):
                    la = (self.rest[bn].inverted() @ axis).normalized()
                    q = q @ Quaternion(la, math.radians(deg))
                bones[bn].append(tuple(q))
        # expressions (material mix factors)
        mat = self.body.data.materials[0]
        if self.tag_copy:
            mat = mat.copy()
            self.body.data = self.body.data.copy()
            self.body.data.materials[0] = mat
        nodes = {n.name[5:]: n for n in mat.node_tree.nodes if n.name.startswith("EXPR_")}
        ks = sorted(self.expr_keys, key=lambda k: k[0])
        for ex, node in nodes.items():
            inp = node.inputs["Factor"]
            prev = 0.0
            for f, name, ramp in ks:
                v = 1.0 if name == ex else 0.0
                inp.default_value = prev
                inp.keyframe_insert("default_value", frame=max(0, f - 1))
                inp.default_value = v
                inp.keyframe_insert("default_value", frame=f + ramp)
                prev = v
        bake(self.root, "location", frames, loc)
        bake(self.root, "rotation_euler", frames, rot)
        ob = self.rig
        if ob.animation_data is None:
            ob.animation_data_create()
        act = bpy.data.actions.new(ob.name + "_act")
        ob.animation_data.action = act
        for bn, vals in bones.items():
            ob.pose.bones[bn].rotation_mode = "QUATERNION"
            path = f'pose.bones["{bn}"].rotation_quaternion'
            for i in range(4):
                fc = act.fcurves.new(path, index=i, action_group=bn)
                fc.keyframe_points.add(len(frames))
                fc.keyframe_points.foreach_set("co", [c for f, q in zip(frames, vals) for c in (f, q[i])])
                for k in fc.keyframe_points:
                    k.interpolation = "LINEAR"


def bake_all(N):
    for c in ALL:
        c.bake(N)


# ---------------------------------------------------------------- actions (rest pose faces -Y)

def idle(phase=0.0, amp=1.0):
    def fn(f):
        s = math.sin(2 * math.pi * f / 70 + phase)
        return {"spine": (X, 1.5 * s * amp), "head": (Z, 4 * math.sin(2 * math.pi * f / 110 + phase) * amp),
                "upper_arm.L": (Y, -2 * s * amp), "upper_arm.R": (Y, 2 * s * amp)}
    return fn


def walk(f0, f1, period=18, amp=26, arm=22, bounce=0.035):
    """Natural walk cycle: legs step, knees bend, arms swing opposite, body bobs."""
    def fn(f):
        e = env(f, f0, f1, ramp=6)
        if e <= 0:
            return {}
        ph = 2 * math.pi * (f - f0) / period
        s, c = math.sin(ph), math.cos(ph)
        r = {"thigh.L": (X, amp * s * e), "thigh.R": (X, -amp * s * e),
             "shin.L": (X, max(0.0, -c) * amp * 1.2 * e), "shin.R": (X, max(0.0, c) * amp * 1.2 * e),
             "upper_arm.L": (X, -arm * s * e), "upper_arm.R": (X, arm * s * e),
             "forearm.L": (X, -12 * e), "forearm.R": (X, -12 * e),
             "hips": (Z, 5 * s * e), "spine": (Z, -4 * s * e),
             "head": (X, 2 * c * e)}
        r["_lift"] = bounce * abs(math.sin(ph)) * e
        return r
    return fn


def run(f0, f1, period=12):
    return walk(f0, f1, period=period, amp=38, arm=40, bounce=0.07)


def wave(f0, f1, side="R"):
    sg = 1 if side == "R" else -1

    def fn(f):
        e = env(f, f0, f1)
        if e <= 0:
            return {}
        s = math.sin(2 * math.pi * (f - f0) / 14)
        return {f"upper_arm.{side}": (Y, sg * 140 * e), f"forearm.{side}": (Y, sg * (25 * s) * e),
                "head": (Y, -sg * 6 * e)}
    return fn


def cheer(f0, f1, jumps=2, h=0.25):
    def fn(f):
        e = env(f, f0, f1, ramp=5)
        if e <= 0:
            return {}
        t = (f - f0) / max(1, f1 - f0)
        hop = abs(math.sin(math.pi * jumps * min(1, max(0, t))))
        return {"upper_arm.L": (Y, -150 * e), "upper_arm.R": (Y, 150 * e),
                "forearm.L": (Y, -15 * e), "forearm.R": (Y, 15 * e),
                "thigh.L": (X, -25 * hop * e), "thigh.R": (X, -25 * hop * e),
                "shin.L": (X, 40 * hop * e), "shin.R": (X, 40 * hop * e), "_lift": h * hop * e}
    return fn


def sad(f0, f1):
    def fn(f):
        e = env(f, f0, f1, ramp=12)
        if e <= 0:
            return {}
        return {"head": (X, 12 * e), "spine": (X, 6 * e),
                "upper_arm.L": (Y, 6 * e), "upper_arm.R": (Y, -6 * e), "forearm.L": (X, -20 * e), "forearm.R": (X, -20 * e)}
    return fn


def surprised(f0, f1):
    def fn(f):
        e = env(f, f0, f1, ramp=4)
        if e <= 0:
            return {}
        return {"head": (X, -10 * e), "spine": (X, -6 * e),
                "upper_arm.L": (Y, -35 * e), "upper_arm.R": (Y, 35 * e), "forearm.L": (X, -110 * e), "forearm.R": (X, -110 * e),
                "_lift": 0.04 * e}
    return fn


def point(f0, f1, side="R", up=10):
    sg = -1 if side == "R" else 1

    def fn(f):
        e = env(f, f0, f1)
        if e <= 0:
            return {}
        return {f"upper_arm.{side}": (X, -(75 + up) * e), "spine": (Z, sg * 8 * e)}
    return fn


def bow(f0, f1, deg=35):
    def fn(f):
        e = env(f, f0, f1, ramp=10)
        if e <= 0:
            return {}
        return {"spine": (X, deg * e), "head": (X, 10 * e)}
    return fn


def kick(f0, side="R"):
    def fn(f):
        e = env(f, f0, f0 + 4, ramp=5)
        if e <= 0:
            return {}
        return {f"thigh.{side}": (X, -45 * e), f"shin.{side}": (X, 10 * e), "spine": (X, -6 * e)}
    return fn


def crossed_arms(f0, f1):
    def fn(f):
        e = env(f, f0, f1, ramp=8)
        if e <= 0:
            return {}
        return {"upper_arm.L": (X, -30 * e), "upper_arm.R": (X, -30 * e),
                "forearm.L": (Z, -95 * e), "forearm.R": (Z, 95 * e), "head": (Y, 5 * e)}
    return fn


def sit(f0, f1):
    def fn(f):
        e = env(f, f0, f1, ramp=1)
        if e <= 0:
            return {}
        return {"thigh.L": (X, -85 * e), "thigh.R": (X, -85 * e), "shin.L": (X, 85 * e), "shin.R": (X, 85 * e),
                "upper_arm.L": (X, -40 * e), "upper_arm.R": (X, -40 * e)}
    return fn


def visible(char, f0, f1=None):
    """Show the character only between f0 and f1 (both inclusive)."""
    for ob in (char.body,):
        ob.hide_render = True
        ob.keyframe_insert("hide_render", frame=0)
        ob.hide_render = False
        ob.keyframe_insert("hide_render", frame=f0)
        if f1 is not None:
            ob.hide_render = True
            ob.keyframe_insert("hide_render", frame=f1 + 1)
