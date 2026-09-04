#!/usr/bin/env python3
"""Generate a replacement windshield washer nozzle for a measured hole.

    python nozzle.py --list
    python nozzle.py --check-only
    python nozzle.py --part gauge --out out/gauge.stl     # print this first
    python nozzle.py --part all --panel 1.2 --length 13.9 --preview out/n.svg
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

from washer.check import check_fit
from washer.parts import build, build_nozzle
from washer.spec import PRESETS, NozzleSpec

PARTS = ("nozzle", "clip", "gauge", "all")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--list", action="store_true", help="show the presets and exit")
    p.add_argument("--preset", default="measured")
    p.add_argument("--part", default="nozzle", choices=PARTS)

    h = p.add_argument_group("the hole (mm) -- measure it, do not guess")
    h.add_argument("--length", type=float, help="long axis")
    h.add_argument("--neck", type=float, help="across the narrow waist")
    h.add_argument("--lobe-width", type=float, help="across the lobes")
    h.add_argument("--lobe-span", type=float, help="how far the lobes run")
    h.add_argument("--panel", type=float, help="sheet thickness at the hole")
    h.add_argument("--fit", type=float, metavar="SCALE", dest="fit_scale",
                   help="scale every hole dimension; set this from the gauge")

    f = p.add_argument_group("fit and spray")
    f.add_argument("--clearance", type=float, help="gap per side, plug to hole")
    f.add_argument("--aim", type=float, dest="aim_deg",
                   help="jet tilt from vertical, degrees (max 45)")
    f.add_argument("--aim-az", type=float, help="which way it points, degrees")
    f.add_argument("--jet", type=float, nargs=2, metavar=("W", "H"),
                   help="jet slot, mm")
    f.add_argument("--hose-id", type=float, help="washer hose bore")
    f.add_argument("--barb-len", type=float)
    f.add_argument("--facets", type=int, help="samples per section (default 96)")

    o = p.add_argument_group("output")
    o.add_argument("--out", type=Path, default=Path("out/nozzle.stl"))
    o.add_argument("--preview", type=Path, help="also write an SVG drawing here")
    o.add_argument("--check-only", action="store_true",
                   help="report the fit and write nothing")
    o.add_argument("--force", action="store_true",
                   help="write the STL even if the fit check fails")
    return p


def resolve_spec(args) -> NozzleSpec:
    if args.preset not in PRESETS:
        raise SystemExit(f"unknown preset {args.preset!r}; try --list")
    s = PRESETS[args.preset]
    named = (("hole_length", args.length), ("hole_neck", args.neck),
             ("lobe_width", args.lobe_width), ("lobe_span", args.lobe_span),
             ("panel", args.panel), ("fit_scale", args.fit_scale),
             ("clearance", args.clearance), ("aim_deg", args.aim_deg),
             ("aim_az", args.aim_az), ("hose_id", args.hose_id),
             ("barb_len", args.barb_len), ("facets", args.facets))
    for attr, val in named:
        if val is not None:
            s = replace(s, **{attr: val})
    if args.jet:
        s = replace(s, jet_w=args.jet[0], jet_h=args.jet[1])
    return s


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.list:
        print("presets:")
        for name, s in PRESETS.items():
            print(f"  {name:<12} hole {s.L:>4.1f} x {s.W:>3.1f} mm  "
                  f"sheet {s.panel:>3.1f} mm  jet {s.aim_deg:>2.0f} deg")
        print("parts: " + ", ".join(PARTS))
        return 0

    s = resolve_spec(args)
    nozzle = build_nozzle(s)
    fit = check_fit(s, nozzle)

    print(f"hole {s.L:.1f} x {s.W:.1f} mm ({s.lobe_width * s.fit_scale:.1f} over "
          f"the lobes), {s.panel:.1f} mm sheet")
    print(f"  goes in        {fit.insertion:.2f} mm to spare at the tightest point")
    print(f"  head           covers the hole by {s.head_margin:.1f} mm all round")
    print(f"  clip           grips {fit.panel_range[0]:.1f}-{fit.panel_range[1]:.1f} "
          f"mm sheet, {fit.clip_travel:.0f} mm of travel")
    print(f"  channel        {s.bore:.1f} mm bore, {fit.min_wall:.2f} mm wall "
          f"beside it")
    print(f"  jet            {s.jet_w:.1f} x {s.jet_h:.2f} mm at {s.aim_deg:.0f} deg, "
          f"{fit.jet_area:.2f} mm2")
    print(f"  printing       {fit.max_overhang:.0f} deg worst overhang, "
          f"{fit.max_ledge:.2f} mm worst ledge, head face down")
    print(f"  nozzle         {fit.mass_g:.2f} g, {len(nozzle)} triangles")

    if fit.ok:
        print("  fit            OK")
    else:
        print("  fit            FAILED")
        for problem in fit.problems:
            print(f"    - {problem}")

    if args.check_only:
        return 0 if fit.ok else 1
    if not fit.ok and not args.force:
        print("\nrefusing to write an STL; change the numbers or pass --force",
              file=sys.stderr)
        return 1

    mesh = build(s, args.part)
    report = mesh.check()
    if not report.ok:
        print("\nmesh is not watertight -- this is a bug, not a setting:",
              file=sys.stderr)
        for problem in report.problems:
            print(f"  - {problem}", file=sys.stderr)
        return 2

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(mesh.to_stl(f"washer-{args.part}"))
    lo, hi = mesh.bbox()
    size = " x ".join(f"{hi[i] - lo[i]:.1f}" for i in range(3))
    print(f"\nwrote {args.out} -- {args.part}, {size} mm, "
          f"{report.triangles} triangles in {report.solids} closed "
          f"solid{'s' if report.solids > 1 else ''}")

    if args.preview:
        from washer.preview import render
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        args.preview.write_text(render(s, fit))
        print(f"wrote {args.preview}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
