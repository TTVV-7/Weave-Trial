# Santa down the chimney: a 600 × 600 mm LED neon sign

![lit](example/preview.png)

A neon-style sign made from an ordinary 10 mm WS2812B LED strip in 3D-printed
channels, stuck open side first to the inside of a frosted glass door, which
diffuses the light. Santa waves, sinks until
only his hat shows, vanishes down the chimney, the fire flares, and he climbs
back out. 177 LEDs, about 2.7 m of strip with LEDs 15 mm apart.

```bash
pip install manifold3d pillow numpy
python neonsign/make_neon_sign.py              # writes neonsign/example/
python neonsign/make_neon_sign.py --check-only # just the bend and spacing checks
```

Open `example/preview.html` to watch the animation and read the full build
sheet: the still frames, the chassis front and back to scale, a cross-section,
parts to print and buy, the LED map and the build order.

## What's in `example/`

| file | what |
|---|---|
| `channels_plate_1…7.3mf` | everything that holds LEDs: the line channels, the moon, the star and dot boxes, each with a flange for taping to the glass. White PLA, open side up, no supports |
| `back_parts.3mf` | the controller cover |
| `template.svg`, `template_a4.pdf` | the layout at 1:1, drawn from inside (mirrored): where every part sticks |
| `neon_layout.h` | LED index of every run (also copied into `firmware/santa_neon/`) |
| `board_preview.png` | the board with the lights off |

## How it is built

* **Glass:** every part sticks open side first to the inside of a frosted
  door, which does the diffusing. A flat 8 mm flange round the open side,
  flush with it, takes clear double-sided mounting tape. Underneath it is a
  hollow 45° skirt, so the parts print open side up without supports. Where
  parts sit close, their flanges are trimmed to share the gap.
* **Lines:** a flat strip can't bend sideways while it lies flat, so it stands
  on its edge against one wall of a 12 mm channel, LEDs facing across. Light
  bounces off the white wall opposite and out into the glass, as a band about
  15 mm wide.
* **Shapes:** the stars, eyes and mittens are boxes of that shape with one LED
  cut from the strip lying in the bottom, facing the glass. The moon is a
  crescent box with strip round the inside of its outer wall.
* **Wiring:** each run's wires come out through a slot in the floor at each
  end, on the room side. The data line visits each run in turn by short hops from the controller.
  The preview's back view numbers every stop, and that order is the LED map.
  Feed 5 V and GND to every run from a bus.
* **Low voltage:** everything on the board is 5 V DC. The only mains part is a
  sealed plug-in 5 V adapter, with a 10 A fuse where the 5 V comes in.
* **Controller:** ESP32 + 74AHCT125 level shifter, 5 V 10 A supply. The
  firmware caps the current at 6 A.

## Changing it

`--mount board` builds the earlier version instead: parts with screw tabs on a
600 mm board, under printed translucent caps, with wall standoffs. `--caps`
adds the caps on glass too, and `--flange-w` sets the flange width.

The drawing is `artwork()` in `make_neon_sign.py`: strokes in board millimetres
(y down). Every stroke is checked against `--min-bend` (default 20 mm), and every
part for clearance from every other. Nothing is written if a check fails, and the
output tells you which parts are too tight or too close. `--bed` sets your
printer's bed size. `--strip-w`, `--strip-t` and `--pitch` describe your strip,
and `--inner-w`, `--depth` and `--fit` set the channel and cap.
