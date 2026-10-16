# Google review stand: QR + NFC

![example](example/preview.png)

A two-piece table sign: a flat plate with your logo, business name, stars and a
real QR code generated from your review link, and a base it slots into at a
12° lean. An NFC tag sits behind the "tap" icon so phones can tap instead of
scanning.

```bash
pip install manifold3d qrcode fonttools pillow
python reviewstand/make_review_stand.py \
    --name "Bella's Bakery" \
    --url "https://g.page/r/YOUR-PLACE-ID/review" \
    --logo my_logo.svg
```

Output goes in `reviewstand/<name>/`: `sign.3mf` (multi-colour), `base.3mf`,
`base.stl`, `preview.png`.

**Your review link:** Google Business Profile → *Ask for reviews* (or *Get more
reviews*) → copy the link. Short links give a coarser QR code, which prints
sharper.

## Printing

* **Sign:** face up, no supports. With an AMS every colour comes out in one
  print. Without one, all the artwork sits above 4.0 mm, so it is one filament
  change at that height. `--flush` sets the artwork into the face instead of
  raising it (that needs an AMS).
* **Base:** as it lies, no supports.
* **Logo:** an SVG. Each fill colour is matched to the nearest filament, or
  gets its own while you have AMS slots left (`--max-colors`, default 4).
  White parts of the logo stay the plate colour. `--logo-color ink` prints the
  whole logo in one colour.

## NFC

Use a 25 mm NTAG213 or NTAG215 sticker or coin (`--tag-d 30` for 30 mm ones).
Write your review link to it with the free *NFC Tools* app.

* `--nfc back` (default): a recess in the back of the plate. Press the tag in
  after printing, with a dot of glue if it's loose.
* `--nfc hidden`: the tag is sealed inside. The script prints the height to
  pause at so you can drop it in.
* `--nfc none`: no tag, and the icon is dropped.

## Other options

`--header`, `--cta` (the line by the tap icon), `--no-stars`, `--body`,
`--ink` and `--accent` colours, `--border 0` (no frame), `--width`,
`--qr-size`, `--tilt`. Run with `--help` for everything.
