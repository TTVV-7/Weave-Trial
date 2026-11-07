# Strawberry, cloud & raindrops

Mock-ups for a customer quote: a hollow strawberry (~9" tall, 7.5" wide) with a
leafy top, a fluffy cloud (~11.4" wide), and 2.6" raindrops, all in PLA.

```
python3 make_shapes.py        # stl/*.stl + shapes.glb (numpy, trimesh, shapely, manifold3d)
node render.cjs               # mockups/*.png (Playwright; serves render.html locally)
python3 split.py              # stl/print/*.stl: hollow halves + coupler rings, ready to slice
python3 sheet.py              # mockups/mockup-sheet.png and how-it-splits.png
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

## Printing hollow: split in two (`split.py`)

See `mockups/how-it-splits.png`. The files in `stl/print/` are already hollow and
turned so the cut face sits on the bed:

| Plate | Files | Filament |
|---|---|---|
| Berry bottom (tip up) | `strawberry-body-bottom`, `strawberry-seeds-bottom` | ~142 g red, 8 g yellow |
| Berry top (leaves up) | `strawberry-body-top`, `strawberry-seeds-top`, `strawberry-leaves-top` | ~118 g red, 3 g yellow, 46 g green |
| Berry ring | `strawberry-ring` | 16 g red |
| Cloud front / back (turned 45°) | `cloud-front`, `cloud-back` | ~139 g white each |
| Cloud ring | `cloud-ring` | 19 g white |

- Strawberry: 2 mm shell, cut level at the widest point (118 mm up). Cloud:
  2.5 mm shell, cut front-to-back.
- Load a berry half's files together in Snapmaker Orca, answer **yes** to "load
  as a single object with multiple parts", and give each part its toolhead.
- Slice with **100 % infill** (the shell is the part) or 5 walls. Use **tree supports**
  only for the inside of each dome: they come out through the open cut. The
  outside needs no supports.
- Glue the coupler ring 6 mm into one half, then press the other half over it
  (0.2 mm clearance; CA glue or 2-part epoxy).
- The seeds on the berry halves still mean a toolchange or two on most layers.
