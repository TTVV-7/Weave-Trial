# iPad holder: threaded clamp, wing screw, logos

![back, clamp thread, wing screw](preview.png)

```bash
pip install trimesh manifold3d matplotlib
python ipad_holder/make_holder.py
```

Reads `source_ipad_holder.3mf` and the two logo SVGs, and writes:

| file | what |
|---|---|
| `ipad_holder.3mf` | the holder, as one object with three parts: body, VanEye logo, printyours.ca logo |
| `wing_screw.3mf` / `.stl` | the M5 wing screw ("butterfly key") |

## The thread

The 5.2 mm hole through the left corner of the diamond loop is now an
**M5 x 0.8** thread (60°, right hand). It is opened up for printing (major
5.30, minor 4.35), so the printed wing screw fits and so does a steel M5.
The wall there is about 4.3 mm, which gives roughly five turns of
engagement. Tighten it by hand, not with a tool.

## The wing screw

The thread is 15 mm long and the wings span 30 mm. Print it head down, with
the wings flat on the bed and the thread pointing up. That way the thread
prints round, with no supports. Its thread is undersized (4.80 major) so it
runs freely in the printed hole.

## The logos

Both logos sit in the back face, the face on the bed. They are 0.4 mm deep,
which is two 0.2 mm layers, and they are mirrored so they read correctly
from behind. Each logo is its own part, so in the slicer you give the body
one filament and each logo another. Change the depth with `INLAY_DEPTH`,
and the position or size with `LOGOS`, in `make_holder.py`.
