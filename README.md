# Weave Trial

A see-through woven lamp shade, generated as g-code and printed as **one
continuous bead** that climbs in a wave and welds to itself on the way past.
No slicer, no layers, no supports, no vase mode.

![three densities, lit from inside](docs/densities.png)

The shade is roughly **80% open air** at the default setting. You can see the
bulb through it.

```bash
python generate.py --lamp test-ring --out out/test.gcode   # 40 mm, ~25 min
python generate.py --lamp open-weave --preview out/lamp.svg
```

Print `test-ring` first. It is the same weave at a fifth of the height, and it
tells you in twenty minutes whether your flow and cooling are right.

---

## How the weave works

The nozzle walks a spiral whose height oscillates as it goes around:

```
z(theta) = centreline(theta) + a * sin(w * theta)
```

`w`, the waves per turn, is a **half**-integer — 30.5, not 30. That half wave
is the entire trick. After one full revolution the sine has advanced by an odd
multiple of pi, so it comes back **inverted**: turn `k+1` troughs exactly where
turn `k` crests. The vertical gap between them is

```
gap(theta) = step - (a_k + a_k+1) * sin(w * theta)
```

which sweeps from a wide open diamond down to zero and back, twice per wave.
Where it reaches zero the two turns weld — 61 welds per revolution at the
default. Between the welds, an open lens-shaped hole. That is the weave, and
it is why the shade is rigid despite being mostly air.

### The two dials, and why they are separate

**`rise_per_turn`** — how far the spiral climbs per revolution. This alone
decides how see-through the shade is, because each revolution lays exactly one
bead into each `rise_per_turn` of wall height:

```
open area = 1 - bead_height / rise_per_turn
```

At the 2.2 mm default with a 0.45 mm bead, that is 80% open. Use `--open` to
set it by the number you actually care about.

**`weld_overlap`** — how far the nozzle dips below the previous turn at a weld,
which sets how strongly the two fuse. The amplitude follows from it:
`a = (rise + overlap) / 2`.

### The thing that breaks this print

It is very tempting to crank the amplitude up for bigger holes. **That does not
work, and it is the failure that wrecks the print.** The turns do not merely
touch harder. The descending half of turn `k+1` carries on down *past* turn `k`
and keeps going, so the nozzle ends up travelling underneath a bead it laid a
revolution ago, with that bead sitting directly over the nozzle shaft. It
catches, and the print comes off the plate.

The safe regime is a shallow dip — about one bead height or less — so a weld is
an ordinary squish rather than a crash. **Bigger holes come from raising
`rise_per_turn`, never from raising the amplitude.**

Two things enforce that rather than just documenting it:

- The centreline is **solved, not shaped**. `step()` in `weave/geometry.py`
  pins the deepest point of every weld to exactly `-weld_overlap` and solves
  for the climb, so the transition turns hold the same weld depth as the
  middle of the shade. Hand-picked ramp curves cannot do this — they leave the
  fade-in and fade-out turns either floating apart or ploughing in.
- `check_support()` re-measures the **generated path**, comparing every sample
  against the point one revolution earlier. It reports the deepest dip, the
  longest unsupported bridge, and any revolution that never touches the one
  below it. `generate.py` refuses to write g-code when that check fails.

```
$ python generate.py --lamp open-weave --check-only
open-weave: 152 mm tall, 90 mm across
  open area      80%  (holes up to 4.8 mm tall)
  weave          30.5 waves/turn, 61 welds/turn, 29deg slope
  bead           39 m, 6 g, 36902 points
  weld dip       0.32 mm (bead is 0.45 mm)
  longest bridge 7.9 mm unsupported
  printability   OK
```

---

## Shades

| preset | size | open | notes |
|---|---|---|---|
| `open-weave` | 150 x 90 mm | 80% | the default; see-through and still rigid |
| `airy` | 150 x 90 mm | 87% | wide diamonds, longer bridges, print it slow |
| `frosted` | 150 x 90 mm | 64% | fine slits, soft even glow, no visible bulb |
| `table-shade` | 110 x 120 mm | 81% | short and wide, slight taper |
| `pendant` | 180 x 110 mm | 81% | tapered with a waist |
| `test-ring` | 40 x 60 mm | 80% | print this first |

`python generate.py --list` also lists the printers and materials.

Anything can be overridden: `--height --radius --top-radius --belly --open
--rise --waves --overlap --bead --nozzle`. `--waves` must end in `.5`; a whole
number stacks the waves instead of weaving them, and is rejected.

`--open` retunes the shade and then **re-measures** it, packing the waves
tighter if opening it up has stretched the unsupported bridges past 12 mm.
Above about 90% open the technique runs out and the check starts failing, which
is the honest answer rather than a shade that droops.

---

## Printing it

Single wall, no infill, no supports — there is nothing for a slicer to decide.
**Do not open the g-code in a slicer.** It is a non-planar path; re-slicing it
flattens it back into layers and you lose the weave.

| setting | value |
|---|---|
| nozzle | 0.4 mm |
| bead | 0.45 x 0.45 mm, round, in free air |
| weave speed | 14–18 mm/s — this is the one that matters |
| fan | 100% over the whole weave, off for layer 1 |
| foot / rim | 3 solid walls, 0.25 mm layers |
| material | translucent PLA is easiest; PETG is tougher but droops more |

The free-air spans are the whole game. Each bead crosses up to about 8 mm of
open air before it reaches its next weld, so it has to set before it sags:
**slow, and full cooling.** If the bridges droop, drop the weave speed before
you touch anything else.

The foot and rim are ordinary stacked walls, so the shade starts and ends
solid and has something to stand on and something to clamp a fitting to.

Use an **LED bulb.** The shade is thin plastic and it is not a heat shield.

## Layout

```
generate.py                    CLI
weave/geometry.py              the weave: centreline solver + check_support
weave/gcode.py                 g-code writer (no dependencies)
weave/profiles.py              printers, materials, shade presets
weave/preview.py               SVG preview: elevation, detail, lit
weave/fullcontrol_backend.py   optional: emit via FullControl instead
tests/test_weave.py            34 tests, incl. the crash mode above
```

```bash
python -m pytest tests -q
```

---

## Also here: a windshield washer nozzle

Same idea, different object. [`docs/washer-nozzle.md`](docs/washer-nozzle.md)
generates a replacement washer nozzle as STL from two caliper readings and a
photograph of the hole it has to fit. The hole is a distance field, every
section of the part is an offset of it, and the body is written as a single
closed tube, so the channel that must not leak has no boolean subtraction
anywhere near it.

```bash
python nozzle.py --check-only
python nozzle.py --part gauge --out out/gauge.stl     # print this one first
python nozzle.py --part all --out out/plate.stl --preview out/nozzle.svg
```

```
nozzle.py                      CLI
washer/geom.py                 the hole outline, as distance fields
washer/mesh.py                 rings, tubes, hexahedra, watertightness, STL
washer/parts.py                nozzle, wedge clip, fit gauge
washer/check.py                does it go in, hold, flow, and print
tests/test_nozzle.py           52 tests
```

## Provenance

The technique here was worked out from the geometry, not transcribed from a
source. The r/FullControl post that prompted it could not be read from the
environment this was built in (the network policy blocks reddit.com), so if
that post specifies particular parameters, they are not reflected here — treat
the numbers as independently derived and check them against it.

FullControl itself is optional and only used by `--fullcontrol`, which emits
the same geometry through `fc.transform` for its viewer and printer library.
The default writer is the built-in one, which is what knows about the
per-bead extrusion heights the fade regions need.
