"""Sweeps at 2.5 deg with neighbouring joints bent; runs fine_sweep.py cases in parallel."""
import subprocess, json, sys
from concurrent.futures import ThreadPoolExecutor
CASES = [
 ({"body joint 1": 25}, "front", "f_b1p25"), ({"body joint 1": -25}, "front", "f_b1m25"),
 ({"body joint 1": 29}, "front", "f_b1p29"), ({"body joint 1": -29}, "front", "f_b1m29"),
 ({"body joint 3": 25}, "hind", "h_b3p25"), ({"body joint 3": -25}, "hind", "h_b3m25"),
 ({"body joint 3": 29}, "hind", "h_b3p29"), ({"body joint 3": -29}, "hind", "h_b3m29"),
 ({"body joint 1": 29, "body joint 3": 29}, "joint 2", "j2_pp"), ({"body joint 1": -29, "body joint 3": 29}, "joint 2", "j2_mp"),
 ({"body joint 2": 29, "head nod": 18}, "joint 1", "j1_p_up"), ({"body joint 2": -29, "head nod": -18}, "joint 1", "j1_m_dn"),
 ({"body joint 2": 29, "hind left leg": 45, "hind right leg": -45}, "joint 3", "j3_p"),
 ({"body joint 2": -29, "hind left leg": -45, "hind right leg": 45}, "joint 3", "j3_m"),
 ({"body joint 1": 29, "front left leg": 90, "front right leg": -90}, "nod", "nod_b1p"),
 ({"body joint 1": -29, "front left leg": -90, "front right leg": 90}, "nod", "nod_b1m"),
 ({"head nod": 18}, "front", "f_nodup"), ({"head nod": -18}, "front", "f_noddn"),
]
def run(c):
    pose, only, tag = c
    r = subprocess.run([sys.executable, "fine_sweep.py", "2.5", "full", json.dumps(pose), only], capture_output=True, text=True)
    return r.stdout + r.stderr[-500:]
with ThreadPoolExecutor(4) as ex:
    for out in ex.map(run, CASES):
        print(out, flush=True)
