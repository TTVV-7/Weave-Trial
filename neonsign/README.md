# Santa down the chimney: a 600 × 600 mm LED neon sign

![lit](example/preview.png)

Addressable LED neon flex in 3D-printed channels on a flat black board. Santa
waves, sinks until only his hat shows, vanishes down the chimney, the fire
flares, and he climbs back out. 165 LEDs: 2.6 m of flex in 16 runs, plus 11
single pixels for the stars, eyes, mittens and pom.

```bash
pip install manifold3d pillow numpy
python neonsign/make_neon_sign.py              # writes neonsign/example/
python neonsign/make_neon_sign.py --check-only # just the bend and spacing checks
```

Open `example/preview.html` to watch the animation and read the full build
sheet: a cross-section, parts to print and buy, the LED map and the build order.

## What's in `example/`

| file | what |
|---|---|
| `channels_plate_1…5.3mf` | the channels that hold the flex, on 220 mm beds. Black, no supports |
| `pixel_caps.3mf` | translucent stars and dots for the single pixels. White/natural PETG, face down |
| `back_parts.3mf` | controller cover and four keyhole standoffs |
| `template.svg`, `template_a4.pdf` | the board at 1:1: channel positions, wire holes, pilot holes |
| `neon_layout.h` | LED index of every run (also copied into `firmware/santa_neon/`) |
| `board_preview.png` | the board with the lights off |

## How it is built

* **Board:** 600 × 600 mm, 6 mm MDF or ply, painted matte black.
* **Flex:** WS2812B 5 V, 60 LEDs/m, 6 × 12 mm, the kind that bends sideways
  for signs ("top bend"). It sits 8 mm deep in the channel with 4 mm proud.
* **Channels:** split into bed-sized pieces that butt together. Each one is
  screwed down through tabs placed clear of the neighbouring lines.
* **Wiring:** every run ends over an 8 mm hole, so the wires go through to the
  back. Wire the data line in LED-map order, and feed 5 V and GND to every run
  from a bus.
* **Controller:** ESP32 + 74AHCT125 level shifter, 5 V 10 A supply. The
  firmware caps the current at 6 A.

## Changing it

The drawing is `artwork()` in `make_neon_sign.py`: strokes in board millimetres
(y down). Every stroke is checked against `--min-bend` (default 20 mm; check your
flex's datasheet) and for clearance from every other channel. Nothing is written
if a check fails, and the output tells you which strokes are too tight or too
close. `--bed` sets your printer's bed size, and `--flex-w` and `--fit` set the
channel to your flex.
