import subprocess, sys
from concurrent.futures import ThreadPoolExecutor
C = [("joint", "y", 1), ("joint", "y", -1), ("joint", "x", 1), ("joint", "z", 1),
     ("head", "x", 1), ("head", "z", 1), ("head", "y", 1), ("head", "y", -1), ("leg", "x", 1), ("leg", "x", -1), ("leg", "z", 1)]
def run(c):
    r = subprocess.run([sys.executable, "slop.py", c[0], c[1], str(c[2]), "700"], capture_output=True, text=True)
    return (r.stdout + r.stderr[-400:]).strip()
with ThreadPoolExecutor(4) as ex:
    for o in ex.map(run, C):
        print(o, flush=True)
