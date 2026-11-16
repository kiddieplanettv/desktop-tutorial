#!/bin/bash
# render_toy.sh <segment> ...   builds each scene at full size and renders it with two Blender processes
cd "$(dirname "$0")"
for seg in "$@"; do
  blender -b -P $seg.py > build/$seg.build.log 2>&1
  grep -q BUILT build/$seg.build.log || { echo "BUILD FAILED $seg"; continue; }
  blender -b build/$seg.blend -a > build/$seg.r1.log 2>&1 &
  sleep 12
  blender -b build/$seg.blend -a > build/$seg.r2.log 2>&1 &
  wait
  find build/$seg -name 'f_*.png' -size 0 -delete
  blender -b build/$seg.blend -a > build/$seg.r3.log 2>&1
  echo "DONE $seg $(ls build/$seg | wc -l) frames $(date +%T)"
done
