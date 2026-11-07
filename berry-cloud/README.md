# Strawberry, cloud & raindrops

Mock-ups for a customer quote: a hollow strawberry (~9" tall, 7.5" wide) with a
leafy top, a fluffy cloud (~11.4" wide), and 2.6" raindrops, all in PLA.

```
python3 make_shapes.py        # stl/*.stl + shapes.glb (numpy, trimesh, shapely, manifold3d)
node render.cjs               # mockups/*.png (Playwright; serves render.html locally)
python3 sheet.py              # mockups/mockup-sheet.png
```

The models are closed solids. Print them hollow with 0 % infill and 3 walls
(vase mode works for the raindrops). The strawberry leaves are a separate green
part that glues on. The cloud is wider than a 256 mm bed: split it front/back
in the slicer and glue the halves.
