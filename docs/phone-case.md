# The phone case generator

A parametric iPhone case, written straight to multi-tool g-code, with your
artwork painted onto the outside of the back by the AMS -- or as an STL, if
you would rather slice it yourself.

```bash
python case.py --list
python case.py --phone iphone-16-pro --test-fit            # print this first
python case.py --phone iphone-16-pro --art logo.svg --palette duo
python case.py --phone iphone-17-pro --no-gcode --stl case.stl
python case.py --phone iphone-17-pro --art logo.svg --3mf case.3mf
```

There is also a browser front end, at
[3-d-print-sandbox.vercel.app/case](https://3-d-print-sandbox.vercel.app/case).
It runs a **vendored copy** of this package, in
[ttvv-7/3D-print-sandbox](https://github.com/TTVV-7/3D-print-sandbox): this
repository is where the generator is developed and tested, so fix things here
and copy `phonecase/` across, updating the `PROVENANCE` string in that repo's
`src/case_app.py` as you go.

The case prints **back face down**, so the artwork is layer 1, against the
build plate. That is the flattest, glossiest surface the printer can make and
the only one worth painting. It is also the face you cannot see while it
prints, which is why the generator mirrors the artwork for you and why the
preview shows you the toolpath the right way round rather than showing you
your own SVG back again.

---

## Print the test fit first

```
$ python case.py --phone iphone-16-pro --test-fit
iphone-16-pro / snug: 75.6 x 153.7 x 11.1 mm
  fit            0.35 mm gap, wall 1.70 mm (4 perimeters at 0.425 mm)
  back plate     1.30 mm, 6 layers, artwork on the first 2
  lip            1.20 mm tall, 0.90 mm in (37 deg overhang)
  cutouts        camera, port, speaker-, speaker+, power, volume-up, ...
  TEST FIT       back plate reduced to a 7 mm rim, artwork off
  filament       11.3 g
  printability   OK
```

`--test-fit` keeps the walls and a rim of back plate around the outline and
around every hole, and leaves the middle open. Everything that can be wrong
about a case is still in it — the outside size, the corner radius, the
clearance, the wall, the lip, and where the camera and the port are — at
about half the filament and none of the purge.

You need it, because **the camera opening and the button positions are
estimates.** The *shape* of the camera is not a guess -- a 17 Pro's cameras
sit in a bar across the whole width of the back, and putting a corner island
there would cover two of the three lenses, so `camera_style` distinguishes
`corner` from `plateau` and the plateau is sized from the body rather than
given as a number. The millimetres are still estimates. The body dimensions in `phonecase/spec.py` are published specs.
The camera island and the buttons are not published, and nothing in this
repository has been measured against a real phone. If the test fit is wrong,
measure yours and pass the numbers:

```bash
python case.py --phone iphone-16-pro \
    --camera 40x40:12 --camera-margin 2.6,3.4 \
    --length 149.6 --width 71.5 --thickness 8.25
```

---

## A 3MF, if you want the colours in your slicer

```bash
python case.py --phone iphone-17-pro --art logo.svg --palette primary \
    --no-gcode --3mf case.3mf
```

```
wrote case.3mf (0.05 MB, 4 parts, 4792 triangles)
    T1 ink          #1B1B1FFF  18.30 cm3
    T0 bone         #F4F4F2FF   0.09 cm3
    T2 red          #E03131FF   0.72 cm3
    T3 blue         #1C7ED6FF   0.44 cm3
```

An STL is one colour by construction. A 3MF can hold several, so this is the
one to take if you want to slice the case yourself and still have the
artwork come out in the right filaments.

**The artwork becomes real geometry.** Each SVG shape is turned into a 2-D
region in case coordinates, the stack is walked from the top down so a shape
is kept only where nothing drawn after it covers it -- the same painter's
rule the raster follows -- and each colour's region is extruded to the depth
of the artwork layers and intersected with the case. So the back plate is
cut into inlays that *are* the picture, and the body is the case with those
inlays taken out of it. The parts add up to exactly the whole case: no
overlaps, no gaps, tested to a millionth.

**The structure is the card generator's**, one object per colour grouped by
`<components>` into a single object, pointing into a `<basematerials>` list
-- copied rather than invented because it is the structure known to survive
the trip into a real slicer.

What a 3MF cannot carry is *how* the printer gets there: the purge tower,
the tool-change ordering, the per-layer flush. None of that is geometry. The
g-code remains the thing that prints; this is the thing you can slice.

Two caveats worth reading:

- **The slicer round-trip is not verified from here.** The package is checked
  against the spec -- valid zip, well-formed XML, one material per part, the
  components pointing at the meshes, the build item placing it on the plate
  -- and the colours are checked against the same raster the g-code uses.
  What has not been done is opening it in Bambu Studio. Open it once and
  look before you commit to a print.
- **`--wrap` extrudes the colour through the whole wall**, not just the
  outermost perimeter the g-code paints. A wrapped case is more faithful as
  g-code.

## An STL, if you would rather slice it yourself

```bash
python case.py --phone iphone-17-pro --no-gcode --stl case.stl
python case.py --phone iphone-17-pro --art logo.svg --3mf case.3mf
```

```
wrote case.stl (0.10 MB, 1952 triangles, 19.5 cm3)
```

Built from the same `CaseSpec` as the g-code, **not traced from the
toolpath**, so it is the real shape rather than a rendering of the beads. Use
it to paint the case in your slicer's own colour tool, to look at it before
committing, or to take the shape somewhere else.

It is deliberately not marching anything. A phone case is mostly flat faces
and straight walls, and putting a grid through it turns a back plate that
wants a hundred triangles into three hundred thousand. Every surface here is
what it actually is: the shell, the cavity and the lip are stacks of rounded
rectangles stitched into watertight tubes, with the base chamfer and the lip
taper one exact loft each; every cutout is a convex prism. A whole case is
about two thousand triangles and a tenth of a megabyte.

Which leaves one thing needing a library — subtracting the cutouts.
`manifold3d` does that and is the only non-stdlib import in
`phonecase/solid.py`; the rounded rectangles, the half-plane clip, the lofts
and the binary STL are all written out. Without it installed, `--stl` says so
and the g-code writer carries on regardless.

Two things worth knowing:

- **`--test-fit` has no STL.** Leaving the middle of the back plate unfilled
  is a thing g-code can say and a solid cannot, so asking for both is
  refused rather than quietly giving you a different part.
- **The STL's volume is not the g-code's filament figure.** A 15 Pro is
  18.7 cm³ of solid, which is 23 g of PLA if it were truly solid; the g-code
  says 20 g. The difference is the corner voids between adjacent beads, and
  the extrusion model that accounts for them is the same one PrusaSlicer
  uses. Neither number is wrong.

## The artwork

Any SVG with flat fills. Point it at the back of the case and it is
rasterised into a grid of AMS slot numbers over the footprint; every perimeter
and every infill line is then cut where that grid changes colour.

```bash
python case.py --phone iphone-15 --art logo.svg --palette primary --show-art
```

```
logo.svg: 5 filled shapes
  #1b1b1f   74.9% -> T1 ink #1b1b1f
  #e03131   12.0% -> T2 red #e03131
  #1c7ed6    7.2% -> T3 blue #1c7ed6
  #f4f4f2    5.9% -> T0 bone #f4f4f2
  on the case:
    T0 bone            1678 mm2
    T1 ink             7102 mm2
    T2 red             1576 mm2
    T3 blue             962 mm2
```

`--show-art` answers the two questions worth asking before printing: which
filament each colour in your drawing became, and how much of the case each
one ends up covering. If two of your colours land on the same slot it says
so — they are about to merge.

### What the SVG reader does and does not do

| | |
|---|---|
| paths | every command, arcs included, flattened adaptively |
| shapes | `rect` (incl. `rx`/`ry`), `circle`, `ellipse`, `polygon`, `polyline`, `line` |
| transforms | `translate`, `scale`, `rotate`, `matrix`, `skewX`, `skewY`, nested |
| fill | attribute or `style`, inherited, `evenodd` and `nonzero` |
| strokes | **converted to fills**, with round and square caps |
| gradients | flattened to their first stop, and it tells you |
| `<text>` | **not rendered.** Convert text to paths before you export |
| `<use>`, `<image>`, filters, clip paths | skipped, and listed in the warnings |

Strokes becoming fills matters more than it sounds: a lot of line art has no
fills at all, and silently printing nothing would be a poor answer to "paint
this on my case".

### Placing it

`--art-fit contain` (default) fits the whole drawing on the back; `cover`
fills the back and crops; `stretch` distorts; `none` treats user units as
millimetres. Then `--art-scale`, `--art-rotate`, `--art-x`, `--art-y` and
`--art-margin` move it around, and `--art-box view` fits the SVG's viewBox
instead of the drawing's own bounding box. On the web page, drag the artwork
on the preview and scroll to scale it; the sliders follow, and the sliders
still work on their own.

**`--art-x` and `--art-y` are in the frame you look at the case in**, not the
one the g-code is written in: positive x is to the right *as you hold the
finished case*, which is the case's -x, because everything on that face is
mirrored. A control that pushes the opposite way from the picture above it is
not a control, it is a puzzle.

`--no-mirror` turns the mirror off. **This makes the case come out
backwards** and exists only because occasionally that is what you want — art
you intend to read through a transparent filament, for instance.

### The palette

```bash
--palette primary
--slot 0=#2b2f36:graphite --slot 1=#e4572e:coral --slot 2=#f4f4f2:bone
```

Slot numbers are AMS slot numbers, so `--slot 2=...` is the third bay.
Artwork colours are matched to the nearest loaded filament by redmean
distance rather than plain RGB, because plain RGB decides a saturated red is
closer to a saturated blue than to a dark red, and that is exactly the swap
you notice on a finished case.

The **body colour** — the sides, the inside, and everything under the skin —
defaults to whatever the artwork mostly is, so a case with a black background
has black sides. `--base N` overrides it.

---

## What a colour change costs

Every tool change flushes the old colour out of the nozzle, by default
110 mm³, and it has to go somewhere that is not the case. The generator
builds its own purge tower, because nothing downstream is going to.

The design decision that matters: the tower is only printed on the layers
that need it.

```
tool changes   8 (tower 46 x 40 mm, 3 layers)
filament       19.9 g + 1.5 g purged
```

Artwork on the back plate changes colour for the first two layers and never
again, so the tower is three layers tall and costs 1.5 g. Compare `--wrap`,
which carries the artwork up the outside of the side walls:

```
tool changes   96 (tower 50 x 40 mm, 51 layers)
filament       19.2 g + 24.2 g purged
! the purge tower (24 g) outweighs the case (19 g)
```

That is not a bug, it is what multi-material printing costs when the colour
changes on every layer. `--wrap` is worth it when the sides are the point.
`--purge 60` halves the flush if your colours are close; `--purge 250` if you
are putting white over black.

Only the **outermost** perimeter is ever painted on the sides, and only the
first `--art-layers` (default 2) of the back plate are painted at all.
Everything under the skin is the body colour, because nobody can see it and
every colour change down there is another gram in the bin.

---

## Cases and phones

### The camera, per phone

| style | phones | opening |
|---|---|---|
| `corner`, square | 13/14/15/16 Pro and Pro Max | ~39 x 39 island, top corner |
| `corner`, pill | 15, 15 Plus, 16, 16 Plus, 17 | ~27 x 47 vertical pill |
| `corner`, diagonal | 13, 14 | ~34 x 34 |
| `corner`, small | SE (3rd gen) | ~17 x 17 |
| `plateau` | 17 Pro, 17 Pro Max | full width, ~34 mm tall, centred |
| `plateau` | Air | full width, ~26 mm tall, one lens |

The plateau height was wrong to begin with -- 25 mm, which is shorter than
the three-lens cluster that has to fit inside it. The same triangle of lenses
needs a 39 mm island on a 16 Pro, so the bar holding it cannot be much under
thirty: the opening and the hardware are not independent, and a plateau too
short for its own lenses is a case with plastic over one. A test now compares
how big a lens each opening can hold and complains when phones with the same
cluster disagree by more than a third.

It is still an estimate. Measure yours and pass `--camera 68x34:12
--camera-margin 2.5,2`; the web page has the same five fields, starts them
from the phone's defaults, outlines whichever you have moved, and prints the
command line that reproduces what it used.

A plateau leaves the back plate holding on a few millimetres of material
above and beside it. That is true of the real cases too, and `check_case`
measures it and complains if your wall and clearance make it thinner.

| preset | clearance | wall | back | lip | |
|---|---|---|---|---|---|
| `snug` | 0.35 | 1.7 | 1.3 | 1.2 | the default |
| `slim` | 0.30 | 1.2 | 1.0 | 0.8 | faster, thinner, protects less |
| `rugged` | 0.40 | 2.4 | 1.8 | 2.0 | noticeably chunkier |
| `test` | 0.50 | 1.6 | 1.2 | 1.0 | loose, for an unfamiliar phone |

`python case.py --list` prints the phones, printers, filaments and palettes.
Anything can be overridden: `--clearance --wall --back --lip --lip-inset
--chamfer --layer-height --line-width --nozzle`.

---

## Printing it

| setting | value |
|---|---|
| nozzle | 0.4 mm |
| layers | 0.2 mm, 0.24 first |
| material | PLA is easiest; PETG is tougher; TPU is the *right* answer and the wrong one for an AMS |
| supports | none — there is nothing that needs them |
| bed | clean and degreased. Layer 1 is the artwork |

Layer 1 is the face you will look at every day, so the usual first-layer
advice is not optional here: level the bed, wipe it with alcohol, and do not
print the artwork onto a plate with a fingerprint on it.

TPU deserves a note. It is the material a phone case wants to be made of, and
it is a poor fit for a Bowden multi-material path — long retractions, high
purge, jams. The `tpu-95a` profile is there so you can print the geometry in
one colour. If you want colour *and* flexibility, that is a printer problem
this generator cannot solve.

### The tool change macros

`T0`..`Tn` is what Marlin, RepRap, Klipper and Prusa firmware act on. The
Bambu profiles wrap it in the `M620`/`M621` AMS pair their own output uses.
These are the one part of the generator that could not be verified from the
environment it was written in. **Put a two-layer test through your machine
before committing to a print.** If your machine wants something else, set
`tool_change` on the printer profile rather than editing the writer.

---

## How the geometry works

A case is a thin shell with holes punched through it, and the holes are the
hard part. The obvious way to build the perimeters — take the outline, offset
it inwards a few times, then cut out the bits that fall inside a hole —
leaves every loop severed at the hole edge, with the cut ends of four lines
staring out of it. That is not what a hole in a case looks like. The
perimeters are supposed to *turn* and run around the opening.

So the section is not drawn, it is **solved**. Each cross-section is a signed
distance function:

```
d(x, y) = max( outer, -cavity, -hole_0, -hole_1, ... )
```

negative inside the plastic, and every perimeter is an isocontour of it: loop
`i` is the set of points at `d = -(i + 0.5) * width`. Offsetting, routing
around holes, merging two perimeters where the wall narrows between a button
and the rim and splitting them again on the next layer — none of it is
special-cased, because the distance field already knows.

Three things fall out of that for free:

- **The wall is always filled exactly.** A contour at a given depth comes back
  as two loops, one measured in from each face, so the count that matters is
  loops *per side*: `wall_pairs = round((wall/2) / line_width)` and the
  spacing is `(wall/2) / wall_pairs`. Whatever wall thickness you ask for is
  spanned with no void up the middle and no over-packed wall that bows out.
- **`--test-fit`'s rim follows the holes.** `d` is the distance to *any*
  surface, so filling the band `-7 <= d <= level` puts a rim around the camera
  opening as well as around the outline, without knowing the camera exists.
- **The skirt is the same contour at a positive level.** Outside the part is
  just the other side of the same field.

The cost is a grid, so the field is cached per distinct section rather than
per layer, clamped to ±band so that runs of clamped cells can be skipped
wholesale, and traced with marching squares chained by grid-edge identity
rather than by comparing floating-point endpoints. `--res` sets the pitch;
0.3 mm is invisible under a 0.42 mm line, and 0.6 halves the runtime.

---

## Layout

```
case.py                        CLI
phonecase/spec.py              phones, cases, cutouts, check_case
phonecase/shapes.py            the little slicer: SDF, marching squares, infill
phonecase/toolpath.py          layers, perimeters, colour assignment, ordering
phonecase/svgart.py            SVG -> filled polygons (stdlib only)
phonecase/paint.py             palette, rasteriser, splitting a path by colour
phonecase/gcode.py             multi-tool writer and the purge tower
phonecase/solid.py             the case as a mesh, and a binary STL
phonecase/threemf.py           the case split by filament, as a 3MF
phonecase/preview.py           SVG preview: back, plan, edges
phonecase/profiles.py          printers, filaments, palettes, case presets
tests/test_case.py             207 tests
```

The lamp's `weave/` package and this one share no code on purpose. They are
two generators that happen to live in one repository; coupling them would
mean every change to a printer profile had to be right for both.

```bash
python -m pytest tests -q
```
