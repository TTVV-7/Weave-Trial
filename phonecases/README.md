# iPhone 15 Pro: TPU case and TPU + PETG hybrid

```bash
pip install manifold3d
python phonecases/make_iphone15pro.py      # rebuilds everything in iphone-15-pro/
```

Built on this repo's case generator (`phonecase/`), so the body, lip and
cutouts are its shapes. The fit and the extras are tuned in the constants at
the top of `make_iphone15pro.py`.

| File | Print in | What it is |
|---|---|---|
| `tpu_case.stl` / `.3mf` | TPU 95A | One-piece case, ~22 g |
| `hybrid_tpu_frame.stl` / `.3mf` | TPU 95A | Bumper frame with a window in the back, ~13 g |
| `hybrid_petg_plate_gradient.3mf` | PETG, 2 colours (AMS) | Back plate with a line-dither gradient, ~13 g |
| `hybrid_petg_plate.stl` | PETG, 1 colour | The same plate, plain |
| `hybrid_assembly.3mf` | — | Frame and plate together, to look at only |
| `onepiece_hybrid_tpu_petg.3mf` | TPU + PETG, **one print** | Tool changer (Snapmaker U1 etc.), 2 toolheads, ~12 g TPU + ~20 g PETG |
| `onepiece_hybrid_tpu_petg_gradient.3mf` | TPU + 2 PETG, **one print** | The same with the gradient back, 3 toolheads |

## The designs

**TPU case.** A tighter fit than the PLA presets (0.15 mm gap instead of 0.35)
because TPU stretches over the phone. The lip is taller (1.5 mm) and leans in
further (1.1 mm), which TPU can do because you push it past the screen edge
and it grips. Vertical grip ribs are cut into the lower half of both long
sides, below the buttons. They run vertically so no groove is an overhang.

**Hybrid.** This is the "flexible bumper, rigid back" idea from MakerWorld. A TPU
frame has a window in its back, leaving a 5 mm ledge. A 1.2 mm PETG plate
drops in from the inside and sits on that ledge, and the phone sits on top of
the plate and holds it in. Nothing is glued, so you can print more plates and
swap them.

**The gradient plate** is colour mixing without mixing filament. Stripes of
the second colour widen along the plate, from about one line width at the
bottom to nearly the full pitch at the camera end. From arm's length it reads
as a blend from one colour into the other. The stripes are the first two
layers, the face against the bed, so they are on the smooth side.

**One-print hybrid (tool changers).** The same bumper and back, printed
fused instead of dropped in. The PETG back fills the window flush with the TPU
rim, then spreads over the whole cavity floor as a 0.8 mm flange above the
rim. That is a lap joint: the TPU rim is trapped under the PETG flange, so the
two are held mechanically and not only by the bond. The flange's edge also
bonds to the inside of the TPU wall. The parts tile the case exactly, with no
gaps and no overlaps, which is what a slicer wants from a multi-material
object.

## Snapmaker U1 (one print)

1. Open `onepiece_hybrid_tpu_petg.3mf` (or `_gradient`) in Snapmaker Orca. It
   loads as one object with two (or three) parts, named `T1 TPU`, `T2 PETG`
   and so on.
2. Assign each part to the toolhead loaded with that filament: TPU 95A on
   one, PETG on another (and the second PETG colour on a third for the
   gradient).
3. Use the slicer's own TPU 95A and PETG filament profiles. Orca slows each
   part to its filament's volumetric limit, so the TPU runs slowly and the
   PETG doesn't.
4. **Bed:** textured PEI at about 70 °C is a fair compromise. That's warm for
   TPU and on the cool side for PETG, and both stick.
5. If your Orca version has **interlocking** under the multimaterial settings
   ("Use beam interlocking"), turn it on. It weaves the two materials together
   where they meet and makes the bond much stronger.
6. Print back face down with no supports. Both materials share only the
   first 2 mm, the back, so the toolhead swaps happen there: about ten layers,
   one or two swaps each. Above that it is TPU walls only. With no purge on
   the U1, the swaps cost time, not filament.

TPU and PETG bond reasonably well to each other, and the lap joint does the
rest. Still, check the first print by flexing the bumper away from the back
at a corner before you trust it on a phone.

## Printing separately

Everything prints **back face down**. No supports are needed: the lip
leans in at 36°.

**TPU (case and frame)**
- Feed it from the external spool, not the AMS.
- Use your slicer's Generic TPU 95A profile: about 230 °C, bed 35–45 °C,
  slow (outer walls around 15–20 mm/s), minimal retraction.
- Use 3–4 walls and 15–20 % infill. The walls are only 1.8 mm, so this ends
  up mostly solid anyway.
- A textured PEI plate releases TPU easily. On smooth PEI, use glue stick.

**PETG (plate)**
- Use about 240 °C, bed 70–80 °C, 0.2 mm layers.
- PETG can bond to smooth PEI hard enough to tear it. Use glue stick as a
  release layer, or print on textured PEI, which also gives a matte face.
- For the gradient, load both colours in the AMS and keep the prime tower.
  Only the first two layers change colour, so the flush is small.

## Fit

The body dimensions are Apple's published specs. **The camera and button
positions are estimates** from the generator and have not been checked on a
real phone. TPU forgives a lot, so print the TPU case first and check the
camera opening and buttons before printing the hybrid. If anything is off,
adjust `TPU_FIT` or pass measurements through the generator (see
[docs/phone-case.md](../docs/phone-case.md)), then rebuild.

If the plate rattles, reduce `PLATE_GAP` (0.2 mm). If it is hard to seat,
raise it.
