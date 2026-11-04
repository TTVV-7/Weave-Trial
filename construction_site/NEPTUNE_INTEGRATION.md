# Plan: the construction models in the Neptune Terminals twin

How the Construction Site packs (1–4, 52 models) become things you can place in the Neptune
Terminals digital twin ([TTVV-7/Neptune-digital-twin](https://github.com/TTVV-7/Neptune-digital-twin)),
and the three decisions that are yours to make first. The twin was surveyed read-only at commit
`a264638`; nothing in it has been changed.

**In short:** 39 of the 52 models go in. 35 are new library items and 4 replace weaker existing ones.
The other 13 are left out because the twin already has a good, lighter equivalent. Each model is
slimmed for the web on the way in. The 26 from packs 1–3 go from 41 MB to **9 MB**, and from about
4,000 draw calls to one or two each. They land as ordinary entries in the twin's own library format,
so placing, rotating, Rows, the Show panel, saving, sharing and undo all work with **no app code
changes**.

## The three decisions

**1. Public files: the twin repository and site are public.** Anything under `public/library/` can be
downloaded by anyone. Your Cults3D packs sell the print files (STL and painted 3MF) and include the
GLBs in their CAD zip. Pick one:

| Option | What it means |
|---|---|
| **A. Ship the slimmed GLBs publicly** (recommended) | The twin gets display models: compressed, merged into one or two meshes each, part names gone. These are not what buyers pay for. They aren't print-ready (parts overlap rather than union, nothing is thickened) and they aren't editable like the STEP files. This is how the twin's other models are shipped. |
| B. A, but simplified further | Adds `--simplify 0.5` to the slimming, so the public copies are coarser. There's less to take, but they look slightly less crisp in the twin. |
| C. Mark them Pro | The twin's Pro gate (`premium: true`) only stops *placing* them in the app. The files stay public (`src/premium.js:11`). It's a business choice, not protection. |
| D. Private storage | Serve them from storage behind sign-in instead of `public/`. This needs app changes (the loader assumes `library/<file>`) and is out of scope for this plan. |

You also need to set `license` in `construction_site/neptune/manifest.json`, for example "Own work,
used with permission". The twin's library policy is that only CC0 or CC-BY models from Sketchfab or
Poly Haven go in. Your own models are a third source, so the merge script also updates the heading of
`CREDITS.md`.

**2. Replace or add.** Four models replace twin items by reusing their ids. Every saved layout that
uses those items then shows the new model, and the twin's `resolve()` migrates them automatically.

| Twin id | Today | Becomes | Why |
|---|---|---|---|
| `telehandler-10k` | a rigged GLB with SkyTrak lettering (a known trademark issue in `docs/equipment.md`) | Pack 1 telehandler | unbranded; keeps the Pro flag and drive tuning |
| `crawler-dozer-d6` | a battered, rusty scan, 2.9 MB | Pack 3 dozer, 0.6 MB | clean and the same class |
| `backhoe-loader` | a GLB with brand marks | Pack 3 backhoe | unbranded |
| `concrete-mixer-truck` | a 1950s-style truck | Pack 3 mixer, 0.9 MB | current truck |

Change any of these to `"action": "add"` with a new id if you'd rather keep both versions.

**3. Which models.** The recommended set is below. Every row is an editable line in the manifest.

## What goes in

| Pack | Model | Twin id | Category | Action |
|---|---|---|---|---|
| 1 | Concrete line pump (trailer) | `concrete-line-pump-trailer` | Heavy equipment | add |
| 1 | Air compressor (750 CFM class) | `compressor-750cfm` | Power & air | add |
| 1 | Roll-off dumpster 20 yd (detailed) | `rolloff-20-detailed` | Waste | add |
| 1 | Pallet of concrete bags | `pallet-concrete-bags` | Materials | add |
| 1 | Planetary concrete mixer on stand | `planetary-mixer-on-stand` | Heavy equipment | add |
| 1 | Telehandler 10,000 lb | `telehandler-10k` | Material handling | **replace** |
| 1 | Industrial steel stair (12 ft) | `steel-stair-12ft` | Access & scaffolding | add |
| 1 | Rail crossover gantry | `rail-crossover-gantry` | Access & scaffolding | add |
| 2 | Shipping container 20 ft (detailed) | `container-20-iso` | Site trailers & containers | add |
| 2 | LED light tower | `light-tower-led` | Power & air | add |
| 2 | Frame scaffold tower | `scaffold-tower-frame` | Access & scaffolding | add |
| 2 | Type III barricade, ROAD CLOSED | `barricade-type-3-road-closed` | Traffic control | add |
| 2 | Pallet of concrete blocks | `pallet-cmu-blocks` | Materials | add |
| 2 | Steel beam bundle | `steel-beam-bundle-w12` | Materials | add |
| 2 | Contractor wheelbarrow | `wheelbarrow` | Site services | add |
| 2 | Cable reel | `cable-reel` | Power & air | add |
| 3 | Articulated dump truck (30 t) | `articulated-dump-truck-30t` | Heavy equipment | add |
| 3 | Crawler dozer (20 t class) | `crawler-dozer-d6` | Heavy equipment | **replace** |
| 3 | Backhoe loader | `backhoe-loader` | Heavy equipment | **replace** |
| 3 | Vibratory roller, single drum 84 in | `roller-single-drum-84in` | Heavy equipment | add |
| 3 | Concrete mixer truck | `concrete-mixer-truck` | Heavy equipment | **replace** |
| 3 | Scissor lift 26 ft (raised) | `scissor-lift-26ft-raised` | Cranes & lifts | add |
| 3 | Arrow board trailer | `arrow-board-trailer` | Traffic control | add |
| 3 | Trench shield (laydown) | `trench-shield-8x20-laydown` | Shoring | add |
| 3 | Concrete pipe stack | `rcp-pipe-stack-24in` | Materials | add |
| 3 | Water-filled barrier 6 ft | `water-barrier-6ft` | Barriers & fencing | add |
| 4 | Water truck, dust control | `water-truck-4000gal` | Heavy equipment | add |
| 4 | Hydrovac truck | `hydrovac-truck` | Heavy equipment | add |
| 4 | Concrete boom pump 38 m | `concrete-boom-pump-38m` | Heavy equipment | add |
| 4 | Fuel and lube truck | `fuel-lube-truck` | Site services | add |
| 4 | Vacuum road sweeper | `road-sweeper` | Site services | add |
| 4 | Vibratory pile hammer + power pack | `vibratory-pile-hammer` | Shoring | add |
| 4 | Steel pipe pile stack | `pipe-pile-stack-36in` | Shoring | add |
| 4 | Radial stacking conveyor | `radial-stacker-100ft` | Material handling | add |
| 4 | Conveyor gallery module (12 m) | `conveyor-gallery-12m` | Material handling | add (Rows every 12 m) |
| 4 | Coal rail car | `rail-gondola-coal` | Vehicles | add |
| 4 | Railcar mover | `railcar-mover` | Vehicles | add |
| 4 | Dust fog cannon | `dust-fog-cannon` | Site services | add |
| 4 | Drive-through wheel wash | `wheel-wash` | Site services | add |

**Left out (13).** The twin's version is as good or better here, usually much lighter for Rows of
hundreds:

- traffic cone and traffic drum
- fence panel and fence run
- jersey barrier and barrier run
- mini excavator (never the digging one), skid steer, portable toilet, wheel loader and site office (optional swaps)
- the 500 L mixer and mixer stand on their own (the combined one goes in)

Pack 4 was chosen from what the survey found missing from both the twin and packs 1–3, for a rail-fed
coal and potash terminal with berth, conveyor and foundation works.

## How it works

Three tools in this repo do it, and none of them touches the twin until you run the last step:

1. **`construction_site/neptune/manifest.json`**: which model becomes which id, in which category,
   added, replacing or skipped.
2. **`python construction_site/export_neptune.py --neptune <twin checkout>`** stages everything under
   `construction_site/neptune/out/`:
   - `public/library/<id>.glb`: slimmed by `neptune/optimize.mjs`. It runs the same steps as the
     twin's own `scripts/add-asset.mjs` (dedup, prune, weld, meshopt), plus palette, flatten and join.
     Each model's flat colours go into a tiny palette texture, so all its parts merge into one mesh.
     Only glass and lamps stay separate.
   - `public/library/thumbs/<id>.webp`: a 256 px card, rendered fresh from the model so every card
     matches.
   - `library-entries.json`: entries in the twin's exact schema, with `front: "+x"`, `scale: 1`,
     dimensions measured from the slimmed model, and a full `source` credit.
   - `REPORT.md`: sizes, triangles and draw calls, plus any problems.

   It checks against the twin as well: an id to add must be free, an id to replace must exist, every
   category must be in the sidebar's `CATEGORY_ORDER`, and every base must be on the ground.
3. **`node construction_site/neptune/merge-into-twin.mjs <twin checkout>`** copies the files in and
   merges the entries exactly the way `add-asset.mjs` does: `{ ...earlier, ...new }`, so replaced
   items keep their drive tuning and Pro flag. It uses the same sort, and rewrites `CREDITS.md` in the
   same format.

Plus **`construction_site/neptune/test-library.mjs`**, a new test for the twin's `scripts/` folder.
Nothing there checks downloaded models today. This test checks that every library entry has its GLB
and thumbnail, a unique id (including against the items built in code), a known category, a valid
facing, a full credit, an up-to-date `sizeKB`, and that the model's measured size matches its card
within 5%. It skips rigged models, which are measured in their bind pose.

**Why the models fit as they are.** Our GLBs are already in the twin's frame: metres, Y up, ground at
y = 0, footprint centred, front along +X, which is `front: "+x"`, as 10 existing entries use. The twin
draws a Row as one instanced mesh per mesh in the model. Unmerged, a row of backhoes would cost 153
draw calls per row; merged, it costs one or two.

**Measured on packs 1–3:**

| | Size | Draw calls |
|---|---|---|
| As built | 41.2 MB | ~4,000 |
| Slimmed for the twin | **9.0 MB** | 1–2 per model |

The twin's library is 35 MB today. All 39 models would add about 12–14 MB once Pack 4 is in.

## Rollout

1. Settle decisions 1–3 and edit the manifest. Then rerun the exporter and read `REPORT.md`.
2. In the twin, create a feature branch. **Never use `claude/kind-ride-ovicsk`**: a push there deploys
   to production through Cloudflare Workers Builds.
3. Run `merge-into-twin.mjs`, add `scripts/test-library.mjs` and a `test:library` script to
   `package.json`, then commit, using the twin's commit style ("Library: …").
4. Test:
   - `node --test scripts/test-library.mjs`
   - the four library-related UI suites: `npm run test:rows-ui`, `test:site-items-ui`, `test:plant-ui`
     and `test:premium-ui`
   - by hand in `npm run dev`: press **L**, place each new model, and check its facing, size, ground
     contact, a Row of it, and the replaced models in an old saved layout
5. Open a pull request, review it in the preview deploy, then merge.

**Follow-ups for later, not needed to start:**

- `drive` tuning so the trucks can be driven. Category "Vehicles" already does this for the rail car
  and railcar mover; move those two to "Material handling" if that isn't wanted.
- A `BEDS` entry (`src/excavator.js`) so the excavator can load the 30 t dump truck.
- A "Rail" category for the rail car and railcar mover.

## Risks

- **Ids are permanent once layouts are saved with them.** Settle the manifest before anyone uses the
  new items.
- **The Pro test.** Marking a new item `premium: true` breaks `scripts/test-premium-ui.mjs` until its
  hard-coded `PACK` list is updated. The telehandler keeps its id and its existing flag, so it's
  unaffected.
- **Repository growth.** The twin stores models directly in git, with no LFS. About 13 MB is fine,
  but every later re-export adds its full size to the history again, so re-export rarely.
- **Metal parts may look dark.** The twin has no environment map. Check the silver parts in the app;
  the slimmed models keep their metalness and could be dulled if needed.
