#!/bin/bash
# quick check of every segment for vehicles driving into each other (no scenery, nothing saved)
cd "$(dirname "$0")"
for s in "${@:-t_intro t_ep1 t_ep2 t_ep3 t_ep4 t_outro}"; do for x in $s; do blender -b -P $x.py -- --lo --dry 2>&1 | grep -E "OVERLAP|TIDY|OFFROAD|RETIME|Error|Traceback|FRAMES|line "; done; done
