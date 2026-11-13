"""Turn CMU motion-capture clips (BVH, free to use) into a compact, rig-independent motion library.

python3 mocap_prep.py <dir with .bvh files>   ->  chars3d/mocap.json

Every frame is stored in a canonical character space (Z up, facing -Y, left = +X) as
  dirs : unit directions of thigh/shin/foot/upper_arm/forearm (L and R)
  rots : world rotations (quaternions w,x,y,z) of hips, chest and head relative to standing straight
  lat, fwd : hips offset sideways / forward (in leg lengths), air : height of the lowest foot (leg lengths)
Locomotion clips are cut to one clean loop, kept in place; 'stride' is the distance per loop in leg lengths.
"""
import sys, os, json, math
import numpy as np

SRC = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 24


def parse(path):
    toks = open(path).read().split()
    i = 0
    joints = []          # name, parent, offset, channels
    stack = []
    while toks[i] != "MOTION":
        t = toks[i]
        if t in ("ROOT", "JOINT"):
            joints.append(dict(name=toks[i + 1], parent=stack[-1] if stack else -1, off=None, ch=[]))
            cur = len(joints) - 1
            i += 2
        elif t == "End":
            joints.append(dict(name=joints[stack[-1]]["name"] + "_end", parent=stack[-1], off=None, ch=[]))
            cur = len(joints) - 1
            i += 2
        elif t == "{":
            stack.append(cur); i += 1
        elif t == "}":
            stack.pop(); i += 1
        elif t == "OFFSET":
            joints[stack[-1]]["off"] = np.array([float(x) for x in toks[i + 1:i + 4]]); i += 4
        elif t == "CHANNELS":
            n = int(toks[i + 1]); joints[stack[-1]]["ch"] = toks[i + 2:i + 2 + n]; i += 2 + n
        else:
            i += 1
    nf = int(toks[i + 2]); dt = float(toks[i + 5])
    data = np.array([float(x) for x in toks[i + 6:]]).reshape(nf, -1)
    return joints, data, dt


def rot(axis, a):
    c, s = math.cos(a), math.sin(a)
    if axis == "X":
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == "Y":
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


C = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)     # BVH (Y up, facing +Z) -> canonical (Z up, facing -Y)


def fk(joints, row):
    pos, R = {}, {}
    k = 0
    for j in joints:
        p = j["parent"]
        Rl = np.eye(3); t = np.zeros(3)
        for ch in j["ch"]:
            v = row[k]; k += 1
            if ch.endswith("position"):
                t["XYZ".index(ch[0])] = v
            else:
                Rl = Rl @ rot(ch[0], math.radians(v))
        if p < 0:
            R[j["name"]] = Rl; pos[j["name"]] = t
        else:
            pn = joints[p]["name"]
            R[j["name"]] = R[pn] @ Rl
            pos[j["name"]] = pos[pn] + R[pn] @ j["off"]
    return {n: C @ v for n, v in pos.items()}, {n: C @ m @ C.T for n, m in R.items()}


def quat(m):
    t = np.trace(m)
    if t > 0:
        s = math.sqrt(t + 1) * 2
        q = [0.25 * s, (m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s]
    else:
        i = int(np.argmax(np.diag(m))); j, k = (i + 1) % 3, (i + 2) % 3
        s = math.sqrt(1 + m[i, i] - m[j, j] - m[k, k]) * 2
        q = [0, 0, 0, 0]
        q[0] = (m[k, j] - m[j, k]) / s; q[1 + i] = 0.25 * s
        q[1 + j] = (m[j, i] + m[i, j]) / s; q[1 + k] = (m[k, i] + m[i, k]) / s
    return q


LIMBS = {"thigh": ("UpLeg", "Leg"), "shin": ("Leg", "Foot"), "foot": ("Foot", "ToeBase"),
         "upper_arm": ("Arm", "ForeArm"), "forearm": ("ForeArm", "Hand")}


def load(name, f0=None, f1=None):
    joints, data, dt = parse(os.path.join(SRC, name + ".bvh"))
    step = 1.0 / FPS / dt
    idx = [int(round(i * step)) for i in range(int((len(data) - 1) / step) + 1)]
    frames = [fk(joints, data[i]) for i in idx]
    return frames[f0:f1]


def zrot(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def build(frames, loco=False, loop=False):
    P = [f[0] for f in frames]; R = [f[1] for f in frames]
    leg = np.linalg.norm(P[0]["LeftLeg"] - P[0]["LeftUpLeg"]) + np.linalg.norm(P[0]["LeftFoot"] - P[0]["LeftLeg"])
    hips = np.array([p["Hips"] for p in P])
    if loco:
        d = hips[-1] - hips[0]; a = math.atan2(d[0], -d[1])       # rotate travel direction onto -Y
    else:
        fwd = R[0]["Hips"] @ np.array([0, -1, 0]); a = math.atan2(fwd[0], -fwd[1])
    Z = zrot(-a)
    n = len(P)
    ground = np.percentile([min(p["LeftToeBase"][2], p["RightToeBase"][2]) for p in P], 5)
    out = []
    h0 = Z @ hips[0]; h1 = Z @ hips[-1]
    for k in range(n):
        u = k / max(1, n - 1)
        p = {nm: Z @ v for nm, v in P[k].items()}
        r = {nm: Z @ m for nm, m in R[k].items()}
        base = h0 + (h1 - h0) * u if loco else h0
        fr = {"dirs": {}, "rots": {}}
        for bn, (a_, b_) in LIMBS.items():
            for side, S in (("L", "Left"), ("R", "Right")):
                v = p[S + b_] - p[S + a_]
                fr["dirs"][f"{bn}.{side}"] = (v / np.linalg.norm(v)).tolist()
        for bn, src in (("hips", "Hips"), ("spine", "Spine1"), ("head", "Head")):
            fr["rots"][bn] = quat(r[src])
        fr["lat"] = float((p["Hips"][0] - base[0]) / leg)
        fr["fwd"] = float((p["Hips"][1] - base[1]) / leg)
        fr["air"] = float(max(0.0, min(p["LeftToeBase"][2], p["RightToeBase"][2], p["LeftFoot"][2] - 0.08 * leg,
                                       p["RightFoot"][2] - 0.08 * leg) - ground) / leg)
        fr["hz"] = float((p["Hips"][2] - ground) / leg)
        out.append(fr)
    clip = {"frames": out, "loop": loop}
    if loco:
        clip["stride"] = float(np.linalg.norm((h1 - h0)[:2]) / leg)
    return clip


def cycle(name, skip=0.25):
    """One clean gait loop: from a left-foot strike to the next one, on the straightest stretch of the clip."""
    frames = load(name)[1:]
    P = [f[0] for f in frames]; R = [f[1] for f in frames]
    hips = np.array([p["Hips"] for p in P])
    rel = []
    for p, r in zip(P, R):
        fw = r["Hips"] @ np.array([0, -1, 0]); fw[2] = 0; fw /= np.linalg.norm(fw)
        rel.append((p["LeftFoot"] - p["Hips"]) @ fw)
    rel = np.convolve(np.array(rel), np.ones(3) / 3, mode="same")
    def find(sig):
        return [i for i in range(1, len(sig) - 1) if sig[i] >= sig[i - 1] and sig[i] > sig[i + 1] and sig[i] > 0.5 * sig.max()]
    peaks = find(rel)
    if len(peaks) < 2:
        peaks = find(-rel)          # short clip: loop from one push-off to the next instead
    cands = []
    for a, b in zip(peaks, peaks[1:]):
        if b - a < 8:
            continue
        seg = hips[a:b + 1, :2]
        chord = np.linalg.norm(seg[-1] - seg[0]); arc = np.linalg.norm(np.diff(seg, axis=0), axis=1).sum()
        cands.append((chord / max(arc, 1e-6), chord, a, b))
    med = np.median([c[1] for c in cands])
    cands = [c for c in cands if c[1] >= 0.85 * med and c[2] >= skip * len(rel)] or cands
    _, _, a, b = max(cands)
    seg = frames[a:b + 1]
    clip = build(seg, loco=True, loop=True)
    fr = clip["frames"]; n = len(fr)
    last, first = fr[-1], fr[0]
    for k, f in enumerate(fr):
        u = k / (n - 1)
        for key in ("lat", "fwd", "air", "hz"):
            f[key] -= (last[key] - first[key]) * u
        for bn in f["dirs"]:
            v = np.array(f["dirs"][bn]) - (np.array(last["dirs"][bn]) - np.array(first["dirs"][bn])) * u
            f["dirs"][bn] = (v / np.linalg.norm(v)).tolist()
        for bn in f["rots"]:
            q0, q1 = np.array(first["rots"][bn]), np.array(last["rots"][bn])
            if q0 @ q1 < 0:
                q1 = -q1
            q = np.array(f["rots"][bn])
            if q @ q0 < 0:
                q = -q
            q = q - (q1 - q0) * u
            f["rots"][bn] = (q / np.linalg.norm(q)).tolist()
    clip["frames"] = fr[:-1]
    print(name, "cycle", a, b, "frames", n - 1, "stride (legs)", round(clip["stride"], 2))
    return clip


if __name__ == "__main__":
    spec = json.load(open(os.path.join(HERE, "mocap_clips.json")))
    lib = {}
    for key, s in spec.items():
        if s.get("cycle"):
            lib[key] = cycle(s["src"], s.get("skip", 0.25))
        else:
            lib[key] = build(load(s["src"], s.get("f0"), s.get("f1")), loop=s.get("loop", False))
            print(key, "frames", len(lib[key]["frames"]))

    def rnd(o):
        if isinstance(o, float):
            return round(o, 4)
        if isinstance(o, list):
            return [rnd(x) for x in o]
        if isinstance(o, dict):
            return {k: rnd(v) for k, v in o.items()}
        return o
    json.dump(rnd(lib), open(os.path.join(HERE, "chars3d", "mocap.json"), "w"), separators=(",", ":"))
    print("saved", len(lib), "clips")
