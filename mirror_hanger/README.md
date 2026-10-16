# Renolux mirror hanger

A three-colour rearview-mirror hanger made from `logo.jpg`. It's built for a
multi-material FDM printer such as the Snapmaker U1 with a 0.4 mm nozzle.

```bash
pip install -r mirror_hanger/requirements.txt
python3 mirror_hanger/segment.py mirror_hanger/logo.jpg --out mirror_hanger/segmentation.png   # check colours
python3 mirror_hanger/make_hanger.py                                                         # build the model
```

Outputs land in `out/`. All of them share one coordinate system in mm, with
the plate's bottom-left corner at the origin:

| file | what |
|---|---|
| `black_base.stl` | 3.0 mm plate, rounded corners, tab with a 4 mm hole |
| `white_layer.stl` | white artwork, z 3.0 to 3.8 |
| `red_layer.stl` | red artwork, z 3.0 to 3.8 |
| `hanger.3mf` | one object with three coloured parts, assigned to extruders 1/2/3 (black/white/red) |
| `preview.png` | the original, the model seen from above, and a map of what was thickened |

Every dimension is a variable at the top of `make_hanger.py`: width, margin,
thicknesses, hole size and wall, minimum feature width, and so on.

## How thin features are handled

Anything white or red narrower than `MIN_FEATURE` (0.8 mm) is thickened
*locally*. Each stroke's centreline is found, and a 0.8 mm disc is drawn along
the parts that are too thin. As a result:

* a 0.56 mm CONTRACTING stroke grows by 0.12 mm on each side;
* a tapered building stripe stays tapered down to 0.8 mm and ends in a round tip;
* parts that are already thick don't change, so the gaps between stripes
  stay open.

Offsetting each shape uniformly doesn't work for this logo. The stripes taper
to points, so every stripe would need the full 0.4 mm offset, and almost
every black gap in the building would close.

The script prints a warning listing what it thickened. Black gaps narrower than
`MIN_GAP` get filled, and slivers left over from the colour split are removed.

## Printing

Import `hanger.3mf`. It opens as one object with its parts already assigned
to extruders 1/2/3 (black/white/red). If you'd rather use the STLs, import all
three at once and answer "yes" when the slicer asks whether to treat them as a
single object with multiple parts. Print flat with the artwork facing up.
