# Pacific Northwest tree magnets (3D print files)

Six stylized trees generated with hi3D (`*.png` source image → `*.glb` textured model),
turned into two-part printable STLs that hide a magnet in the base by `make_magnets.py`.

![side view, tree underside and cap](magnet-preview.png)

| Files | Assembled W × D × H (mm) | Wall around pocket | Base thickened (mm) |
|---|---|---|---|
| `stl/douglas-fir-tree.stl` + `-cap.stl` | 39 × 41 × 75 | 3.8 mm | — |
| `stl/western-red-cedar-tree.stl` + `-cap.stl` | 64 × 47 × 77 | 12.9 mm | 2 |
| `stl/sitka-spruce-tree.stl` + `-cap.stl` | 27 × 27 × 76 | 6.4 mm | 1 |
| `stl/western-hemlock-tree.stl` + `-cap.stl` | 47 × 29 × 78 | 4.0 mm | 3 |
| `stl/pacific-madrone-tree.stl` + `-cap.stl` | 65 × 42 × 75 | 11.5 mm | — |
| `stl/bigleaf-maple-tree.stl` + `-cap.stl` | 74 × 45 × 75 | 12.6 mm | — |

## How it goes together

Each base is split 1 mm above the bottom:

- **`-tree.stl`** has a 10.3 × 3.2 mm pocket for a **10 × 3 mm disc magnet** opening on its
  underside, with at least 1.2 mm of solid plastic above it, plus two pin holes.
- **`-cap.stl`** is the 1 mm slice that was cut away, with two 2 mm locating pins. The pins are
  off-centre, so the cap only fits one way round and its outline lines up with the base.

1. Drop the magnet into the pocket. If they'll sit side by side, mark which face is "out" and
   put every magnet in the same way up.
2. Glue the cap on (CA glue or two-part epoxy on the flat faces, not in the pocket), pins into
   their holes. Clamp or weigh it down until set.

The magnet ends up fully enclosed behind 1 mm of plastic, which costs a little pull. A
grade N52 magnet is recommended for the larger trees.

The cedar, spruce and hemlock bases were extended straight down (2, 1 and 3 mm) so the pocket
fits above the cap line. Every bottom is shaved flat.

## Printing

- Tree: base down. The overhanging branches need supports (tree supports work best); 0.12 mm
  layers for the needle detail, 15% infill is plenty.
- Cap: flat, pins up, no supports.

They're single-colour STLs; the `.glb` files keep the full colour textures if you want to paint
to match.

To change the size, the magnet or the cap, edit the constants at the top of `make_magnets.py`
and run `python3 make_magnets.py`, then `python3 preview.py` for the preview sheet (needs
`pip install trimesh manifold3d shapely fast-simplification matplotlib`).
