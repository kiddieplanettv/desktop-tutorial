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


GROUND = ("curb", "ground", "parklawn", "parkpath", "road", "lawn", "path", "sidewalk", "farm", "field", "yard", "grass")


def ground_z(x, y):
    """Height of the walkable surface (lawn, path, pavement, road) under a point."""
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    z = 1.2
    for _ in range(12):
        hit, loc, _n, _i, ob, _m = sc.ray_cast(dg, Vector((x, y, z)), Vector((0, 0, -1)))
        if not hit:
            return 0.0
        if ob.name.lower().startswith(GROUND):
            return loc.z
        z = loc.z - 0.002
    return 0.0


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

# ---------------------------------------------------------------- motion capture library
import json
_MC = None


def mocap():
    global _MC
    if _MC is None:
        raw = json.load(open(os.path.join(CH3, "mocap.json")))
        _MC = {}
        for name, c in raw.items():
            fr = [dict(dirs={k: Vector(v) for k, v in f["dirs"].items()},
                       rots={k: Quaternion(v) for k, v in f["rots"].items()},
                       lat=f["lat"], fwd=f["fwd"], air=f["air"]) for f in c["frames"]]
            _MC[name] = dict(frames=fr, loop=c.get("loop", False), stride=c.get("stride", 0.0))
    return _MC


def pmix(a, b, w, bones=None):
    """Blend two poses (w = share of b); 'bones' limits the blend to some bones (e.g. the upper body)."""
    if w <= 0:
        return a
    out = dict(dirs=dict(a["dirs"]), rots=dict(a["rots"]), lat=a["lat"], fwd=a["fwd"], air=a["air"])
    for k, v in b["dirs"].items():
        if bones is None or k in bones:
            d = a["dirs"][k].lerp(v, w)
            out["dirs"][k] = d.normalized() if d.length > 1e-6 else v
    for k, q in b["rots"].items():
        if bones is None or k in bones:
            out["rots"][k] = a["rots"][k].slerp(q, w)
    if bones is None:
        for k in ("lat", "fwd", "air"):
            out[k] = a[k] * (1 - w) + b[k] * w
    return out


def psample(name, t, mirror=False):
    """Pose of clip 'name' at (fractional) frame t. Gait loops wrap; other loops play back and forth."""
    c = mocap()[name]
    fr = c["frames"]; n = len(fr)
    if c["stride"]:
        t = t % n
        i = int(t); j = (i + 1) % n
    else:
        if c["loop"]:
            t = t % (2 * (n - 1))
            if t > n - 1:
                t = 2 * (n - 1) - t
        t = max(0.0, min(n - 1.0, t))
        i = int(t); j = min(n - 1, i + 1)
    p = pmix(fr[i], fr[j], t - i)
    if mirror:
        sw = lambda k: k[:-1] + ("R" if k.endswith("L") else "L") if k[-2:] in (".L", ".R") else k
        p = dict(dirs={sw(k): Vector((-v.x, v.y, v.z)) for k, v in p["dirs"].items()},
                 rots={k: Quaternion((q.w, q.x, -q.y, -q.z)) for k, q in p["rots"].items()},
                 lat=-p["lat"], fwd=p["fwd"], air=p["air"])
    return p


UPPER = {"spine", "head", "upper_arm.L", "upper_arm.R", "forearm.L", "forearm.R"}
ARM = {"L": {"upper_arm.L", "forearm.L"}, "R": {"upper_arm.R", "forearm.R"}}


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
        self.plays = []
        self.gph = {}
        self.look_cam = True
        bs = self.rig.data.bones
        self.order = [b.name for b in bs]            # parents come first
        self.parent = {b.name: (b.parent.name if b.parent else None) for b in bs}
        self.bhead = {b.name: b.head_local.copy() for b in bs}
        self.blen = {b.name: b.length for b in bs}
        self.L = bs["thigh.L"].length + bs["shin.L"].length
        self.seed = len(ALL) * 37.0
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

    def go(self, f0, x, y, gait="walk", rate=1.0, heading=None):
        """Travel to (x, y) starting at f0 at the natural speed of the gait (real stride length for this
        character's legs). Returns the arrival frame."""
        from lib import FPS
        p0, _ = self._at(f0)
        d = (Vector((x, y, 0)) - Vector((p0.x, p0.y, 0))).length
        c = mocap()[gait]
        v = c["stride"] * self.L / len(c["frames"]) * rate       # metres per frame at full speed
        f1 = f0 + max(8, int(round(d / v / (1 - 0.22))))
        self.move(f0, f1, x, y, heading=heading, gait=gait)
        return f1

    def play(self, f0, name, f1=None, rate=1.0, bones=None, mirror=False, fade=6, gain=1.0):
        """Play a motion-capture clip from f0 (blended in/out). bones: None = whole body, or a set of bones."""
        n = len(mocap()[name]["frames"])
        f1 = f1 if f1 is not None else f0 + int(n / rate)
        self.plays.append((f0, f1, name, rate, bones, mirror, fade, gain))
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
    def solve(self, pose):
        """Motion-capture pose -> local bone rotations for this rig + how far the lowest foot is below rest."""
        rest = self.rest
        A, Hd, out = {}, {}, {}
        for bn in self.order:
            p = self.parent[bn]
            if p:
                inh = A[p] @ rest[p].inverted() @ rest[bn]
                Hd[bn] = Hd[p] + A[p] @ rest[p].inverted() @ (self.bhead[bn] - self.bhead[p])
            else:
                inh = rest[bn].copy()
                Hd[bn] = self.bhead[bn].copy()
            if bn in pose["rots"]:
                D = pose["rots"][bn].to_matrix() @ rest[bn]
            elif bn in pose["dirs"]:
                d = pose["dirs"][bn].copy()
                sg = 1 if bn.endswith(".L") else -1
                if bn.startswith("upper_arm") and d.z < -0.2:      # chubby body: keep hanging arms off the tummy
                    d.x = sg * max(d.x * sg, 0.30); d.normalize()
                if bn.startswith("forearm") and d.z < -0.2:
                    d.x = sg * max(d.x * sg, 0.12); d.normalize()
                D = inh.col[1].rotation_difference(d).to_matrix() @ inh
            else:
                D = inh
            out[bn] = (inh.inverted() @ D).to_quaternion()
            A[bn] = D
        low = 0.0
        for sd in ("L", "R"):
            fb = "foot." + sd
            ank = Hd[fb].z - self.bhead[fb].z
            toe = (Hd[fb] + A[fb].col[1] * self.blen[fb]).z - (self.bhead[fb] + rest[fb].col[1] * self.blen[fb]).z
            low = min(low, ank, toe) if sd == "R" else min(ank, toe)
        return out, low

    def bake(self, N):
        from lib import FPS
        frames = list(range(0, N + 1))
        loc, rot = [], []
        bones = {b.name: [] for b in self.rig.data.bones}
        path = [self._at(f) for f in frames]
        dist = [0.0]
        for k in range(1, len(frames)):
            (pa, ha), (pb, hb) = path[k - 1], path[k]
            dh = abs((hb - ha + 180) % 360 - 180)
            dist.append(dist[-1] + (pb - pa).length + math.radians(dh) * 0.25 * self.L)
        MC = mocap()
        zs = []
        # cheat to camera: turn the head (and a little of the chest) towards the active camera, so the
        # drawn face is seen from the front / three-quarter and never in a hard profile
        from lib import evalv
        marks = sorted(bpy.context.scene.timeline_markers, key=lambda m: m.frame)
        look = []
        for f in frames:
            cam = None
            for m in marks:
                if m.frame <= f and m.camera:
                    cam = m.camera
            y = 0.0
            if cam is not None and self.look_cam:
                p, h = path[f]
                d = Vector(evalv(cam, "location", f)) - p
                hr = math.radians(h)
                lx = d.x * math.cos(hr) + d.y * math.sin(hr)
                ly = -d.x * math.sin(hr) + d.y * math.cos(hr)
                a = math.degrees(math.atan2(lx, -ly))
                y = max(-48.0, min(48.0, a * 0.65)) * max(0.0, min(1.0, (170 - abs(a)) / 30))
            look.append(y)
        look = [sum(look[max(0, k - 6):k + 7]) / len(look[max(0, k - 6):k + 7]) for k in range(len(look))]
        for f in frames:
            p, h = path[f]
            ds = dist[f] - dist[f - 1] if f else 0.0
            pose = psample("idle", f * 0.15 + self.seed)
            pose = dict(pose, lat=0.0, fwd=0.0)
            for g in self.gaits:
                f0, f1, kind = g[:3]
                clip = "walk" if kind == "turn" else kind
                c = MC[clip]; n = len(c["frames"])
                st = self.gph.setdefault(id(g), 0.0)
                if f0 - 8 <= f <= f1 + 8:
                    st += ds / (c["stride"] * self.L) * n          # feet stay locked to the ground distance
                    self.gph[id(g)] = st
                w = env(f, f0, f1, ramp=6)
                if w <= 0:
                    continue
                vnat = c["stride"] * self.L / n
                w *= min(1.0, ds / (0.3 * vnat)) if kind != "turn" else 0.5
                pose = pmix(pose, psample(clip, st), smooth(w))
            for f0, f1, name, rate, bns, mirror, fade, gain in self.plays:
                w = env(f, f0, f1, ramp=fade)
                if w <= 0:
                    continue
                q = psample(name, max(0.0, (f - f0) * rate), mirror)
                q = dict(q, air=q["air"] * gain, lat=0.0, fwd=0.0)
                if bns is not None and "hips" not in bns:      # upper-body clip rides on the current hips
                    rel = pose["rots"]["hips"] @ q["rots"]["hips"].inverted()
                    q["rots"] = {k: rel @ v for k, v in q["rots"].items()}
                    q["dirs"] = {k: rel @ v for k, v in q["dirs"].items()}
                pose = pmix(pose, q, smooth(w), bns)
            quats, low = self.solve(pose)
            ang, lift, shift = {}, 0.0, 0.0
            for fn in self.acts:
                r = fn(f)
                lift += r.pop("_lift", 0.0)
                shift += r.pop("_shift", 0.0)
                for bn, axis, deg in r.pop("_extra", []):
                    ang.setdefault(bn, []).append((axis, deg))
                for bn, (axis, deg) in r.items():
                    ang.setdefault(bn, []).append((axis, deg))
            ang.setdefault("head", []).append((Z, look[f] * 0.7))
            ang.setdefault("spine", []).append((Z, look[f] * 0.3))
            hr = math.radians(h)
            sx = shift + pose["lat"] * self.L
            sy = pose["fwd"] * self.L
            zs.append(-low + pose["air"] * self.L + lift)
            loc.append([p.x + sx * math.cos(hr) - sy * math.sin(hr), p.y + sx * math.sin(hr) + sy * math.cos(hr), p.z])
            rot.append((0, 0, hr))
            for bn in bones:
                q = quats[bn]
                for axis, deg in ang.get(bn, []):
                    la = (self.rest[bn].inverted() @ axis).normalized()
                    q = q @ Quaternion(la, math.radians(deg))
                bones[bn].append(tuple(q))
        gz = [ground_z(l[0], l[1]) if self.rig.parent and not self.root.parent else 0.0 for l in loc]
        gz = [sum(gz[max(0, k - 3):k + 4]) / len(gz[max(0, k - 3):k + 4]) for k in range(len(gz))]   # step up kerbs softly
        for k in range(len(frames)):                # tiny smoothing of the height (no jitter on contact changes)
            w = zs[max(0, k - 1):k + 2]
            loc[k][2] += sum(w) / len(w) + gz[k]
        for bn, vals in bones.items():              # keep quaternions on one side (no flips between frames)
            for k in range(1, len(vals)):
                if sum(x * y for x, y in zip(vals[k], vals[k - 1])) < 0:
                    vals[k] = tuple(-x for x in vals[k])
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
                inp.keyframe_insert("default_value", frame=f)      # hard switch: two faces are never mixed
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
    """Alive while standing: breathing, slow weight shift, small head movements (on top of the standing pose)."""
    def fn(f):
        br = math.sin(2 * math.pi * f / 72 + phase)
        ws = math.sin(2 * math.pi * f / 190 + phase * 1.7)
        hd = math.sin(2 * math.pi * f / 130 + phase * 0.6)
        return {"spine": (X, 1.2 * br * amp), "hips": (Y, 1.5 * ws * amp), "head": (Z, 5 * hd * amp),
                "_extra": [("spine", Y, -1.5 * ws * amp), ("head", X, -1.0 * br * amp),
                           ("forearm.L", X, -8 * amp), ("forearm.R", X, -8 * amp)]}
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
    """Arms thrown up while cheering (the jump itself is motion capture: see cheer_on)."""
    def fn(f):
        e = env(f, f0, f1, ramp=6)
        if e <= 0:
            return {}
        sw = math.sin(2 * math.pi * (f - f0) / 16)
        return {"upper_arm.L": (Y, -150 * e), "upper_arm.R": (Y, 150 * e),
                "forearm.L": (Y, (-15 + 12 * sw) * e), "forearm.R": (Y, (15 - 12 * sw) * e)}
    return fn


def cheer_on(ch, f0, jumps=2, gain=2.2, arms=True):
    """Happy motion-captured jumps (crouch, spring, soft landing) with the arms up. Returns the end frame."""
    n = len(mocap()["jump"]["frames"])
    step = int(n * 0.72)
    for k in range(jumps):
        ch.play(f0 + k * step, "jump", rate=1.25, gain=gain, fade=5)
    f1 = f0 + jumps * step
    if arms:
        ch.add(cheer(f0 + 4, f1 - 4))
    return f1


def wave_on(ch, f0, f1, side="R"):
    """Motion-captured hello wave with one arm (the rest of the body keeps doing what it does)."""
    n = len(mocap()["wave"]["frames"])
    sd = side
    ch.play(f0, "wave", f1=f1, rate=n / max(1, f1 - f0), bones=ARM[sd] | {"spine", "head"}, mirror=(side == "L"), fade=7)
    sg = 1 if side == "R" else -1
    ch.add(lambda f: {f"upper_arm.{sd}": (Y, sg * 75 * env(f, f0 + 6, f1 - 8, ramp=8))})
    return f1


def sad(f0, f1, k=1.0):
    def fn(f):
        e = env(f, f0, f1, ramp=12) * k
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
