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

## The diamond loop

The loop's walls are grown 1 mm on the outside and 1 mm into the opening
(`LOOP_GROW`), taking them from 3 mm to 5 mm. The opening is now 7.2 mm per
side instead of 9.2 mm.

## The thread

The source's 5.2 mm hole at 9 o'clock is filled. The thread is now an
**M5 x 0.8** (60°, right hand) through the upper-right wall, square to the
wall so the wings seat flat. It is opened up for printing (major 5.30, minor
4.35), so the printed wing screw fits and so does a steel M5. The 5 mm wall
gives about six turns of engagement.

It sits at about 1:50 rather than exactly 2 o'clock. The inside of that wall
is only 7.2 mm long and the screw is 4.8 mm across. Exactly 2 o'clock would
put the screw 0.2 mm from the lower-right wall as it goes in, so it is held
0.5 mm clear (`SCREW_GAP`). The screw can reach 3.2 mm into the opening
before it meets the opening's flat bottom, so it clamps anything at least
about 4 mm across.

The script checks the fit every run. It turns the screw head a full
revolution in 5° steps against the holder, then pushes a rod the screw's
diameter across the opening. At 2 o'clock the wings point up and away. The
lowest wing tip clears the frame by 7.3 mm, so the longer neck that 9 o'clock
needed has gone (`LOOP_RAISE` = 0). The neck runs 1 mm into the frame wall,
because in the source file it only touched the frame and was a separate
solid.

## Power button

A slot runs through the top wall and its lip in the top-right corner (seen
from the front), from the pocket floor and open to the front, so a finger
reaches the iPad mini's top button. It spans 6 to 30 mm in from the right
inside wall (`POWER_SLOT`). That is generous, because Apple publishes no
exact position for the button.

## The wing screw

The thread is 10 mm long, which covers the 5 mm wall plus the 3.2 mm the
screw can reach, and the wings span 30 mm. Print it head down, with the
wings flat on the bed and the thread pointing up. That way the thread prints
round, with no supports. Its thread is undersized (4.80 major) so it runs
freely in the printed hole.

## The logos

Both logos sit in the back face, the face on the bed. They are 0.4 mm deep,
which is two 0.2 mm layers, and they are mirrored so they read correctly
from behind. Each logo is its own part, so in the slicer you give the body
one filament and each logo another. Change the depth with `INLAY_DEPTH`,
and the position or size with `LOGOS`, in `make_holder.py`.
