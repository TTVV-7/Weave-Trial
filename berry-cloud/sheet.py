"""Combine the renders in mockups/ into one labelled sheet for the customer."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
M = Path(__file__).parent / "mockups"
def font(sz, bold=False):
    for f in (["DejaVuSans-Bold.ttf"] if bold else ["DejaVuSans.ttf"]):
        try: return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{f}", sz)
        except OSError: pass
    return ImageFont.load_default()
def crop(name, box):
    im = Image.open(M / f"{name}.png").convert("RGB"); return im.crop(box)
bg = (243, 239, 233)
W = 1600
group = crop("group", (200, 220, 1420, 800))
tiles = [
    ("Strawberry", "9\" tall × 7.5\" wide · red with green leafy top", crop("berry", (450, 150, 1150, 830))),
    ("Cloud", "11.4\" wide × 5.4\" tall × 4.8\" deep · white", crop("cloud", (250, 200, 1350, 820))),
    ("Raindrop", "2.6\" long × 1.6\" wide · blue", crop("drop", (450, 120, 1150, 900))),
]
th = 420
out = Image.new("RGB", (W, 120 + group.height + 60 + th + 120), bg)
d = ImageDraw.Draw(out)
d.text((60, 40), "Strawberry, cloud & raindrops — design mock-ups", font=font(40, True), fill=(40, 40, 40))
out.paste(group, ((W - group.width) // 2, 110))
y = 110 + group.height + 40
tw = (W - 120) // 3
for i, (name, sub, im) in enumerate(tiles):
    im.thumbnail((tw - 20, th))
    x = 60 + i * tw
    out.paste(im, (x + (tw - im.width) // 2, y))
    d.text((x + 10, y + th + 10), name, font=font(30, True), fill=(40, 40, 40))
    d.text((x + 10, y + th + 50), sub, font=font(20), fill=(90, 90, 90))
out.save(M / "mockup-sheet.png")
print(out.size)
