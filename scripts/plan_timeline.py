"""beats.json'dan intro + loop blokları + outro planı çıkarır; toplam süre şarkıyla birebir aynıdır.

Kullanım:
    .venv/bin/python scripts/plan_timeline.py public/data/beats.json -o public/data/timeline.json --fps 30
"""
import argparse
import json
import math
from pathlib import Path

MOVES_CALM = ["sway", "bounce", "armWave"]
MOVES_ENERGETIC = ["jump", "spin", "slideLeftRight", "clapUp"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("beats", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=Path("public/data/timeline.json"))
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--intro-min", type=float, default=4.0, help="intro en az kaç saniye")
    ap.add_argument("--outro-min", type=float, default=6.0, help="outro en az kaç saniye")
    ap.add_argument("--bars-per-block", type=int, default=4)
    args = ap.parse_args()

    b = json.loads(args.beats.read_text())
    fps, duration = args.fps, b["duration"]
    total = math.ceil(duration * fps)
    bars = b["downbeats"]
    energy = b["barEnergy"]
    to_f = lambda t: int(round(t * fps))

    # Intro: intro-min'den sonraki ilk ölçü başında biter.
    intro_end_bar = next((i for i, t in enumerate(bars) if t >= args.intro_min), 0)
    # Outro: şarkı sonundan outro-min önceki son ölçü başında başlar.
    outro_bar = max((i for i, t in enumerate(bars) if t <= duration - args.outro_min),
                    default=len(bars) - 1)
    outro_bar = max(outro_bar, intro_end_bar)

    intro_end = to_f(bars[intro_end_bar]) if bars else 0
    outro_start = to_f(bars[outro_bar]) if bars else total
    sections = set(b.get("sectionStarts", []))

    blocks = []
    i = intro_end_bar
    while i < outro_bar:
        j = min(i + args.bars_per_block, outro_bar)
        # Bölüm sınırı bloğun ortasına düşüyorsa bloğu orada kes.
        for k in range(i + 1, j):
            if bars[k] in sections:
                j = k
                break
        e = sum(energy[i:j]) / max(1, j - i)
        pool = MOVES_ENERGETIC if e >= 0.6 else MOVES_CALM
        blocks.append({
            "from": to_f(bars[i]),
            "durationInFrames": to_f(bars[j]) - to_f(bars[i]),
            "move": pool[len(blocks) % len(pool)],
            "energy": round(e, 3),
        })
        i = j

    out = {
        "fps": fps,
        "durationInFrames": total,
        "intro": {"from": 0, "durationInFrames": intro_end},
        "blocks": blocks,
        "outro": {"from": outro_start, "durationInFrames": total - outro_start},
        "beatFrames": [to_f(t) for t in b["beats"]],
        "downbeatFrames": [to_f(t) for t in bars],
    }
    assert out["intro"]["durationInFrames"] + sum(x["durationInFrames"] for x in blocks) \
        + out["outro"]["durationInFrames"] == total, "timeline şarkı süresini tam doldurmuyor"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))
    print(f"{args.out}: {total} kare, intro {intro_end}, {len(blocks)} blok, "
          f"outro {total - outro_start}")


if __name__ == "__main__":
    main()
