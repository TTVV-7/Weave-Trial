#!/bin/bash
# round-2: sweeps with neighbours bent, 'wiggle it out' escape searches, wrong-way slop
cd /home/user/Weave-Trial/fidgets/attempts/verify-round1-function
python3 combos.py > r2/combos.txt 2>&1
for g in "orange" "head" "front leg" "hind leg"; do python3 escape.py "$g" 400 > "r2/escape_${g// /_}.txt" 2>&1 & done; wait
for g in "joint 1" "joint 2" "joint 3"; do python3 escape.py "$g" 400 > "r2/escape_${g// /_}.txt" 2>&1 & done; wait
python3 slop_all.py > r2/slop.txt 2>&1
echo done-b > r2/done_b
