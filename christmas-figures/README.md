# Christmas figures (3D print files)

Six Christmas figures generated with hi3D from clay-style pictures (`*.png` →
`*.glb`), each made printable three ways by `make_figures.py`:

| Files in `stl/` | What |
|---|---|
| `<name>.stl` / `.3mf` | standing figurine, 70 mm tall |
| `<name>-ornament.stl` / `.3mf` | the same with a hanging loop on top (3 mm hole, 1.8 mm wire) |
| `<name>-half.stl` / `.3mf` + `<name>-lids.stl` | fridge magnet: the front half, flat back, hidden magnet pockets with glue-in lids |

The figures are Santa, a snowman, a reindeer, a gingerbread man, a nutcracker
and a penguin. The cutting, pockets, lids and painting are
`../pnw-tree-magnets/make_magnets.py`'s; this folder's script adds the loop
and the filaments.

## Filaments: four per figure

Every 3MF is painted per triangle for a 4-filament printer, in the same slot
order, so five of the six figures load the same way and can share a plate:

| Slot | Five figures | Penguin |
|---|---|---|
| T1 | Red | Red |
| T2 | White | White |
| T3 | Dark green | **Black** |
| T4 | Golden brown | Golden brown |

Santa's and the nutcracker's faces print white, the nearest of the four to
skin; the sculpted nose and cheeks still read. The penguin's texture is black
where the trees' was only shadowed, so its shadow filter is set lower
(`shadow_l`) to keep the body.

## The loop

The ornament's ring sits on the highest surface near the figure's centre line
(so it hangs straight), sunk 1.5 mm in, its plane facing the front so a hook
goes through it front to back. If the union leaves the ring loose, the script
sinks it 1 mm deeper and tries again.

## Rebuilding

```bash
python3 make_figures.py              # all six
python3 make_figures.py santa        # one
```

Needs `trimesh manifold3d shapely scipy fast-simplification`. Then
`python3 ../listings/make_christmas_listing.py` for the pictures, zip and
`listing.json`.
