# Strawberry, cloud & raindrops

Mock-ups for a customer quote: a hollow strawberry (~9" tall, 7.5" wide) with a
leafy top, a fluffy cloud (~11.4" wide), and 2.6" raindrops, all in PLA.

```
python3 make_shapes.py        # stl/*.stl + shapes.glb (numpy, trimesh, shapely, manifold3d)
node render.cjs               # mockups/*.png (Playwright; serves render.html locally)
python3 sheet.py              # mockups/mockup-sheet.png
```

The models are closed solids. Print them hollow with 3 walls and no real
infill (vase mode works for the raindrops).

## Strawberry on the Snapmaker U1 (one print, three colours)

`strawberry.py` builds three parts that fit together without overlapping:

| File | Toolhead | What |
|---|---|---|
| `stl/strawberry-body.stl` | 1 · red PLA | lumpy berry body with ~360 seed pits, flat 26 mm foot |
| `stl/strawberry-seeds.stl` | 2 · yellow PLA | ~360 seeds lying in the pits |
| `stl/strawberry-leaves.stl` | 3 · green PLA | two rings of serrated leaves with midribs, bent stem |

Import all three STLs at once in Snapmaker Orca and answer **yes** to "load as a
single object with multiple parts", then give each part its toolhead.
Total height is 223 mm (fits the U1's 270 mm), and the parts use about 190 g
red, 45 g green and 12 g yellow.

Slicer settings:
- 3 walls, 4 top layers, and **lightning infill at about 10 %**. It only holds up
  the top shoulders, so the berry stays hollow and light. With 0 % infill the
  top will sag.
- **Tree supports, build plate only**, for the bottom ~22 mm where the berry
  curves out from the tip. Add a 5 mm brim, because the foot is small for a part this tall.
- Seeds sit on every layer from 10 mm to 150 mm, so expect a toolchange or two
  per layer through that band. That's a few extra hours over a single-colour print.

Sizes, seed spacing (`SEED_GAP`), leaf count and lumpiness are constants and
functions at the top of `strawberry.py`. The cloud is wider than a 256 mm bed: split it front/back
in the slicer and glue the halves.
