# Listings: from a model in this repo to a post on Cults3D

Three steps, and nothing is posted until you say so.

```bash
python listings/make_scale_models.py          # 1. full-size CAD -> printable, painted 1:50 models
python listings/make_listing.py               # 2. pictures, zip, listing.json  -> review it
python listings/cults_upload.py listings/construction-site-1-50 --base-url <where the files are online>
                                              # 3. dry run; add --publish to really post
```

Needs `pip install trimesh manifold3d rtree networkx scipy matplotlib pillow`,
and `cadquery` for the crane and bulk bag.

## The first pack: construction site, 1:50

`construction-site-1-50/` is fourteen site models made printable at 1:50, the
scale of diecast construction equipment (a telehandler is 175 mm long): twelve
from `construction_site/`, the carry deck crane from `crane_model/` (without
its owner's name and fleet number) and the bulk bag from `bulkbag/`.

Two models are changed from their sources. The air compressor's front side
doors stuck 250 mm past the end of its canopy, so all three pairs are re-spaced
to fit (`fix_compressor_doors`). The fence panel is built fresh
(`fence_panel`) as the welded-mesh panel most sites use, because the source's
chain-link mesh prints as a diagonal grid at this scale. Its wires are 0.5 mm,
which a 0.4 mm nozzle prints as single lines, so turn on thin-wall detection
in the slicer.

| What | Where |
|---|---|
| plain STL per model, one solid each | `files/*_1-50.stl` |
| painted 3MF per model, up to four filaments | `files/*_1-50.3mf` |
| everything zipped with a print guide (the file buyers get) | `construction-site-1-50.zip` |
| cover plus one picture per model | `images/` |
| title, description, price, tags | `listing.json` |
| size, filaments and printability of each model | `report.json` |

The models are drawn at real size, so a fence wire is 4 mm across and would be
0.08 mm at 1:50. `make_scale_models.py` stretches every piece thinner than
0.8 mm up to 0.8 mm where it stands, which is what model makers do by hand. It
also fills the small gaps where a part was drawn a few centimetres clear of
what holds it up, because on a printer that part would be printed in mid-air.
Then it measures the result: `report.json` gives each model's loose-piece
count (all 1) and how much of its surface is still under 0.8 mm thick.

**Colour.** Each part's colour in the `.glb` is matched to the nearest of
eleven stock PLA colours (`FILAMENTS`), and each model keeps its four most-used.
The 3MFs use the same per-triangle painting as `pnw-tree-magnets/`, so they
open painted in Bambu Studio, OrcaSlicer and Snapmaker Orca.

## Before you post

- **Print one.** The pictures are renders. Listings with photos of a real print
  sell far better, and a print is the only real test of the thickening.
- **`made_with_ai` is `true`.** These were designed by an AI writing CAD code.
  Cults asks this of every design. The answer is yours to give, but `true` is
  the accurate one.
- **Category.** `python listings/cults_upload.py --categories` lists Cults'
  category ids. Put one in `listing.json` as `category_id`.
- **Price** is $9 for the fourteen. Edit `listing.json`. A rebuild keeps your
  text and only refreshes the file and image lists.

## Posting to Cults

Cults has a GraphQL API (`https://cults3d.com/graphql`). Make a key at
<https://cults3d.com/en/api/keys>, then:

```bash
export CULTS_USERNAME=you CULTS_API_KEY=...
```

Cults does not accept uploads through the API. It downloads each file from a
public HTTPS link that ends in the file name, at most ten files and ten images
per listing. So put the listing folder online first: a public GitHub release,
any web host, or direct-download Google Drive links. Then pass that address as
`--base-url`. The dry run checks that every link answers before `--publish`
sends anything.

Community notes put the API's limit at roughly 500 requests a day.
`cults_upload.py` makes one request per listing.
