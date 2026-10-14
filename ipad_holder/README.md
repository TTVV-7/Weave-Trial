# iPad holder: threaded clamp, wing screw, logos

![back, clamp thread, wing screw](preview.png)

```bash
pip install trimesh manifold3d matplotlib
python ipad_holder/make_holder.py
```

Reads `source_ipad_holder.3mf` and the two logo SVGs, and writes:

| file | what |
|---|---|
| `ipad_holder.3mf` | the holder, as one object with two parts: the body and the VanEye logo |
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

## Rounded edges

The case's four corners are rounded to 8 mm, seen from the front
(`CORNER_R`). The pocket's two closed corners on the left are rounded to
5 mm about the same centres (`POCKET_R`), so the wall stays 3 mm all the way
round. The right side is open below the lip, so it has no inside corners.
The front and back perimeter edges are rounded over by 1.5 mm (`EDGE_R`).

## Power button

A slot runs through the top wall and its lip in the top-right corner (seen
from the front), from the pocket floor and open to the front, so a finger
reaches the iPad mini's top button. It spans 9 to 33 mm in from the frame's
right outside edge (`POWER_SLOT`). That is generous, because Apple publishes no
exact position for the button.

## The wing screw

The thread is 10 mm long, which covers the 5 mm wall plus the 3.2 mm the
screw can reach, and the wings span 30 mm. Print it head down, with the
wings flat on the bed and the thread pointing up. That way the thread prints
round, with no supports. Its thread is undersized (4.80 major) so it runs
freely in the printed hole.

## The logos

Both logos sit in the back face, the face on the bed, and are mirrored so
they read correctly from behind.

- **VanEye** is a 0.4 mm inlay (two 0.2 mm layers) and its own part, so in
  the slicer you give it its own filament.
- **printyours.ca** is etched: a 0.4 mm recess in the body's own colour
  (`ETCH_DEPTH`). It stays 42 mm wide.

Change the size, position or kind (`"inlay"` or `"etch"`) with `LOGOS` in
`make_holder.py`.
