# Pacific Northwest tree magnets (3D print files)

Six stylized trees generated with hi3D (`*.png` source image → `*.glb` textured model),
turned into printable STLs with a magnet pocket in the base by `make_magnets.py`.

![side and bottom views](magnet-preview.png)

| File | Size W × D × H (mm) | Wall around pocket | Base thickened (mm) |
|---|---|---|---|
| `stl/douglas-fir-magnet.stl` | 39 × 41 × 75 | 5.3 mm | — |
| `stl/western-red-cedar-magnet.stl` | 64 × 47 × 76 | 12.9 mm | 1 |
| `stl/sitka-spruce-magnet.stl` | 27 × 27 × 75 | 6.4 mm | — |
| `stl/western-hemlock-magnet.stl` | 47 × 29 × 77 | 4.0 mm | 2 |
| `stl/pacific-madrone-magnet.stl` | 65 × 42 × 75 | 6.7 mm | — |
| `stl/bigleaf-maple-magnet.stl` | 74 × 45 × 75 | 11.7 mm | — |

**Magnet:** 10 × 3 mm neodymium disc. The pocket is 10.3 mm wide and 3.2 mm deep, with at
least 1.2 mm of solid plastic above it, so it never breaks through between the roots. Press the
magnet in or add a drop of CA glue; check the polarity is the same on every tree if they'll sit
side by side.

The cedar and hemlock have thin base discs, so their bottoms were extended straight down
(1 and 2 mm) to fit the pocket. Every bottom is shaved flat.

Print base down. The overhanging branches need supports (tree supports work best). Use
0.12 mm layers for the needle detail, and 15% infill is plenty. They're single-colour STLs; the
`.glb` files keep the full colour textures if you want to paint to match.

To change the size or the magnet, edit the constants at the top of `make_magnets.py` and run
`python3 make_magnets.py` (needs `pip install trimesh manifold3d shapely fast-simplification`).
