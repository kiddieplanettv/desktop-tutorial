#!/bin/bash
# render_meyve.sh <python with bpy 5.2> [meyve.py options]   builds the scene and renders it with two processes
cd "$(dirname "$0")"; PY=$1; shift
$PY meyve.py "$@" > build.log 2>&1; grep -q BUILT build.log || { echo BUILD FAILED; tail -5 build.log; exit 1; }
$PY render52.py build/meyve.blend > build/r1.log 2>&1 &
sleep 10
$PY render52.py build/meyve.blend > build/r2.log 2>&1 &
wait
find build/kareler -name 'f_*.png' -size 0 -delete
$PY render52.py build/meyve.blend > build/r3.log 2>&1
echo "DONE $(ls build/kareler | wc -l) frames $(date +%T)"
