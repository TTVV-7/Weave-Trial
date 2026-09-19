#!/usr/bin/env python3
"""Generate g-code for a parametric iPhone case, painted with the AMS.

    python case.py --list
    python case.py --phone iphone-15-pro --test-fit
    python case.py --phone iphone-16-pro --art logo.svg --palette duo
    python case.py --phone iphone-15 --art logo.svg --show-art
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

from phonecase.gcode import plan_tower, tower_stats, write as write_gcode
from phonecase.paint import Palette, plan as plan_paint
from phonecase.profiles import CASES, FILAMENTS, PALETTES, PRINTERS
from phonecase.spec import PHONES, CaseSpec, Cutout, check_case
from phonecase.svgart import load_file
from phonecase.toolpath import build, stats


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--list", action="store_true",
                   help="show the phones, cases, printers and palettes")
    p.add_argument("--phone", default="iphone-15-pro")
    p.add_argument("--case", default="snug", help="fit preset (default: snug)")
    p.add_argument("--printer", default="generic-mmu")
    p.add_argument("--filament", default="pla")

    g = p.add_argument_group("phone overrides (mm) -- measure yours")
    g.add_argument("--length", type=float)
    g.add_argument("--width", type=float)
    g.add_argument("--thickness", type=float)
    g.add_argument("--corner-radius", type=float)
    g.add_argument("--camera", metavar="WxH[:R]",
                   help="camera opening, e.g. 39x39:11.5")
    g.add_argument("--camera-margin", metavar="TOP,SIDE",
                   help="gap from the body's top and side edge to the opening")
    g.add_argument("--no-buttons", action="store_true",
                   help="leave the side buttons covered instead of cut out")

    c = p.add_argument_group("case overrides (mm)")
    c.add_argument("--clearance", type=float, help="gap around the phone")
    c.add_argument("--wall", type=float)
    c.add_argument("--back", type=float, dest="back_thickness")
    c.add_argument("--lip", type=float)
    c.add_argument("--lip-inset", type=float)
    c.add_argument("--chamfer", type=float, dest="base_chamfer")

    a = p.add_argument_group("artwork")
    a.add_argument("--art", type=Path, metavar="FILE.svg",
                   help="SVG to paint onto the back of the case")
    a.add_argument("--palette", default=None,
                   help="named palette, or use --slot")
    a.add_argument("--slot", action="append", default=[], metavar="N=#RRGGBB:NAME",
                   help="one AMS slot; repeat for each loaded filament")
    a.add_argument("--base", type=int, default=0,
                   help="slot to use for the body of the case (default 0)")
    a.add_argument("--art-fit", default="contain",
                   choices=("contain", "cover", "stretch", "none"))
    a.add_argument("--art-box", default="content", choices=("content", "view"),
                   help="fit the drawing itself, or the SVG's viewBox")
    a.add_argument("--art-scale", type=float, default=1.0)
    a.add_argument("--art-rotate", type=float, default=0.0, metavar="DEG")
    a.add_argument("--art-x", type=float, default=0.0, metavar="MM",
                   help="move the artwork right, as you look at the finished "
                        "case. Negative moves it left")
    a.add_argument("--art-y", type=float, default=0.0, metavar="MM",
                   help="move the artwork up, towards the top of the phone")
    a.add_argument("--art-margin", type=float, default=2.0,
                   help="keep-out at the edge of the back (default 2)")
    a.add_argument("--art-layers", type=int, default=None,
                   help="how many bottom layers carry the artwork")
    a.add_argument("--no-mirror", action="store_true",
                   help="do not flip the artwork. The case prints face down, "
                        "so this makes it come out backwards. See the docs")
    a.add_argument("--wrap", action="store_true",
                   help="carry the artwork up the outside of the side walls")
    a.add_argument("--show-art", action="store_true",
                   help="report the SVG's colours and where they land, no output")

    o = p.add_argument_group("print settings")
    o.add_argument("--nozzle", type=float)
    o.add_argument("--line-width", type=float)
    o.add_argument("--layer-height", type=float)
    o.add_argument("--purge", type=float, metavar="MM3",
                   help="volume flushed per tool change (default from filament)")
    o.add_argument("--no-tower", action="store_true",
                   help="skip the purge tower. Colours will bleed into each other")
    o.add_argument("--brim", type=int, default=0)
    o.add_argument("--skirt", type=int, default=1)
    o.add_argument("--res", type=float, default=None,
                   help="section grid pitch (default 0.3); raise it to go faster")

    w = p.add_argument_group("output")
    w.add_argument("--out", type=Path, default=Path("out/case.gcode"))
    w.add_argument("--no-gcode", action="store_true",
                   help="skip the g-code; useful with --stl on its own")
    w.add_argument("--stl", type=Path, metavar="FILE.stl",
                   help="also write the case as a solid, to slice yourself. "
                        "Built from the same dimensions as the g-code, not "
                        "traced from it. One colour: an STL cannot hold more. "
                        "Needs the manifold3d package")
    w.add_argument("--3mf", type=Path, metavar="FILE.3mf", dest="threemf",
                   help="also write the case as a 3MF, with the artwork cut "
                        "into the back plate as one part per filament, so the "
                        "colours survive into your slicer")
    w.add_argument("--preview", type=Path, help="also write an SVG preview here")
    w.add_argument("--test-fit", nargs="?", type=float, const=7.0,
                   metavar="MM",
                   help="leave the middle of the back open, keeping a MM rim "
                        "(default 7) around the outline and the holes. Checks "
                        "every dimension for a third of the filament. Print "
                        "this first, and in one colour")
    w.add_argument("--check-only", action="store_true",
                   help="report and write nothing")
    w.add_argument("--force", action="store_true",
                   help="write the g-code even if the check fails")
    return p


def resolve_spec(args) -> CaseSpec:
    if args.phone not in PHONES:
        raise SystemExit(f"unknown phone {args.phone!r}; try --list")
    if args.case not in CASES:
        raise SystemExit(f"unknown case {args.case!r}; try --list")
    phone = PHONES[args.phone]

    for attr, val in (("length", args.length), ("width", args.width),
                      ("thickness", args.thickness),
                      ("corner_radius", args.corner_radius)):
        if val is not None:
            phone = replace(phone, **{attr: val})
    if args.camera:
        head, _, r = args.camera.partition(":")
        try:
            cw, ch = (float(v) for v in head.lower().split("x"))
        except ValueError:
            raise SystemExit(f"--camera wants WxH[:R], got {args.camera!r}")
        phone = replace(phone, camera_w=cw, camera_h=ch,
                        camera_r=float(r) if r else min(cw, ch) / 3)
    if args.camera_margin:
        try:
            top, side = (float(v) for v in args.camera_margin.split(","))
        except ValueError:
            raise SystemExit("--camera-margin wants TOP,SIDE")
        phone = replace(phone, camera_margin_top=top, camera_margin_side=side)

    kw = dict(CASES[args.case])
    for attr in ("clearance", "wall", "back_thickness", "lip", "lip_inset",
                 "base_chamfer", "nozzle", "line_width", "layer_height"):
        val = getattr(args, attr, None)
        if val is not None:
            kw[attr] = val
    if args.art_layers is not None:
        kw["art_layers"] = args.art_layers
    if args.res is not None:
        kw["section_res"] = args.res

    spec = CaseSpec(phone, **kw)
    # Cutouts depend on the fit, so they are rebuilt once the fit is settled.
    spec.cutouts = phone.cutouts(back_thickness=spec.back_thickness,
                                 cavity_depth=spec.cavity_depth,
                                 clearance=spec.clearance,
                                 buttons=not args.no_buttons)
    return spec


def resolve_palette(args) -> Palette:
    """Pick the palette, leaving the body colour to be settled once the
    artwork has been rasterised (see :func:`main`)."""
    if args.slot:
        return Palette.parse(args.slot, args.base)
    name = args.palette or ("duo" if args.art else "mono")
    if name not in PALETTES:
        raise SystemExit(f"unknown palette {name!r}; try --list")
    pal = PALETTES[name]
    return Palette(list(pal.slots), args.base) if args.base else pal


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.list:
        print("phones:")
        for name, ph in PHONES.items():
            print(f"  {name:<20} {ph.length:>5.1f} x {ph.width:>4.1f} x "
                  f"{ph.thickness:.2f} mm")
        print("cases:     " + ", ".join(CASES))
        print("printers:  " + ", ".join(PRINTERS))
        print("filaments: " + ", ".join(FILAMENTS))
        print("palettes:")
        for name, pal in PALETTES.items():
            print(f"  {name:<10} " + "  ".join(
                f"T{s.index} {s.name} {s.hex}" for s in pal.slots))
        return 0

    spec = resolve_spec(args)
    palette = resolve_palette(args)
    printer = PRINTERS.get(args.printer) or _die(f"unknown printer {args.printer!r}")
    filament = FILAMENTS.get(args.filament) or _die(
        f"unknown filament {args.filament!r}")
    if args.purge is not None:
        filament = replace(filament, purge_mm3=args.purge)
    if args.no_tower:
        filament = replace(filament, purge_mm3=0.0)

    art = None
    if args.art:
        if not args.art.exists():
            raise SystemExit(f"no such file: {args.art}")
        art = load_file(args.art)

    place_kw = dict(fit=args.art_fit, box=args.art_box, margin=args.art_margin,
                    scale=args.art_scale, rotate=args.art_rotate,
                    offset=(args.art_x, args.art_y),
                    mirror=not args.no_mirror)
    if args.test_fit:
        art = None
    paint = plan_paint(art, palette, spec.outer_w, spec.outer_l, **place_kw)

    # The sides and the inside of the case are the body colour, and the least
    # surprising body colour is whatever the artwork mostly is. Rasterising
    # is what reveals that, so the plan is rebuilt once with the answer.
    if art is not None and args.base == 0 and "--base" not in (argv or sys.argv):
        area = paint.raster.area_mm2()
        dominant = max(area, key=area.get)
        if dominant != palette.base:
            palette = Palette(list(palette.slots), dominant)
            paint = plan_paint(art, palette, spec.outer_w, spec.outer_l,
                               **place_kw)

    if args.show_art:
        if art is None:
            raise SystemExit("--show-art needs --art")
        print(f"{args.art}: {len(art.shapes)} filled shapes")
        for rgb, slot, share in paint.mapping:
            s = palette.slots[slot]
            print(f"  #{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}  {share * 100:5.1f}% "
                  f"-> T{slot} {s.name} {s.hex}")
        area = paint.raster.area_mm2()
        print("  on the case:")
        for slot in sorted(area):
            print(f"    T{slot} {palette.slots[slot].name:<12} "
                  f"{area[slot]:7.0f} mm2")
        for msg in paint.warnings:
            print(f"  ! {msg}")
        return 0

    report = check_case(spec, bed=(printer.bed_x, printer.bed_y, printer.max_z),
                        slots=printer.tools,
                        used_slots=len(paint.raster.used_slots()))

    print(f"{args.phone} / {args.case}: {spec.outer_w:.1f} x {spec.outer_l:.1f} "
          f"x {spec.height:.1f} mm")
    print(f"  fit            {spec.clearance:.2f} mm gap, wall {spec.wall:.2f} mm "
          f"({spec.perimeters} perimeters at {spec.wall_line:.3f} mm)")
    print(f"  back plate     {spec.back_thickness:.2f} mm, "
          f"{spec.solid_layers} layers, artwork on the first {spec.art_layers}")
    print(f"  lip            {spec.lip:.2f} mm tall, {spec.lip_inset:.2f} mm in "
          f"({spec.lip_overhang_deg:.0f} deg overhang)")
    print(f"  cutouts        " + ", ".join(c.name for c in spec.cutouts))
    body = palette.slots[palette.base]
    print(f"  body colour    T{body.index} {body.name} {body.hex}"
          + ("  (the artwork's main colour; override with --base)"
             if art is not None and args.base == 0
             and body.index != 0 else ""))

    if args.test_fit:
        print(f"  TEST FIT       back plate reduced to a "
              f"{args.test_fit:.0f} mm rim, artwork off")

    path = build(spec, paint, wrap=args.wrap, brim=args.brim, skirt=args.skirt,
                 test_fit=args.test_fit)
    st = stats(spec, path, density=filament.density,
               filament_d=printer.filament_diameter)
    tower = plan_tower(spec, path, filament) if not args.no_tower else None
    tw = (tower_stats(spec, path, tower, printer, filament)
          if tower is not None else {"grams": 0.0, "layers": 0})

    print(f"  toolpath       {st['layers']} layers, "
          f"{st['path_length_m']:.0f} m, {st['points']} points")
    print(f"  filament       {st['grams']:.1f} g"
          + (f" + {tw['grams']:.1f} g purged" if tw["grams"] else ""))
    for slot in sorted(st["per_slot_g"]):
        name = palette.slots[slot].name if slot < len(palette) else "?"
        print(f"    T{slot} {name:<12} {st['per_slot_g'][slot]:5.2f} g")
    print(f"  tool changes   {st['tool_changes']}"
          + (f" (tower {tower.w:.0f} x {tower.d:.0f} mm, "
             f"{tw['layers']} layers)" if tower and tower.active else ""))

    for msg in paint.warnings:
        print(f"  ! {msg}")
    for msg in report.warnings:
        print(f"  ! {msg}")
    if tw["grams"] > st["grams"]:
        print(f"  ! the purge tower ({tw['grams']:.0f} g) outweighs the case "
              f"({st['grams']:.0f} g). Every layer that changes colour costs "
              f"{filament.purge_mm3:.0f} mm3 of flush; keeping the artwork on "
              "the back plate instead of --wrap is what makes that go away")

    if report.ok:
        print("  printability   OK")
    else:
        print("  printability   FAILED")
        for problem in report.problems:
            print(f"    - {problem}")

    if args.check_only:
        return 0 if report.ok else 1
    if not report.ok and not args.force:
        print("\nrefusing to write g-code; adjust the settings or pass --force",
              file=sys.stderr)
        return 1

    print()
    if not args.no_gcode:
        text = write_gcode(spec, path, printer, filament, paint, tower=tower)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        print(f"wrote {args.out} ({len(text) / 1e6:.1f} MB)")

    if (args.stl or args.threemf) and args.test_fit:
        raise SystemExit(
            "--test-fit is a toolpath trick: it leaves the middle of the back "
            "plate unfilled, which is a thing g-code can say and a solid "
            "cannot. Export the whole case, or take the test fit as g-code")

    if args.stl:
        from phonecase.solid import (MeshUnavailable, build_solid, mesh_to_stl,
                                     stats as solid_stats)
        try:
            solid = build_solid(spec)
        except MeshUnavailable as exc:
            raise SystemExit(str(exc))
        data = mesh_to_stl(solid, header=f"{args.phone} case - phonecase")
        args.stl.parent.mkdir(parents=True, exist_ok=True)
        args.stl.write_bytes(data)
        ss = solid_stats(solid)
        print(f"wrote {args.stl} ({len(data) / 1e6:.2f} MB, "
              f"{ss['triangles']} triangles, {ss['volume_mm3'] / 1000:.1f} cm3)")

    if args.threemf:
        from phonecase.solid import MeshUnavailable
        from phonecase.threemf import (colour_parts, parts_to_3mf,
                                       stats as mf_stats)
        try:
            parts = colour_parts(spec, paint, wrap=args.wrap)
        except MeshUnavailable as exc:
            raise SystemExit(str(exc))
        data = parts_to_3mf(parts, origin=(spec.outer_w / 2, spec.outer_l / 2),
                            name=args.phone)
        args.threemf.parent.mkdir(parents=True, exist_ok=True)
        args.threemf.write_bytes(data)
        ms = mf_stats(parts)
        print(f"wrote {args.threemf} ({len(data) / 1e6:.2f} MB, "
              f"{ms['parts']} parts, {ms['triangles']} triangles)")
        for part in ms["per_part"]:
            print(f"    T{part['slot']} {part['name']:<12} {part['hex']}  "
                  f"{part['volume_mm3'] / 1000:5.2f} cm3")

    if args.preview:
        from phonecase.preview import render
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        args.preview.write_text(render(spec, path, paint, stats=st))
        print(f"wrote {args.preview}")
    return 0


def _die(msg: str):
    raise SystemExit(msg)


if __name__ == "__main__":
    raise SystemExit(main())
