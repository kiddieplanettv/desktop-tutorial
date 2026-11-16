#!/bin/bash
# assemble_toy.sh <output.mp4> <segment> ...   joins rendered segments (short fades between them) and adds the soundtrack
cd "$(dirname "$0")"
out=$1; shift
list=build/_toy_concat.txt; : > $list
for seg in "$@"; do
  n=$(ls build/$seg/f_*.png | wc -l)
  ffmpeg -v error -y -framerate 24 -i build/$seg/f_%04d.png -vf "fade=in:0:10,fade=out:$((n-10)):10" -c:v libx264 -crf 17 -preset medium -pix_fmt yuv420p build/$seg.mp4
  echo "file '$seg.mp4'" >> $list
done
segs=$(IFS=,; echo "$*")
python3 audio.py "$segs" _toy.wav
ffmpeg -v error -y -f concat -safe 0 -i $list -i build/_toy.wav -c:v copy -c:a aac -b:a 192k -shortest "$out"
echo "ASSEMBLED $out $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out")"
