#!/bin/bash
# Joins all rendered segments + soundtrack into KurtarmaEkibi.mp4 (1280x720, 24 fps).
set -e
cd "$(dirname "$0")"
ORDER="intro ep_police ep_ambulance ep_fire ep_tow ep_heli game finale"
mkdir -p build/all
find "$(pwd)/build/all" -name 'f_*.png' -type l -delete
i=0
for seg in $ORDER; do
  for f in $(ls build/$seg/f_*.png | sort); do
    ln -s "$(pwd)/$f" "$(printf 'build/all/f_%05d.png' $i)"
    i=$((i+1))
  done
done
echo "frames: $i"
[ -f build/soundtrack.wav ] || python3 audio.py
ffmpeg -y -loglevel error -framerate 24 -i build/all/f_%05d.png -i build/soundtrack.wav \
  -vf "scale=1280:720:flags=lanczos,fade=t=in:st=0:d=0.5,fade=t=out:st=$(python3 -c "print($i/24-1.5)"):d=1.5" \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart \
  KurtarmaEkibi.mp4
echo "wrote KurtarmaEkibi.mp4"
