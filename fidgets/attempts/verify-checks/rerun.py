"""Re-run the design script with its output folder redirected here, then compare with the shipped files."""
import hashlib, pathlib, time
from common import cb, HERE
out = HERE / "rerun-out"; out.mkdir(exist_ok=True)
cb.OUT = out
t = time.time()
cb.main()
print("seconds", round(time.time() - t, 1))
src = pathlib.Path('/home/user/Weave-Trial/fidgets/attempts/joints')
for f in sorted(out.iterdir()):
    a = hashlib.sha256(f.read_bytes()).hexdigest()[:16]
    b = hashlib.sha256((src / f.name).read_bytes()).hexdigest()[:16]
    print(f.name, a, b, "SAME" if a == b else "DIFFERENT")
