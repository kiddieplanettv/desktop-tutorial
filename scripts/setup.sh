#!/usr/bin/env bash
# Projeyi sıfırdan kurar: Node paketleri, Python ortamı, referans repolar.
# Kullanım: bash scripts/setup.sh
set -euo pipefail
cd "$(dirname "$0")/.."

command -v ffmpeg >/dev/null || { echo "ffmpeg bulunamadı (apt install ffmpeg / brew install ffmpeg)"; exit 1; }

echo "==> Node paketleri (remotion, rive, lottie, spine)"
npm ci

echo "==> Python ortamı (.venv): librosa, madmom, demucs, whisperx"
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip setuptools wheel cython numpy
.venv/bin/pip install -q -r requirements.txt

echo "==> Referans repolar (vendor/, git'e girmez)"
mkdir -p vendor
[ -d vendor/AnimatedDrawings ] || git clone -q --depth 1 https://github.com/facebookresearch/AnimatedDrawings vendor/AnimatedDrawings

echo "==> Kontrol"
.venv/bin/python -c "import librosa, madmom, demucs, whisperx; print('python ok')"
npx tsc --noEmit && echo "typescript ok"
