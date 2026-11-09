# Basketball fidgets (3D print files)

Two basketball fidgets, each as a **painted 3MF** (orange ball, black seams) and a
plain single-colour STL. The seams are real 0.6 mm grooves, so they still read as
basketballs printed in one colour.

![the gyro as printed and mid-spin, and the spinner with its caps](preview.png)

| Fidget | Files | Size (mm) | Hardware |
|---|---|---|---|
| **Basketball gyro**: a ball spinning inside four rings, print-in-place | `stl/basketball-gyro.3mf` / `.stl` | 56 × 56 × 17 | none |
| **Basketball spinner**: three-lobe spinner with a basketball on each lobe | `stl/basketball-spinner.3mf` (body and 2 caps on one plate), or `stl/basketball-spinner.stl` + 2 × `stl/basketball-spinner-cap.stl` | 80 × 73 × 7 | one 608 bearing (22 × 8 × 7, the skateboard kind) |

## Filaments

Both use the same three filaments in the same slots, so they can share a plate.

| Slot | Filament | Hex | Paints |
|---|---|---|---|
| T1 | Orange | `#E86A1C` | the ball, the lobe faces, the gyro's outer ring |
| T2 | Black | `#1A1A1A` | seams, the 1st and 3rd gyro rings, the spinner body |
| T3 | White | `#F2F2F2` | the 2nd gyro ring |

The 3MFs use Bambu Studio's painting format, so they open the same in Bambu Studio
(P1S + AMS), OrcaSlicer and Snapmaker Orca (U1).

## Basketball gyro

It prints in one piece and comes off the plate already assembled: the ball pivots
in ring 1 on two cone pins, ring 1 pivots in ring 2 at 90° to that, and so on out.
Spin the ball with a finger, or flick the outer ring and let the rings tumble.

- Print it flat, as it comes. **No supports** (they'd fill the gaps and weld it
  solid). The steepest overhang is the underside of the ball, at 45°.
- 0.2 mm layers, 3 walls, 15% infill. Turn off "ironing" and keep the first layer
  from being over-squished: the rings are 0.6 mm apart on the bed.
- When it comes off the plate, hold the outer ring and gently twist each ring in
  turn until it frees up. A few spins and it loosens.
- Pins have 0.35 mm of clearance all round. If yours fuse, raise `PIN_CLEAR` to
  0.45 (and `GAP` to 0.7) in `make_fidgets.py` and re-run; if they're sloppy,
  drop it to 0.3.

## Basketball spinner

- Print the body flat. The seams on the underside are grooves on the bed face, so
  they print as clean first-layer lines. No supports.
- Use 4 walls and 40%+ infill: the lobes are the weight, and heavier spins longer.
- Print the caps flat face down (the orange basketball face is on the bed), peg up.
- **Assembly:** press the 608 bearing into the hub (it's a 22.15 mm press fit;
  a vice or a table edge helps). Then push a cap into the bearing from each side.
  Each cap only touches the bearing's inner race, so the body spins freely.
- For a longer, quieter spin, wash the grease out of the bearing with
  isopropyl alcohol first.
- If the bearing is loose, glue it, or lower `BEARING_FIT`; if it won't go in,
  raise it.

## Changing them

Every dimension is a constant at the top of `make_fidgets.py` (ball size, ring
count and thickness, clearances, lobe size, bearing size, colours). Then:

```bash
python3 make_fidgets.py   # writes stl/*.3mf and stl/*.stl
python3 preview.py        # redraws preview.png and stl/*.png from the 3MFs
```

Needs `pip install numpy trimesh manifold3d matplotlib`.

Before writing anything, `make_fidgets.py` turns every gyro pivot through a full
circle and stops if a ring jams or comes apart from its pins:

```
gyro: every pivot turns a full circle, tightest gap 0.35 mm
```
