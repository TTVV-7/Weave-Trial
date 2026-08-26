"""The point of these tests is that a bad shade never reaches the printer."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from weave.geometry import (LampSpec, build, check_support, stats,
                            with_open_area)
from weave.gcode import write as write_gcode
from weave.profiles import LAMPS, MATERIALS, PRINTERS


def spt(spec: LampSpec) -> int:
    return int(round(spec.waves_per_turn * spec.segments_per_wave))


@pytest.mark.parametrize("name", sorted(LAMPS))
def test_every_preset_is_printable(name):
    spec = LAMPS[name]
    report = check_support(spec, build(spec))
    assert report.ok, f"{name}: {report.problems}"


@pytest.mark.parametrize("name", sorted(LAMPS))
def test_every_preset_is_actually_see_through(name):
    # The whole request. A shade whose beads close up is a vase.
    assert LAMPS[name].open_area_fraction > 0.5


@pytest.mark.parametrize("name", sorted(LAMPS))
def test_reaches_requested_height(name):
    spec = LAMPS[name]
    got = stats(spec, build(spec))["actual_height_mm"]
    # The spiral can only stop on a whole turn, so it lands within one turn.
    assert spec.height - 1.0 <= got <= spec.height + spec.rise_per_turn + 1.0


def test_centreline_never_descends():
    # A turn that sits lower than the one before it drives the nozzle through
    # everything already printed.
    spec = LAMPS["open-weave"]
    path = build(spec)
    idx = path.turn_index
    n = spt(spec)
    for j in range(n, len(idx)):
        here = path.segments[idx[j][0]].z
        before = path.segments[idx[j - n][0]].z
        assert here - before > -spec.mesh_bead_height * 1.2, f"turn dropped at j={j}"


def test_every_turn_welds_to_the_one_below():
    spec = LAMPS["open-weave"]
    path = build(spec)
    n = spt(spec)
    idx = path.turn_index
    per_turn: dict[int, float] = {}
    for j in range(n, len(idx)):
        i, turn = idx[j]
        gap = path.segments[i].z - path.segments[idx[j - n][0]].z
        slack = gap - min(path.segments[i].bead_h,
                          path.segments[idx[j - n][0]].bead_h)
        per_turn[int(turn)] = min(per_turn.get(int(turn), 1e9), slack)
    floating = [t for t, s in per_turn.items() if s > 1e-9]
    assert not floating, f"turns never touching anything: {floating}"


def test_weld_depth_is_a_squish_not_a_crash():
    spec = LAMPS["open-weave"]
    report = check_support(spec, build(spec))
    assert report.max_dip <= spec.mesh_bead_height * 1.2
    # ...but it must actually dip, or nothing is welded to anything.
    assert report.max_dip > spec.weld_overlap * 0.7


def test_deep_overlap_is_caught_not_printed():
    # This is the failure this project exists to prevent: a big amplitude looks
    # like bigger holes and is really the nozzle driving under its own bead.
    spec = replace(LAMPS["open-weave"], weld_overlap=3.0)
    report = check_support(spec, build(spec))
    assert not report.ok
    assert any("below the previous turn" in p for p in report.problems)


def test_whole_number_waves_is_rejected():
    with pytest.raises(ValueError, match="weav"):
        LampSpec(waves_per_turn=12.0)


def test_rise_below_bead_height_is_rejected():
    with pytest.raises(ValueError, match="see-through"):
        LampSpec(rise_per_turn=0.3, mesh_bead_height=0.45)


@pytest.mark.parametrize("fraction", [0.55, 0.7, 0.8, 0.9])
def test_with_open_area_hits_its_target(fraction):
    spec = with_open_area(LAMPS["open-weave"], fraction)
    assert spec.open_area_fraction == pytest.approx(fraction)
    assert check_support(spec, build(spec)).ok


def test_geometry_stays_inside_its_stated_envelope():
    spec = LAMPS["pendant"]
    path = build(spec)
    limit = max(spec.bottom_radius, spec.top_radius) + max(0.0, spec.belly)
    for s in path.segments:
        assert math.hypot(s.x, s.y) <= limit + 1e-6
        assert s.z > 0


def test_gcode_extrusion_only_ever_moves_forward():
    spec = LAMPS["test-ring"]
    text = write_gcode(spec, build(spec), PRINTERS["generic-i3"],
                       MATERIALS["petg-natural"])
    last = 0.0
    retracts = 0
    absolute = True
    for line in text.splitlines():
        if line.startswith("G91"):
            absolute = False
        elif line.startswith("G90"):
            absolute = True
        if not absolute or not line.startswith("G1 ") or " E" not in line:
            continue
        e = float(line.split(" E")[1].split()[0])
        if e < last - 1e-9:
            retracts += 1  # deliberate retraction before a travel move
        last = e
    assert last > 0
    assert retracts <= len(build(spec).breaks)


def test_gcode_keeps_the_shade_on_the_bed():
    spec = LAMPS["table-shade"]
    printer = PRINTERS["bambu-p1s"]
    text = write_gcode(spec, build(spec), printer, MATERIALS["petg-natural"])
    seen = 0
    for line in text.splitlines():
        if line.startswith("G1 ") and " X" in line and " Y" in line:
            x = float(line.split(" X")[1].split()[0])
            y = float(line.split(" Y")[1].split()[0])
            assert 0 <= x <= printer.bed_x and 0 <= y <= printer.bed_y
            seen += 1
    assert seen > 1000


def test_oversized_shade_is_refused():
    spec = replace(LAMPS["open-weave"], bottom_radius=200.0, top_radius=200.0)
    with pytest.raises(ValueError, match="bed"):
        write_gcode(spec, build(spec), PRINTERS["ender3"], MATERIALS["petg-natural"])


def test_too_tall_shade_is_refused():
    spec = replace(LAMPS["open-weave"], height=400.0)
    with pytest.raises(ValueError, match="tall"):
        write_gcode(spec, build(spec), PRINTERS["ender3"], MATERIALS["petg-natural"])


def test_fullcontrol_backend_matches_the_builtin_path():
    fc_backend = pytest.importorskip("weave.fullcontrol_backend")
    pytest.importorskip("fullcontrol")
    spec = LAMPS["test-ring"]
    path = build(spec)
    steps = fc_backend.to_steps(spec, path, PRINTERS["generic-i3"],
                                MATERIALS["petg-natural"])
    import fullcontrol as fc
    points = [s for s in steps if isinstance(s, fc.Point)]
    # One point per segment, plus two per travel move.
    assert len(points) >= len(path.segments)
