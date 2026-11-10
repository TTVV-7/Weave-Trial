"""Run the design's own check() on all three models without writing any file."""
import time
from common import cb
for title, maker in (("test strip", cb.make_test), ("no lug", lambda: cb.make_capybara(loop=False)), ("full", cb.make_capybara)):
    t = time.time()
    parts, joints, info = maker()
    print(f"{title}: " + "\n".join(cb.check(parts, joints, info)), flush=True)
    print(f"   [{time.time()-t:.0f} s] parts: {list(parts)}; joints: {[j['name'] for j in joints]}\n", flush=True)
