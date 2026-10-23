# Jubilee X-logo accessories (3D print files)

| File | Item | Size (mm) | Notes |
|---|---|---|---|
| `stl/earring_x_oval.stl` / `stl/earrings_pair.stl` | Oval X earrings | 33 × 45 × 2.4 | Open cut-out X; top loop takes a jump ring + ear hook |
| `stl/necklace_pendant_x.stl` | X choker charm | 27 × 32 × 3 | Open ring + X (shirt shows through); bail for cord or jump ring |
| `stl/chest_pin_x.stl` | X pin badge | 55 × 55 × 3.5 | Open ring + X (shirt shows through); glue a pin back along one X arm (8–10 mm wide) |
| `stl/belt_buckle_x.stl` | X belt buckle | 82 × 52 × 6 | Side slots fit a 38 mm (1.5") belt |

Print flat side down, no supports. 0.12–0.16 mm layers for the small pieces; 3+ walls / high infill for the buckle.
Paint everything silver except the raised parts of the buckle.

To resize (e.g. a different belt width, or the `GROW_*` size increases), edit the constants in `make_props.py` and run `python3 make_props.py`
(needs `pip install trimesh shapely manifold3d mapbox_earcut`).
