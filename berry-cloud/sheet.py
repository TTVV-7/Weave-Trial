"""Labelled sheets from the renders in mockups/:
mockup-sheet.png  what the pieces look like
how-it-splits.png how the strawberry and cloud come apart to print hollow
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
M = Path(__file__).parent / "mockups"
BG, INK, SOFT = (243, 239, 233), (40, 40, 40), (95, 95, 95)


def font(sz, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", sz)
    except OSError:
        return ImageFont.load_default()


def wrap(d, text, f, width):
    """Split text into lines that fit `width` pixels."""
    lines, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if d.textlength(trial, font=f) <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    return lines + [line]


def caption(d, x, y, width, title, body, size=20):
    d.text((x, y), title, font=font(28, True), fill=INK)
    y += 40
    for ln in wrap(d, body, font(size), width):
        d.text((x, y), ln, font=font(size), fill=SOFT)
        y += size + 8
    return y


def crop(name, box):
    return Image.open(M / f"{name}.png").convert("RGB").crop(box)


def tiles(out, d, y, items, th, cols=None, x0=60, size=20):
    cols = cols or len(items)
    tw = (out.width - 2 * x0) // cols
    bottom = y
    for i, (title, body, im) in enumerate(items):
        im = im.copy()
        im.thumbnail((tw - 30, th))
        x = x0 + (i % cols) * tw
        yy = y + (i // cols) * (th + 190)
        out.paste(im, (x + (tw - im.width) // 2, yy))
        bottom = max(bottom, caption(d, x + 10, yy + th + 10, tw - 40, title, body, size))
    return bottom


def mockup_sheet():
    W = 1600
    group = crop("group", (200, 220, 1420, 800))
    items = [
        ("Strawberry", "8.8\" tall × 7.5\" wide. Red, with yellow seeds and green leaves.",
         crop("berry", (450, 150, 1150, 830))),
        ("Cloud", "11.4\" wide × 5.4\" tall × 4.8\" deep. White.", crop("cloud", (250, 200, 1350, 820))),
        ("Raindrop", "2.6\" long × 1.6\" wide. Blue.", crop("drop", (450, 120, 1150, 900))),
    ]
    out = Image.new("RGB", (W, 1400), BG)
    d = ImageDraw.Draw(out)
    d.text((60, 40), "Strawberry, cloud & raindrops: design mock-ups", font=font(40, True), fill=INK)
    out.paste(group, ((W - group.width) // 2, 110))
    bottom = tiles(out, d, 110 + group.height + 40, items, 420)
    out.crop((0, 0, W, bottom + 50)).save(M / "mockup-sheet.png")


def split_sheet():
    W = 1600
    out = Image.new("RGB", (W, 2600), BG)
    d = ImageDraw.Draw(out)
    d.text((60, 40), "Printing hollow: each piece splits in two", font=font(40, True), fill=INK)
    y = caption(d, 60, 100, W - 120, "",
                "Each half prints with its cut face flat on the bed, so the outside needs no supports. "
                "Any supports inside the dome pull out through the open cut. A thin coupler ring "
                "glues 6 mm into each half to line them up and hide the joint.", 22)
    top = [
        ("Strawberry: cut level at its widest point",
         "2 mm shell. The bottom half, the ring and the top half with its leaves. "
         "The seam sits on the widest line, where it is least visible.",
         crop("splitberry", (330, 60, 1270, 960))),
        ("Cloud: cut front-to-back down the middle",
         "2.5 mm shell. Back half, ring and front half. The seam runs around the edge "
         "of the cloud, where the puffs meet.",
         crop("splitcloud", (200, 120, 1400, 960))),
    ]
    y = tiles(out, d, y + 30, top, 560)
    d.text((60, y + 40), "On the U1 bed (270 × 270 mm), cut face down", font=font(32, True), fill=INK)
    plates = [
        ("Berry bottom", "Tip up. Red + yellow. ~150 g.", crop("plateberrybottom", (300, 120, 1300, 900))),
        ("Berry top", "Leaves up. Red + yellow + green. ~170 g.", crop("plateberrytop", (300, 120, 1300, 900))),
        ("Cloud front", "Turned 45° to fit. ~140 g.", crop("platecloudfront", (300, 120, 1300, 900))),
        ("Cloud back", "Turned 45° to fit. ~140 g.", crop("platecloudback", (300, 120, 1300, 900))),
    ]
    y = tiles(out, d, y + 100, plates, 300, size=18)
    out.crop((0, 0, W, y + 50)).save(M / "how-it-splits.png")


if __name__ == "__main__":
    mockup_sheet()
    split_sheet()
