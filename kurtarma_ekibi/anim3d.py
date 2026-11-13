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
        self.gaits = []
        self.expr_keys = [(0, "neutral", 0)]
        self.pos = [(0, Vector(loc), "lin")]
        self.head = [(0, heading)]
        rest = {b.name: b.matrix_local.to_3x3() for b in self.rig.data.bones}
        self.rest = rest
        self.body.visible_shadow = True
        ALL.append(self)

    # ------------------------------------------------------------ root motion
    def move(self, f0, f1, x, y, heading=None, gait="walk", turn=10):
        """Travel to (x, y) between f0 and f1 with natural acceleration/deceleration.
        The legs step automatically in sync with the distance travelled (no foot sliding).
        gait: 'walk', 'run', 'sneak' or None (no stepping, e.g. carried)."""
        p0, h0 = self._at(f0)
        d = Vector((x, y, 0)) - Vector((p0.x, p0.y, 0))
        h = heading if heading is not None else (math.degrees(math.atan2(-d.x, d.y)) + 180 if d.length > 1e-3 else h0)
        self.pos.append((f0, p0.copy(), "lin"))
        self.pos.append((f1, Vector((x, y, p0.z)), "trap"))
        self.head.append((f0, h0))
        self.head.append((f0 + min(turn, max(1, f1 - f0)), h))
        if gait:
            self.gaits.append((f0, f1, gait))
        return self

    def face(self, f, heading, dur=12, step=True):
        """Turn on the spot to a heading; a couple of small steps go with the turn."""
        h0 = self._at(f)[1]
        self.head.append((f, h0))
        self.head.append((f + dur, heading))
        if step and abs((heading - h0 + 180) % 360 - 180) > 20:
            self.gaits.append((f, f + dur, "turn"))
        return self

    @staticmethod
    def _trap(t, r=0.22):
        t = max(0.0, min(1.0, t))
        v = 1.0 / (1.0 - r)
        if t < r:
            return v * t * t / (2 * r)
        if t > 1 - r:
            return 1 - v * (1 - t) ** 2 / (2 * r)
        return v * (t - r / 2)

    def _at(self, f):
        ps = sorted(self.pos, key=lambda p: p[0])
        p = ps[-1][1]
        if f <= ps[0][0]:
            p = ps[0][1]
        else:
            for (a, pa, _), (b, pb, mode) in zip(ps, ps[1:]):
                if a <= f <= b:
                    t = (f - a) / max(1e-6, b - a)
                    p = pa.lerp(pb, self._trap(t) if mode == "trap" else t)
                    break
        hs = sorted(self.head, key=lambda q: q[0])
        h = hs[-1][1]
        if f <= hs[0][0]:
            h = hs[0][1]
        else:
            for (a, ha), (b, hb) in zip(hs, hs[1:]):
                if a <= f <= b:
                    t = (f - a) / max(1e-6, b - a)
                    dh = (hb - ha + 180) % 360 - 180
                    h = ha + dh * smooth(t)
                    break
        return p, h

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
        path = [self._at(f) for f in frames]
        # distance travelled (plus a little for turning on the spot) drives the step phase
        dist = [0.0]
        for k in range(1, len(frames)):
            (pa, ha), (pb, hb) = path[k - 1], path[k]
            dh = abs((hb - ha + 180) % 360 - 180)
            dist.append(dist[-1] + (pb - pa).length + math.radians(dh) * 0.10 * self.H)
        speed = [0.0] + [dist[k] - dist[k - 1] for k in range(1, len(frames))]
        sm = speed[:]
        for k in range(len(frames)):           # smooth the speed a little (gait blends in/out)
            w = speed[max(0, k - 3):k + 4]
            sm[k] = sum(w) / len(w)
        gait_fns = [gait(self, g0, g1, kind, dist, sm) for g0, g1, kind in self.gaits]
        for f in frames:
            p, h = path[f]
            ang = {}
            lift = 0.0
            shift = 0.0
            for fn in gait_fns + self.acts:
                r = fn(f)
                lift += r.pop("_lift", 0.0)
                shift += r.pop("_shift", 0.0)
                for bn, axis, deg in r.pop("_extra", []):
                    ang.setdefault(bn, []).append((axis, deg))
                for bn, (axis, deg) in r.items():
                    ang.setdefault(bn, []).append((axis, deg))
            hr = math.radians(h)
            loc.append((p.x + shift * math.cos(hr), p.y + shift * math.sin(hr), p.z + lift))
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
    """Alive while standing: breathing, slow weight shift from foot to foot, small head movements."""
    def fn(f):
        br = math.sin(2 * math.pi * f / 72 + phase)
        ws = math.sin(2 * math.pi * f / 190 + phase * 1.7)
        hd = math.sin(2 * math.pi * f / 130 + phase * 0.6)
        return {"spine": (X, 1.2 * br * amp), "hips": (Y, 2.0 * ws * amp),
                "head": (Z, 5 * hd * amp),
                "_extra": [("spine", Y, -1.6 * ws * amp), ("head", X, -1.0 * br * amp),
                           ("upper_arm.L", Y, (-3 - 1.5 * br) * amp), ("upper_arm.R", Y, (3 + 1.5 * br) * amp),
                           ("forearm.L", X, -10 * amp), ("forearm.R", X, -10 * amp)],
                "_shift": 0.006 * ws * amp}
    return fn


GAITS = {
    #        cadence(steps/s) maxA  knee_sw knee_st arm  elbow lean  yaw  sway   v_min
    "walk":  dict(cad=2.3, A=30, Kw=55, Ks=10, arm=20, elb=18, lean=3, yaw=6, sway=0.012, vmin=0.25),
    "run":   dict(cad=3.4, A=46, Kw=95, Ks=18, arm=42, elb=75, lean=11, yaw=9, sway=0.008, vmin=0.6),
    "sneak": dict(cad=1.5, A=24, Kw=75, Ks=14, arm=8, elb=55, lean=14, yaw=4, sway=0.018, vmin=0.12),
    "turn":  dict(cad=2.4, A=9, Kw=35, Ks=4, arm=5, elb=12, lean=0, yaw=2, sway=0.006, vmin=0.0),
}


def gait(ch, f0, f1, kind, dist, speed):
    """Procedural gait locked to the distance travelled: feet plant, knees bend in swing, toes push off,
    hips/shoulders counter-rotate, arms swing opposite to the legs with relaxed elbows, body bobs so the
    supporting foot stays on the ground."""
    from lib import FPS
    P = GAITS[kind]
    H = ch.H
    a = b = 0.13 * H                      # thigh / shin length (chibi proportions)
    phase = {}
    ph = 0.0
    for f in range(len(dist)):
        v = speed[f] * FPS
        if kind == "turn":
            dph = math.pi * P["cad"] / FPS if f0 <= f <= f1 else 0.0
        else:
            smax = 0.92 * 4 * (a + b) * math.sin(math.radians(P["A"]))
            stride = max(1e-4, min(2.0 * v / P["cad"], smax))   # faster steps instead of sliding feet
            dph = 2 * math.pi * speed[f] / stride if v > 1e-4 else 0.0
        if f0 - 4 <= f <= f1 + 4:
            ph += dph
        phase[f] = ph

    def leg(q, A, e):
        q = q % (2 * math.pi)
        th = -A * math.cos(q)
        if q < math.pi:                    # stance: small give at mid-stance, foot rolls heel->toe
            kn = P["Ks"] * math.sin(q)
            ft = -8 + 24 * (q / math.pi) ** 2
        else:                              # swing: knee folds early, foot recovers
            u = (q - math.pi) / math.pi
            kn = P["Kw"] * math.sin(math.pi * u ** 0.75) * (A / P["A"])
            ft = 16 - 24 * u
        return th * e, kn * e, ft * e

    def fn(f):
        if f < f0 - 6 or f > f1 + 6:
            return {}
        v = speed[min(f, len(speed) - 1)] * FPS
        w = env(f, f0, f1, ramp=5)
        if kind == "turn":
            e = w
            A = P["A"]
        else:
            e = w * min(1.0, v / P["vmin"]) if P["vmin"] > 0 else w
            stride = 2.0 * v / P["cad"]
            A = min(P["A"], math.degrees(math.asin(min(0.99, stride / (4 * (a + b))))) + 4)
        if e <= 1e-3:
            return {}
        p = phase[f]
        tL, kL, fL = leg(p, A, e)
        tR, kR, fR = leg(p + math.pi, A, e)
        c = math.cos(p)
        r = {"thigh.L": (X, tL), "thigh.R": (X, tR), "shin.L": (X, kL), "shin.R": (X, kR),
             "foot.L": (X, fL), "foot.R": (X, fR),
             "upper_arm.L": (X, P["arm"] * math.cos(p - 0.35) * e * (A / P["A"])),
             "upper_arm.R": (X, -P["arm"] * math.cos(p - 0.35) * e * (A / P["A"])),
             "forearm.L": (X, -(P["elb"] + 8 * max(0.0, -math.cos(p - 0.5))) * e),
             "forearm.R": (X, -(P["elb"] + 8 * max(0.0, math.cos(p - 0.5))) * e),
             "hips": (Z, -P["yaw"] * c * e), "spine": (X, P["lean"] * e),
             "head": (X, -P["lean"] * 0.5 * e + 1.5 * math.cos(2 * p) * e)}
        # counter-rotate the shoulders against the hips
        r["_extra"] = [("spine", Z, P["yaw"] * 1.3 * c * e), ("head", Z, -P["yaw"] * 0.5 * c * e),
                       ("upper_arm.L", Y, -5 * e), ("upper_arm.R", Y, 5 * e)]
        if kind == "sneak":
            r["_extra"] += [("thigh.L", X, -22 * e), ("thigh.R", X, -22 * e), ("shin.L", X, 38 * e),
                            ("shin.R", X, 38 * e), ("upper_arm.L", X, -25 * e), ("upper_arm.R", X, -25 * e)]
        # keep the supporting foot on the ground: hip height from the two-bone leg
        def drop(t, k):
            return a * math.cos(math.radians(t)) + b * math.cos(math.radians(t + k))
        extra_t = -22 * e if kind == "sneak" else 0
        extra_k = 38 * e if kind == "sneak" else 0
        d = max(drop(tL + extra_t, kL + extra_k), drop(tR + extra_t, kR + extra_k))
        lift = d - (a + b)
        if kind == "run":                   # short flight phase between steps
            lift += 0.045 * H * max(0.0, math.sin(2 * p)) * e
        r["_lift"] = lift
        r["_shift"] = P["sway"] * H * math.sin(p) * e
        return r
    return fn


def walk(f0, f1, **kw):
    """Kept for old scripts: an in-place stepping cycle (use Char3D.move(..., gait=...) instead)."""
    return lambda f: {}


def run(f0, f1, **kw):
    return lambda f: {}


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
    """Happy jumps: crouch (anticipation) -> spring up with arms high -> soft landing."""
    def fn(f):
        e = env(f, f0, f1, ramp=6)
        if e <= 0:
            return {}
        T = (f1 - f0) / max(1, jumps)
        t = ((f - f0) % T) / T if f0 <= f <= f1 else 0.0
        if t < 0.25:
            crouch, air = math.sin(math.pi * t / 0.25 * 0.5), 0.0
        elif t < 0.8:
            crouch, air = 0.0, math.sin(math.pi * (t - 0.25) / 0.55)
        else:
            crouch, air = math.sin(math.pi * (t - 0.8) / 0.2), 0.0
        arms = 0.75 + 0.25 * air
        sw = math.sin(2 * math.pi * (f - f0) / 16)
        return {"upper_arm.L": (Y, -150 * arms * e), "upper_arm.R": (Y, 150 * arms * e),
                "forearm.L": (Y, (-15 + 12 * sw) * e), "forearm.R": (Y, (15 - 12 * sw) * e),
                "thigh.L": (X, (-30 * crouch - 12 * air) * e), "thigh.R": (X, (-30 * crouch - 12 * air) * e),
                "shin.L": (X, (55 * crouch + 25 * air) * e), "shin.R": (X, (55 * crouch + 25 * air) * e),
                "spine": (X, (10 * crouch - 4 * air) * e), "head": (X, -6 * air * e),
                "_lift": (h * air - 0.05 * crouch) * e}
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
