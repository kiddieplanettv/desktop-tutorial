"""Şarkı sözlerini kelime düzeyinde zamanlar ve @remotion/captions Caption[] formatında yazar.

Kullanım:
    .venv/bin/python scripts/lyrics_sync.py public/audio/song.wav -o public/data/captions.json --lang en
    (--separate ile önce demucs ile vokal ayrılır; isabet artar, süre uzar)
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def separate_vocals(audio: Path) -> Path:
    out_dir = Path("public/data/stems")
    subprocess.run([sys.executable, "-m", "demucs", "--two-stems=vocals", "-o", str(out_dir),
                    str(audio)], check=True)
    return out_dir / "htdemucs" / audio.stem / "vocals.wav"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=Path("public/data/captions.json"))
    ap.add_argument("--lang", default=None, help="en, tr ... (boşsa otomatik)")
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--separate", action="store_true")
    args = ap.parse_args()

    import whisperx

    src = separate_vocals(args.audio) if args.separate else args.audio
    audio = whisperx.load_audio(str(src))
    model = whisperx.load_model(args.model, "cpu", compute_type="int8", language=args.lang)
    result = model.transcribe(audio, batch_size=8)
    align_model, meta = whisperx.load_align_model(language_code=result["language"], device="cpu")
    aligned = whisperx.align(result["segments"], align_model, meta, audio, "cpu")

    captions = []
    for seg in aligned["segments"]:
        for w in seg.get("words", []):
            if "start" not in w:
                continue
            captions.append({
                "text": " " + w["word"].strip(),
                "startMs": round(w["start"] * 1000),
                "endMs": round(w["end"] * 1000),
                "timestampMs": round((w["start"] + w["end"]) * 500),
                "confidence": w.get("score"),
            })
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(captions, indent=2, ensure_ascii=False))
    print(f"{args.out}: {len(captions)} kelime")


if __name__ == "__main__":
    main()
