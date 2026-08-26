#!/usr/bin/env python3
"""Generate g-code for the see-through woven lamp shade.

    python generate.py --list
    python generate.py --lamp test-ring --printer prusa-mk4
    python generate.py --lamp open-weave --open 0.85 --height 180
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

from weave.geometry import build, check_support, stats, with_open_area
from weave.gcode import write as write_gcode
from weave.profiles import LAMPS, MATERIALS, PRINTERS


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--list", action="store_true", help="show the available profiles and exit")
    p.add_argument("--lamp", default="open-weave", help="shade profile (default: open-weave)")
    p.add_argument("--printer", default="generic-i3")
    p.add_argument("--material", default="petg-natural")

    g = p.add_argument_group("shape overrides (mm)")
    g.add_argument("--height", type=float)
    g.add_argument("--radius", type=float, help="bottom radius")
    g.add_argument("--top-radius", type=float)
    g.add_argument("--belly", type=float, help="mid-height bulge; negative for a waist")

    w = p.add_argument_group("weave overrides")
    w.add_argument("--open", type=float, metavar="FRACTION", dest="open_area",
                   help="target open area, 0-0.95. The see-through dial")
    w.add_argument("--rise", type=float, help="climb per turn (mm); --open sets this for you")
    w.add_argument("--waves", type=float, help="waves per turn; must end in .5")
    w.add_argument("--overlap", type=float,
                   help="weld depth (mm). Keep at or under one bead height")
    w.add_argument("--nozzle", type=float)
    w.add_argument("--bead", type=float, help="mesh bead width and height (mm)")

    o = p.add_argument_group("output")
    o.add_argument("--out", type=Path, default=Path("out/lamp.gcode"))
    o.add_argument("--preview", type=Path, help="also write an SVG preview here")
    o.add_argument("--check-only", action="store_true",
                   help="report printability and write nothing")
    o.add_argument("--fullcontrol", action="store_true",
                   help="emit via FullControl instead of the built-in writer")
    o.add_argument("--force", action="store_true",
                   help="write the g-code even if the printability check fails")
    return p


def resolve_spec(args) -> "object":
    if args.lamp not in LAMPS:
        raise SystemExit(f"unknown lamp {args.lamp!r}; try --list")
    spec = LAMPS[args.lamp]

    # Bead first: open-area and the weld both depend on it.
    if args.nozzle:
        spec = replace(spec, nozzle=args.nozzle)
    if args.bead:
        spec = replace(spec, mesh_bead_width=args.bead, mesh_bead_height=args.bead,
                       wall_width=args.bead)
    for attr, val in (("height", args.height), ("bottom_radius", args.radius),
                      ("top_radius", args.top_radius), ("belly", args.belly),
                      ("waves_per_turn", args.waves), ("rise_per_turn", args.rise),
                      ("weld_overlap", args.overlap)):
        if val is not None:
            spec = replace(spec, **{attr: val})
    if args.radius is not None and args.top_radius is None:
        spec = replace(spec, top_radius=args.radius)
    if args.open_area is not None:
        spec = with_open_area(spec, args.open_area)
    return spec


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.list:
        print("lamps:")
        for name, s in LAMPS.items():
            print(f"  {name:<14} {s.height:>5.0f} mm tall  "
                  f"{2 * s.bottom_radius:>3.0f} mm across  "
                  f"{s.open_area_fraction * 100:>4.0f}% open")
        print("printers: " + ", ".join(PRINTERS))
        print("materials: " + ", ".join(MATERIALS))
        return 0

    spec = resolve_spec(args)
    printer = PRINTERS.get(args.printer) or _die(f"unknown printer {args.printer!r}")
    material = MATERIALS.get(args.material) or _die(f"unknown material {args.material!r}")

    path = build(spec)
    st = stats(spec, path)
    report = check_support(spec, path)

    print(f"{args.lamp}: {st['actual_height_mm']:.0f} mm tall, "
          f"{2 * spec.bottom_radius:.0f} mm across")
    print(f"  open area      {spec.open_area_fraction * 100:.0f}%  "
          f"(holes up to {spec.max_hole_height:.1f} mm tall)")
    print(f"  weave          {spec.waves_per_turn:.1f} waves/turn, "
          f"{spec.nodes_per_turn} welds/turn, {spec.wave_slope_deg:.0f}deg slope")
    print(f"  bead           {st['path_length_m']:.0f} m, "
          f"{st['filament_g']:.0f} g, {st['points']} points")
    print(f"  weld dip       {report.max_dip:.2f} mm "
          f"(bead is {spec.mesh_bead_height:.2f} mm)")
    print(f"  longest bridge {report.max_free_span:.1f} mm unsupported")

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

    if args.fullcontrol:
        from weave.fullcontrol_backend import write as write_fc
        text = write_fc(spec, path, printer, material)
    else:
        text = write_gcode(spec, path, printer, material)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text)
    print(f"\nwrote {args.out} ({len(text) / 1e6:.1f} MB)")

    if args.preview:
        from weave.preview import render
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        args.preview.write_text(render(spec, path))
        print(f"wrote {args.preview}")
    return 0


def _die(msg: str):
    raise SystemExit(msg)


if __name__ == "__main__":
    raise SystemExit(main())
