"""Şarkıyı analiz eder: süre, BPM, beat'ler, ölçü başları, bölümler ve ölçü başına enerji.

Kullanım:
    .venv/bin/python scripts/analyze_audio.py public/audio/song.wav -o public/data/beats.json
"""
import argparse
import json
from pathlib import Path

import librosa
import numpy as np


def track_beats_madmom(path):
    from madmom.features.downbeats import DBNDownBeatTrackingProcessor, RNNDownBeatProcessor

    act = RNNDownBeatProcessor()(str(path))
    result = DBNDownBeatTrackingProcessor(beats_per_bar=[3, 4], fps=100)(act)
    beats = result[:, 0].tolist()
    downbeats = [t for t, pos in result if int(pos) == 1]
    beats_per_bar = int(result[:, 1].max())
    return beats, downbeats, beats_per_bar


def track_beats_librosa(y, sr):
    _, frames = librosa.beat.beat_track(y=y, sr=sr)
    beats = librosa.frames_to_time(frames, sr=sr).tolist()
    return beats, beats[::4], 4


def detect_sections(y, sr, bars, n_sections):
    """Bölüm sınırlarını (kıta/nakarat geçişleri) bulup en yakın ölçü başına yaslar."""
    if len(bars) < 4:
        return [0.0]
    feats = np.vstack([
        librosa.feature.chroma_cqt(y=y, sr=sr),
        librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13),
    ])
    bar_frames = librosa.time_to_frames(bars, sr=sr)
    synced = librosa.util.sync(feats, bar_frames, aggregate=np.median)
    k = max(2, min(n_sections, synced.shape[1] - 1))
    bounds = librosa.segment.agglomerative(synced, k)
    starts = sorted({0.0, *[float(bars[min(b, len(bars) - 1)]) for b in bounds]})
    return starts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=Path("public/data/beats.json"))
    ap.add_argument("--sections", type=int, default=8, help="hedef bölüm sayısı")
    ap.add_argument("--engine", choices=["madmom", "librosa"], default="madmom")
    args = ap.parse_args()

    y, sr = librosa.load(str(args.audio), sr=22050, mono=True)
    duration = float(len(y) / sr)

    if args.engine == "madmom":
        try:
            beats, downbeats, beats_per_bar = track_beats_madmom(args.audio)
        except Exception as e:  # madmom bazı dosyalarda başarısız olabilir
            print(f"madmom başarısız ({e}), librosa'ya geçiliyor")
            beats, downbeats, beats_per_bar = track_beats_librosa(y, sr)
    else:
        beats, downbeats, beats_per_bar = track_beats_librosa(y, sr)

    bpm = float(60.0 / np.median(np.diff(beats))) if len(beats) > 1 else 0.0

    rms = librosa.feature.rms(y=y)[0]
    rms_times = librosa.times_like(rms, sr=sr)
    edges = list(downbeats) + [duration]
    bar_energy = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (rms_times >= a) & (rms_times < b)
        bar_energy.append(float(rms[m].mean()) if m.any() else 0.0)
    peak = max(bar_energy) if bar_energy and max(bar_energy) > 0 else 1.0
    bar_energy = [round(e / peak, 3) for e in bar_energy]

    sections = detect_sections(y, sr, downbeats, args.sections)

    out = {
        "source": args.audio.name,
        "duration": round(duration, 3),
        "bpm": round(bpm, 2),
        "beatsPerBar": beats_per_bar,
        "beats": [round(t, 3) for t in beats],
        "downbeats": [round(t, 3) for t in downbeats],
        "barEnergy": bar_energy,
        "sectionStarts": [round(t, 3) for t in sections],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))
    print(f"{args.out}: {duration:.1f}s, {bpm:.1f} BPM, {len(beats)} beat, "
          f"{len(downbeats)} ölçü, {len(sections)} bölüm")


if __name__ == "__main__":
    main()
