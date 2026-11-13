"""Build clean texture atlases from a character's sheet views (run with system python3).

python3 tex_prep.py <who> <front> <back> <+X view> <-X view>
Writes chars3d/<who>_atlas.png (+ _atlas_<expr>.png for each expression) and chars3d/<who>_atlas.json.
Each view sits in its own 640x1024 tile; transparent pixels are filled with the nearest colour so
UV seams never pick up background. Expression pictures are aligned to the neutral head (scale + shift
search) and only the head is swapped, so faces never slide or double up.
"""
import sys, os, json
import numpy as np
from PIL import Image
from scipy import ndimage

who, vF, vB, vXp, vXn = sys.argv[1:6]
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "chars2", who)
OUT = os.path.join(HERE, "chars3d")
TW, TH, PAD = 640, 1024, 12
EXPRS = ("happy", "sad", "surprised", "angry")


def load(n):
    return np.asarray(Image.open(os.path.join(SRC, n + ".png")).convert("RGBA")).astype(np.float32)


def fit_tile(a):
    """Scale the opaque bbox to fill the tile height (minus padding); returns tile array and mapping."""
    al = a[..., 3] > 128
    ys, xs = np.nonzero(al)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    crop = a[y0:y1, x0:x1]
    s = min((TH - 2 * PAD) / crop.shape[0], (TW - 2 * PAD) / crop.shape[1])
    w, h = max(1, round(crop.shape[1] * s)), max(1, round(crop.shape[0] * s))
    im = Image.fromarray(crop.astype(np.uint8), "RGBA").resize((w, h), Image.LANCZOS)
    t = np.zeros((TH, TW, 4), np.float32)
    ox, oy = (TW - w) // 2, (TH - h) // 2
    t[oy:oy + h, ox:ox + w] = np.asarray(im, np.float32)
    return t


def extents(t):
    """Per-row left/right of the opaque region (tile pixels), smoothed; rows top->bottom."""
    al = t[..., 3] > 128
    rows = np.nonzero(al.any(1))[0]
    top, bot = rows.min(), rows.max() + 1
    L = np.full(TH, np.nan); R = np.full(TH, np.nan)
    for y in range(top, bot):
        xs = np.nonzero(al[y])[0]
        if len(xs):
            L[y], R[y] = xs.min(), xs.max() + 1
    idx = np.arange(TH)
    ok = ~np.isnan(L)
    L = np.interp(idx, idx[ok], L[ok]); R = np.interp(idx, idx[ok], R[ok])
    L = ndimage.median_filter(L, 9); R = ndimage.median_filter(R, 9)
    return int(top), int(bot), L.tolist(), R.tolist()


def fill(t):
    """Fill transparent pixels with the nearest opaque colour (no fringes at UV edges)."""
    al = t[..., 3] > 128
    # slightly erode so anti-aliased edge pixels (mixed with background) are replaced too
    core = ndimage.binary_erosion(al, iterations=10)
    _, (iy, ix) = ndimage.distance_transform_edt(~core, return_indices=True)
    out = t[iy, ix].copy()
    out[..., 3] = 255
    return out


def align(neutral, ex):
    """Find scale/shift that puts expression picture ex onto the neutral front tile's head."""
    nal = neutral[..., 3] > 128
    rows = np.nonzero(nal.any(1))[0]
    top = rows.min(); hgt = rows.max() - top
    head_bot = int(top + hgt * 0.42)
    region = np.zeros_like(nal); region[top:head_bot] = nal[top:head_bot]
    ys, xs = np.nonzero(region)
    hcx = xs.mean()
    # expression picture: put at the same pixel scale as the neutral source picture first
    eal = ex[..., 3] > 128
    ers = np.nonzero(eal.any(1))[0]
    best = None
    small = 2
    N = neutral[::small, ::small]
    for s, ang in [(s, a) for s in np.arange(0.88, 1.15, 0.03) for a in (-12, -8, -4, 0, 4, 8, 12)]:
        sc = hgt / (ers.max() - ers.min()) * s
        w, h = max(1, round(ex.shape[1] * sc)), max(1, round(ex.shape[0] * sc))
        im = Image.fromarray(ex.astype(np.uint8), "RGBA").resize((w, h), Image.LANCZOS)
        if ang:
            # rotate about the head top-centre region so the head can be straightened
            im = im.rotate(ang, resample=Image.BICUBIC, center=(w / 2, h * 0.25))
        E = np.asarray(im, np.float32)
        Eal = E[..., 3] > 128
        er = np.nonzero(Eal.any(1))[0]
        etop = er.min()
        ehead = Eal[etop:etop + int(hgt * 0.42)]
        exs = np.nonzero(ehead.any(0))[0]
        # head centre from the head rows only (arms excluded)
        eys2, exs2 = np.nonzero(ehead)
        ecx = exs2.mean()
        for dy in range(-12, 13, 4):
            for dx in range(-12, 13, 4):
                ox = int(round(hcx - ecx + dx)); oy = int(round(top - etop + dy))
                P = np.zeros_like(neutral)
                x0, y0 = max(0, ox), max(0, oy)
                x1, y1 = min(TW, ox + w), min(TH, oy + h)
                if x1 <= x0 or y1 <= y0:
                    continue
                P[y0:y1, x0:x1] = E[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
                Ps = P[::small, ::small]
                m = (region[::small, ::small]) | (Ps[..., 3] > 128) & (np.arange(TH)[::small, None] < head_bot)
                both = region[::small, ::small] & (Ps[..., 3] > 128)
                if m.sum() == 0:
                    continue
                iou = both.sum() / m.sum()
                col = np.abs(N[..., :3] - Ps[..., :3]).mean(-1)[both].mean() / 255 if both.any() else 1
                score = iou - 0.6 * col
                if best is None or score > best[0]:
                    best = (score, P.copy())
    return best[1], top, head_bot


tiles = {}
for k, n in (("F", vF), ("B", vB), ("Xp", vXp), ("Xn", vXn)):
    tiles[k] = fit_tile(load(n))
meta = {"tile_w": TW, "tile_h": TH, "order": ["F", "B", "Xp", "Xn"], "tiles": {}}
for i, k in enumerate(meta["order"]):
    top, bot, L, R = extents(tiles[k])
    meta["tiles"][k] = {"x0": i * TW, "top": top, "bot": bot, "L": L, "R": R}


def atlas(front):
    A = np.zeros((TH, TW * 4, 4), np.float32)
    for i, k in enumerate(meta["order"]):
        A[:, i * TW:(i + 1) * TW] = fill(front if k == "F" else tiles[k])
    return A


def save(A, name):
    Image.fromarray(np.clip(A, 0, 255).astype(np.uint8), "RGBA").convert("RGB").save(os.path.join(OUT, name))


save(atlas(tiles["F"]), f"{who}_atlas.png")
meta["exprs"] = []
for ex in EXPRS:
    p = os.path.join(SRC, ex + ".png")
    if not os.path.exists(p):
        continue
    P, top, head_bot = align(tiles["F"], load(ex))
    # head mask: neutral head silhouette, feathered at the neck, restricted to where the expression is opaque
    nal = tiles["F"][..., 3] > 128
    yy = np.arange(TH)[:, None]
    neck = np.clip((head_bot + 30 - yy) / 16.0, 0, 1)
    # whole head swap (aligned incl. rotation) -> no doubled features; neck feathered
    m = (nal & (P[..., 3] > 128))
    m = ndimage.binary_erosion(m, iterations=2).astype(np.float32)
    m = ndimage.gaussian_filter(m, 1.5) * neck
    F = tiles["F"].copy()
    F[..., :3] = F[..., :3] * (1 - m[..., None]) + P[..., :3] * m[..., None]
    save(atlas(F), f"{who}_atlas_{ex}.png")
    meta["exprs"].append(ex)
    if os.environ.get("DBG"):
        Image.fromarray(F.astype(np.uint8), "RGBA").save(os.path.join(os.environ["DBG"], f"{who}_F_{ex}.png"))
with open(os.path.join(OUT, f"{who}_atlas.json"), "w") as fh:
    json.dump(meta, fh)
print("atlas ok", who, meta["exprs"])
