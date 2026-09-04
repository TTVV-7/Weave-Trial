"""The point of these tests is that a nozzle that cannot be fitted, cannot be
printed, or leaks into the engine bay never reaches the printer.

Every number the part depends on is a relationship with something else -- the
plug to the hole, the channel to the wall around it, the clip to the flare --
so the tests are written as those relationships rather than as expected values
copied out of the source.
"""

from __future__ import annotations

import math
import struct
from dataclasses import replace

import pytest

import nozzle as cli
from washer.check import check_fit
from washer.geom import hole_sdf, ray, sdf_round_rect, widths
from washer.mesh import Mesh
from washer.parts import (build, build_clip, build_gauge, build_nozzle,
                          clip_geometry, inner_ring, outer_stations,
                          printable_nozzle, _half_gap, _ring)
from washer.preview import render
from washer.spec import PRESETS, NozzleSpec

S = NozzleSpec()


# -- the outline ------------------------------------------------------------
def test_round_rect_distance_is_exact():
    # 4 mm out from the flat, and the corner radius from the corner centre.
    assert sdf_round_rect(6.0, 0.0, 2.0, 2.0, 0.5) == pytest.approx(4.0)
    assert sdf_round_rect(1.5, 1.5, 2.0, 2.0, 0.5) == pytest.approx(-0.5)


def test_hole_matches_the_measurements():
    x, y = widths(S.hole())
    assert x == pytest.approx(S.hole_length, abs=0.01)
    assert y == pytest.approx(S.lobe_width, abs=0.01)


def _width_at(sdf, x: float) -> float:
    lo, hi = 0.0, 10.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if sdf(x, mid) < 0 else (lo, mid)
    return 2 * lo


def test_neck_is_the_narrow_part():
    # On the centreline the hole is the lobes; past them it is the neck.
    assert 2 * ray(S.hole(), math.pi / 2) == pytest.approx(S.lobe_width, abs=0.01)
    assert _width_at(S.hole(), 5.5) == pytest.approx(S.hole_neck, abs=0.05)


@pytest.mark.parametrize("t,expected", [(0.25, 0.60), (0.35, 0.73), (0.50, 0.81)])
def test_lobes_follow_the_photograph(t, expected):
    """Widths measured off the photo, as a fraction of the length."""
    x = (t - 0.5) * S.hole_length
    assert _width_at(S.hole(), x) / S.hole_length == pytest.approx(expected, abs=0.05)


def test_offset_is_a_true_offset():
    # Both halves of the outline have exact distance functions, so this holds
    # for the plug and the head alike, at any offset.
    for d in (-0.35, 0.0, 1.6):
        x, y = widths(S.hole(), d)
        assert x == pytest.approx(S.hole_length + 2 * d, abs=0.02)
        assert y == pytest.approx(S.lobe_width + 2 * d, abs=0.02)


def test_fit_scale_scales_the_hole():
    s = replace(S, fit_scale=1.1)
    assert s.L == pytest.approx(S.hole_length * 1.1)
    assert widths(s.hole())[0] == pytest.approx(S.hole_length * 1.1, abs=0.02)


# -- meshes -----------------------------------------------------------------
def _cyl(r=2.0, h=5.0, n=48):
    rings = [[(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), z)
              for i in range(n)] for z in (0.0, h)]
    m = Mesh()
    m.loft(rings)
    return m


def test_loft_is_closed_and_the_right_size():
    m = _cyl()
    report = m.check()
    assert report.ok
    assert report.volume == pytest.approx(math.pi * 4 * 5, rel=0.01)


def test_open_mesh_is_caught():
    m = _cyl()
    del m.tris[3]
    m.solids = [(0, len(m.tris))]
    assert not m.check().ok


def test_inside_out_mesh_is_caught():
    m = _cyl()
    m.tris = [(a, c, b) for a, b, c in m.tris]
    assert not m.check().ok


def test_turning_the_part_over_keeps_it_solid():
    report = _cyl().flipped().check()
    assert report.ok and report.volume > 0


def test_touching_solids_are_checked_separately():
    # Two boxes sharing a face: a union, not a fault.
    m = Mesh()
    m.box(0, 1, 0, 1, 0, 1)
    m.box(1, 2, 0, 1, 0, 1)
    assert m.check().ok and m.check().solids == 2


def test_stl_round_trips():
    data = build(S, "nozzle").to_stl()
    count = struct.unpack("<I", data[80:84])[0]
    assert count == len(build(S, "nozzle"))
    assert len(data) == 84 + 50 * count


# -- the parts --------------------------------------------------------------
@pytest.mark.parametrize("part", ["nozzle", "clip", "gauge", "all"])
def test_every_part_is_watertight(part):
    report = build(S, part).check()
    assert report.ok, report.problems


def test_the_nozzle_is_one_solid():
    # The channel is the inner wall of a tube, so the body needs no unions.
    assert build_nozzle(S).check().solids == 1


@pytest.mark.parametrize("part", ["nozzle", "clip", "gauge", "all"])
def test_every_part_sits_on_the_bed(part):
    lo, _ = build(S, part).bbox()
    assert lo[2] == pytest.approx(0.0, abs=1e-9)


def test_printable_nozzle_puts_the_head_on_the_bed():
    m = printable_nozzle(S)
    lo, hi = m.bbox()
    assert hi[2] - lo[2] == pytest.approx(S.head_height - S.z_bottom, abs=0.01)


def test_head_covers_the_hole():
    x, y = widths(S.hole(), S.head_margin)
    assert x > S.L + 2.0 and y > S.lobe_width + 2.0


# -- fit --------------------------------------------------------------------
@pytest.mark.parametrize("name", sorted(PRESETS))
def test_every_preset_fits(name):
    s = PRESETS[name]
    report = check_fit(s, build_nozzle(s))
    assert report.ok, f"{name}: {report.problems}"


def test_everything_below_the_head_goes_through_the_hole():
    hole = S.hole()
    for z, sdf, off in outer_stations(S):
        if z >= 0.0:
            continue
        for i in range(96):
            th = 2 * math.pi * i / 96
            assert ray(sdf, th, off) < ray(hole, th), f"stuck at z={z:.2f}"


def test_the_plug_is_the_tightest_point():
    # Not the barb: the lobes leave a 10 mm circle free, so the hole is only
    # tight where the part deliberately matches it.
    report = check_fit(S, build_nozzle(S))
    assert report.insertion == pytest.approx(S.clearance, abs=0.02)


def test_a_shank_too_wide_to_go_in_is_refused():
    s = replace(S, flare_hx=6.8)
    report = check_fit(s, build_nozzle(s))
    assert not report.ok and "hole" in " ".join(report.problems)


def test_the_channel_stays_inside_the_body():
    report = check_fit(S, build_nozzle(S))
    assert report.min_wall >= 0.8


def test_a_wider_bore_eats_the_wall_and_is_refused():
    s = replace(S, bore=3.4)
    assert not check_fit(s, build_nozzle(s)).ok


def test_the_jet_leaves_through_the_top_face():
    top = inner_ring(S, S.head_height, 96)
    assert all(p[2] == pytest.approx(S.head_height) for p in top)
    shift = (S.head_height - S.plenum_z) * math.tan(math.radians(S.aim_deg))
    assert sum(p[1] for p in top) / len(top) == pytest.approx(shift, abs=0.05)


def test_the_jet_hole_is_printable():
    assert min(S.jet_w, S.jet_h) >= 0.45
    s = replace(S, jet_h=0.3)
    assert not check_fit(s, build_nozzle(s)).ok


def test_aiming_too_far_over_is_refused():
    s = replace(S, aim_deg=60.0)
    report = check_fit(s, build_nozzle(s))
    assert not report.ok and "overhang" in " ".join(report.problems)


def test_nothing_overhangs_past_45_degrees():
    assert check_fit(S, build_nozzle(S)).max_overhang <= 45.0


# -- the clip ---------------------------------------------------------------
def test_the_clip_grips_the_sheet_it_was_built_for():
    report = check_fit(S, build_nozzle(S))
    lo, hi = report.panel_range
    assert lo <= S.panel <= hi


def test_the_clip_covers_a_range_of_sheet_thicknesses():
    lo, hi = check_fit(S, build_nozzle(S)).panel_range
    assert hi - lo > 1.0, "the wedge is supposed to take up slack"


def test_the_prongs_clear_the_waist():
    g = clip_geometry(S)
    assert g["z_top"] <= S.z_waist_bot, "prongs would foul the taper going in"


def test_the_notch_narrows_as_it_goes_in():
    g = clip_geometry(S)
    assert _half_gap(g, g["y_root"]) < _half_gap(g, g["y_tip"])


def test_the_prong_face_lies_on_the_flare():
    g = clip_geometry(S)
    rise = g["bevel"] / S.clip_thick
    assert rise == pytest.approx(math.tan(math.radians(S.flare_angle)), rel=1e-6)


def test_a_clip_that_cannot_clear_the_waist_is_refused():
    s = replace(S, clip_rim=0.5)
    report = check_fit(s, build_nozzle(s))
    assert not report.ok and "clip" in " ".join(report.problems)


# -- the gauge --------------------------------------------------------------
def test_the_gauge_steps_in_04_mm():
    steps = (-0.8, -0.4, 0.0, 0.4, 0.8)
    m = build_gauge(S, steps=steps)
    assert m.check().ok
    lo, hi = m.bbox()
    assert hi[0] - lo[0] == pytest.approx(14.0 * len(steps))


def test_the_middle_gauge_tab_is_the_nominal_hole():
    tab = _ring(S.hole(), 0.0, 96)
    assert max(p[0] for p in tab) - min(p[0] for p in tab) == pytest.approx(S.L, abs=0.02)


# -- the drawing and the command line ---------------------------------------
def test_preview_draws_something():
    svg = render(S)
    assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
    assert "13.5" in svg


def test_cli_checks_without_writing(tmp_path, capsys):
    assert cli.main(["--check-only"]) == 0
    assert "fit            OK" in capsys.readouterr().out


def test_cli_refuses_a_part_that_will_not_fit(tmp_path):
    out = tmp_path / "n.stl"
    assert cli.main(["--aim", "70", "--out", str(out)]) == 1
    assert not out.exists()


def test_cli_writes_each_part(tmp_path):
    for part in ("nozzle", "clip", "gauge", "all"):
        out = tmp_path / f"{part}.stl"
        assert cli.main(["--part", part, "--out", str(out)]) == 0
        assert out.stat().st_size > 1000


def test_cli_takes_the_measurements_from_the_gauge(tmp_path, capsys):
    assert cli.main(["--length", "13.9", "--panel", "1.2", "--check-only"]) == 0
    assert "13.9" in capsys.readouterr().out
