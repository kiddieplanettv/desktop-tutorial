#!/bin/bash
# usage: render_seg.sh <segment-name> ...
# Renders build/<seg>.blend to build/<seg>/f_####.png. Resumable: existing frames are skipped.
cd "$(dirname "$0")"
for seg in "$@"; do
  mkdir -p "build/$seg"
  # drop empty placeholder files left by an interrupted run
  find "$(pwd)/build/$seg" -name 'f_*.png' -size 0 -delete
  echo "START $seg $(date +%T) have=$(ls build/$seg | wc -l)"
  blender -b "build/$seg.blend" -a > "build/$seg.render.log" 2>&1
  echo "DONE $seg $(date +%T) frames=$(ls build/$seg | wc -l)"
done
