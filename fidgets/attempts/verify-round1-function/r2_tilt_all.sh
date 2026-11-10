#!/bin/bash
cd /home/user/Weave-Trial/fidgets/attempts/verify-round1-function
run() { python3 r2_tilt.py "$@" >> r2/tilt.txt 2>&1; }
: > r2/tilt.txt
( run 1 0 y 1; run 1 0 y -1; run 1 0 x 1; run 2 0 y 1 ) &
( run 1 25 y 1; run 1 25 y -1; run 1 25 x 1; run 1 25 x -1 ) &
( run 1 12.5 y 1; run 1 12.5 x 1; run 1 12.5 x -1; run 3 0 y 1; run 3 25 y 1 ) &
wait
echo done >> r2/tilt.txt
