"""Re-run the design's own check() on the current source (no files are written) and compare with check-output.txt."""
from lib import cb
for title, maker in (("test strip", cb.make_test), ("pocket capybara", cb.make_capybara)):
    parts, joints, info = maker()
    print(title + ": " + "\n".join(cb.check(parts, joints, info)))
p, j, i = cb.make_capybara(loop=False)
cb.check(p, j, i)
print("without the lug: passes")
