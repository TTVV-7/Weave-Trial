#!/bin/bash
# round-2 reruns of the earlier function-review scripts against the revised joints/make_capybara.py
cd /home/user/Weave-Trial/fidgets/attempts/verify-round1-function
python3 fine_sweep.py 2.5 full > r2/fine_sweep_full.txt 2>&1 &
python3 fine_sweep.py 2.5 test > r2/fine_sweep_test.txt 2>&1 &
python3 nod_fine.py > r2/nod_fine.txt 2>&1 &
python3 paint_check.py > r2/paint_check.txt 2>&1
python3 misc.py > r2/misc.txt 2>&1
python3 misc2.py > r2/misc2.txt 2>&1
python3 thin_spot.py > r2/thin_spot.txt 2>&1
wait
echo done-a
