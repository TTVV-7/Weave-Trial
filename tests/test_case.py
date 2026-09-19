"""The point of these tests is that a bad case never reaches the printer.

The expensive one is building a toolpath, so the fixtures build a short test
band on a coarse section grid and the whole file still runs in seconds.
"""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

import case as cli
from phonecase.gcode import plan_tower, tower_stats, write as write_gcode
from phonecase.paint import Palette, Placement, plan as plan_paint, split
from phonecase.profiles import CASES, FILAMENTS, PALETTES, PRINTERS
from phonecase.shapes import Field, RRect, Section
from phonecase.spec import PHONES, CaseSpec, Cutout, check_case
from phonecase.svgart import load
from phonecase.toolpath import build, section_at, stats

BED = (256.0, 256.0, 256.0)


def spec_for(model="iphone-15-pro", **kw) -> CaseSpec:
    kw.setdefault("section_res", 0.6)
    return CaseSpec(PHONES[model], **kw)


@pytest.fixture(scope="module")
def band():
    """A case truncated to a few layers: enough to exercise plate and wall."""
    spec = spec_for()
    paint = plan_paint(None, PALETTES["mono"], spec.outer_w, spec.outer_l)
    return spec, paint, build(spec, paint, test_fit=2.2)


# --------------------------------------------------------------------------
# the fit
# --------------------------------------------------------------------------

@pytest.mark.parametrize("model", sorted(PHONES))
def test_every_phone_makes_a_printable_case(model):
    spec = spec_for(model)
    report = check_case(spec, bed=BED, slots=4, used_slots=1)
    assert report.ok, f"{model}: {report.problems}"


@pytest.mark.parametrize("model", sorted(PHONES))
@pytest.mark.parametrize("preset", sorted(CASES))
def test_every_preset_fits_the_phone_it_is_for(model, preset):
    spec = spec_for(model, **CASES[preset])
    # The whole job: the phone has to go in, and not fall out.
    assert spec.inner_w == pytest.approx(spec.phone.width + 2 * spec.clearance)
    assert spec.inner_l == pytest.approx(spec.phone.length + 2 * spec.clearance)
    assert spec.cavity_depth > spec.phone.thickness
    assert spec.lip_inset > 0


def test_wall_perimeters_span_the_wall_exactly():
    # A wall that the perimeters do not fill has a void up the middle of it.
    for wall in (1.0, 1.2, 1.7, 2.0, 2.4, 3.1):
        spec = spec_for(wall=wall)
        assert spec.perimeters * spec.wall_line == pytest.approx(wall)
        assert spec.perimeters >= 2


def test_a_too_thin_wall_is_refused():
    r = check_case(spec_for(wall=0.5), bed=BED)
    assert not r.ok and any("wall" in p for p in r.problems)


def test_a_too_tight_clearance_is_refused():
    r = check_case(spec_for(clearance=0.05), bed=BED)
    assert not r.ok and any("clearance" in p for p in r.problems)


def test_a_lip_that_leans_in_too_far_is_refused():
    # A lip stepped in faster than it climbs is an overhang that droops into
    # the screen cutout and ruins the one edge you touch every day.
    r = check_case(spec_for(lip=0.5, lip_inset=1.2), bed=BED)
    assert not r.ok and any("lean" in p for p in r.problems)
    assert check_case(spec_for(lip=1.6, lip_inset=0.9), bed=BED).ok


def test_a_cutout_off_the_edge_is_refused():
    spec = spec_for()
    spec.cutouts = [Cutout("camera", "back", 200.0, 0.0, 20.0, 20.0, 4.0)]
    r = check_case(spec, bed=BED)
    assert not r.ok and any("camera" in p for p in r.problems)


def test_a_case_too_big_for_the_bed_is_refused():
    r = check_case(spec_for("iphone-16-pro-max"), bed=(120.0, 120.0, 250.0))
    assert not r.ok and any("bed" in p for p in r.problems)


def test_more_colours_than_slots_is_refused():
    r = check_case(spec_for(), bed=BED, slots=2, used_slots=4)
    assert not r.ok and any("slots" in p for p in r.problems)


# --------------------------------------------------------------------------
# the section
# --------------------------------------------------------------------------

def test_the_cavity_is_actually_empty():
    spec = spec_for()
    sec = section_at(spec, spec.back_thickness + 1.0)
    assert sec.sdf(0, 0) > 0, "the phone has nowhere to go"
    # ... and the wall around it is solid. The top edge has no cutouts in
    # it, which is what makes it the honest place to ask.
    assert sec.sdf(0, spec.outer_l / 2 - spec.wall / 2) < 0


def test_the_back_plate_is_solid_except_where_the_camera_is():
    spec = spec_for()
    sec = section_at(spec, spec.back_thickness / 2)
    assert sec.sdf(0, 0) < 0
    cam = next(c for c in spec.cutouts if c.name == "camera")
    assert sec.sdf(cam.u, cam.v) > 0


def test_a_side_cutout_opens_the_wall_only_where_it_should():
    spec = spec_for()
    port = next(c for c in spec.cutouts if c.name == "port")
    wall_y = -(spec.outer_l / 2 - spec.wall / 2)
    assert section_at(spec, port.v).sdf(port.u, wall_y) > 0
    # Above the hole the wall is back.
    assert section_at(spec, port.v + port.h / 2 + 0.5).sdf(port.u, wall_y) < 0


def test_no_side_cutout_pierces_the_back_plate():
    # A hole through the plate edge leaves nothing joining the two halves of
    # the wall, and the case snaps there on the first drop. The port is
    # deliberately specified tall enough to try.
    spec = spec_for()
    port = next(c for c in spec.cutouts if c.name == "port")
    assert port.v - port.h / 2 <= spec.back_thickness + 1e-9, \
        "this test is not testing anything unless the port reaches the plate"
    for z in (0.01, spec.back_thickness / 2, spec.back_thickness - 0.01):
        sec = section_at(spec, z)
        # Every edge of the plate is solid: only the camera goes through it.
        # Inset past the base chamfer, which is meant to pull the outline in
        # down here.
        inset = spec.base_chamfer + 0.3
        for x, y in ((0, -(spec.outer_l / 2 - inset)),
                     (0, spec.outer_l / 2 - inset),
                     (-(spec.outer_w / 2 - inset), 0),
                     (spec.outer_w / 2 - inset, 0)):
            assert sec.sdf(x, y) < 0, f"the plate is pierced at z={z}"


def test_the_lip_leans_inwards_and_never_outwards():
    spec = spec_for()
    prev = spec.inner_w
    for z in (spec.height - spec.lip, spec.height - spec.lip / 2, spec.height):
        cav = section_at(spec, z).cavity
        assert cav is not None and 2 * cav.hx <= prev + 1e-9
        prev = 2 * cav.hx
    assert prev == pytest.approx(spec.inner_w - 2 * spec.lip_inset)


# --------------------------------------------------------------------------
# the distance field
# --------------------------------------------------------------------------

def test_a_contour_is_offset_by_the_level_it_was_asked_for():
    sec = Section(RRect(0, 0, 20, 30, 5))
    fld = Field(sec, 0.25, band=4.0)
    for level in (-0.4, -1.0, -1.8):
        loops = fld.contours(level)
        assert len(loops) == 1
        for x, y in loops[0]:
            assert sec.outer.sdf(x, y) == pytest.approx(level, abs=0.06)


def test_a_hole_gets_its_own_perimeter_rather_than_a_severed_one():
    # This is the whole reason the section is a distance field: the
    # perimeters have to turn and run around an opening, not stop dead at it.
    sec = Section(RRect(0, 0, 20, 30, 5), None, (RRect(0, 0, 5, 5, 1),))
    loops = Field(sec, 0.2, band=4.0).contours(-0.4)
    assert len(loops) == 2
    inner = min(loops, key=lambda lp: max(abs(p[0]) for p in lp))
    for x, y in inner:
        assert sec.holes[0].sdf(x, y) == pytest.approx(0.4, abs=0.06)


def test_infill_stays_inside_the_region():
    sec = Section(RRect(0, 0, 20, 30, 5))
    fld = Field(sec, 0.25, band=4.0)
    lines = fld.infill(-1.0, 0.45, 45.0)
    assert lines
    for line in lines:
        for x, y in line:
            assert sec.outer.sdf(x, y) <= -0.9


# --------------------------------------------------------------------------
# the toolpath
# --------------------------------------------------------------------------

def test_the_toolpath_starts_on_the_bed_and_climbs(band):
    spec, _, path = band
    assert path.layers[0].z == pytest.approx(spec.first_layer_height)
    zs = [layer.z for layer in path.layers]
    assert zs == sorted(zs)
    assert all(b > a for a, b in zip(zs, zs[1:]))


def test_the_toolpath_reaches_the_top_of_the_case():
    spec = spec_for("iphone-se-3", section_res=0.9)
    paint = plan_paint(None, PALETTES["mono"], spec.outer_w, spec.outer_l)
    path = build(spec, paint, skirt=0)
    assert path.layers[-1].z == pytest.approx(spec.height, abs=spec.layer_height)


def test_nothing_but_the_skirt_leaves_the_footprint(band):
    spec, _, path = band
    limit = max(spec.outer_w, spec.outer_l) / 2 + 0.2
    for layer in path.layers:
        for run in layer.runs:
            if run.kind in ("skirt", "brim"):
                continue
            for x, y in run.pts:
                assert abs(x) <= spec.outer_w / 2 + 0.2
                assert abs(y) <= spec.outer_l / 2 + 0.2
                assert abs(x) <= limit


def test_no_extrusion_runs_through_a_cutout(band):
    spec, _, path = band
    for layer in path.layers:
        sec = section_at(spec, layer.z - layer.height / 2)
        for run in layer.runs:
            if run.kind in ("skirt", "brim"):
                continue
            for x, y in run.pts:
                for hole in sec.holes:
                    assert hole.sdf(x, y) > -0.25, \
                        f"{run.kind} at z={layer.z:.2f} is inside a cutout"


def test_max_layers_builds_the_skin_and_stops():
    # What the back of the case looks like is decided by the artwork layers,
    # so a preview does not need the other fifty.
    spec = spec_for(section_res=0.9)
    paint = plan_paint(load(_SVG), PALETTES["primary"], spec.outer_w,
                       spec.outer_l)
    skin = build(spec, paint, skirt=0, max_layers=spec.art_layers)
    assert len(skin.layers) == spec.art_layers
    full = build(spec, paint, skirt=0)
    assert len(full.layers) > spec.art_layers
    # The layers it did build are the same ones the full print would lay.
    for a, b in zip(skin.layers, full.layers):
        assert a.z == pytest.approx(b.z)
        assert [r.slot for r in a.runs] == [r.slot for r in b.runs]


def test_a_test_fit_keeps_a_rim_and_drops_the_middle():
    # The point of a test fit is that it still answers every question about
    # whether the case fits, for a fraction of the filament.
    spec = spec_for(section_res=0.6)
    paint = plan_paint(None, PALETTES["mono"], spec.outer_w, spec.outer_l)
    full = build(spec, paint, skirt=0)
    rim = build(spec, paint, skirt=0, test_fit=7.0)
    assert len(rim.layers) == len(full.layers)
    assert stats(spec, rim)["grams"] < 0.7 * stats(spec, full)["grams"]

    sec = section_at(spec, spec.back_thickness / 2)
    plate = [r for ly in rim.layers for r in ly.runs if r.kind == "infill"]
    assert plate
    for run in plate:
        for x, y in run.pts:
            # The tolerance is the grid: the rim is as accurate as the
            # field it was cut out of, and no more.
            assert sec.sdf(x, y) > -7.0 - 2 * spec.section_res, \
                "infill left in the middle"
    # ... and the rim follows the camera hole as well as the outline.
    cam = next(c for c in spec.cutouts if c.name == "camera")
    assert any(abs(math.hypot(x - cam.u, y - cam.v)
                   - max(cam.w, cam.h) / 2) < 7.0
               for run in plate for x, y in run.pts)


def test_a_layer_uses_each_colour_once(band):
    spec, _, _ = band
    paint = plan_paint(load(_SVG), PALETTES["primary"], spec.outer_w,
                       spec.outer_l)
    path = build(spec, paint, test_fit=1.0)
    for layer in path.layers:
        slots = layer.slots
        assert len(slots) == len(set(slots)), \
            "a colour is picked up twice in one layer, which costs a purge"


# --------------------------------------------------------------------------
# reading the artwork
# --------------------------------------------------------------------------

_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 200">
  <rect width="100" height="200" fill="#1b1b1f"/>
  <rect x="5" y="5" width="30" height="30" fill="#e03131"/>
  <circle cx="50" cy="150" r="20" fill="#1c7ed6"/>
</svg>"""


def test_the_basic_shapes_all_parse():
    art = load("""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">
      <rect width="4" height="4" fill="red"/>
      <circle cx="5" cy="5" r="2" fill="#0f0"/>
      <ellipse cx="7" cy="7" rx="2" ry="1" fill="rgb(0,0,255)"/>
      <polygon points="0,9 2,9 1,7" fill="#123456"/>
      <path d="M0 0 h3 v3 z" fill="#abc"/>
    </svg>""")
    assert len(art.shapes) == 5
    assert {s.rgb for s in art.shapes} >= {
        (255, 0, 0), (0, 255, 0), (0, 0, 255), (18, 52, 86), (170, 187, 204)}


def test_every_path_command_is_understood():
    art = load("""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
      <path fill="#000" d="M2 2 L6 2 H10 V6 C12 6 14 8 14 10
        S12 14 10 14 Q6 14 6 10 T2 8 A2 2 0 0 1 2 2 Z"/>
    </svg>""")
    assert len(art.shapes) == 1
    pts = art.shapes[0].subpaths[0]
    assert len(pts) > 20, "curves were not flattened"
    assert math.dist(pts[0], pts[-1]) < 1e-6, "Z did not close the path"


def test_relative_and_absolute_commands_agree():
    a = load('<svg xmlns="http://www.w3.org/2000/svg"><path fill="#000" '
             'd="M1 1 L5 1 L5 5 Z"/></svg>')
    b = load('<svg xmlns="http://www.w3.org/2000/svg"><path fill="#000" '
             'd="m1 1 l4 0 l0 4 z"/></svg>')
    assert a.shapes[0].subpaths[0] == b.shapes[0].subpaths[0]


def test_nested_transforms_compose():
    art = load("""<svg xmlns="http://www.w3.org/2000/svg">
      <g transform="translate(10,20)"><g transform="scale(2)">
        <rect width="1" height="1" fill="#000"/>
      </g></g></svg>""")
    xs = [p[0] for p in art.shapes[0].subpaths[0]]
    ys = [p[1] for p in art.shapes[0].subpaths[0]]
    assert min(xs) == pytest.approx(10) and max(xs) == pytest.approx(12)
    assert min(ys) == pytest.approx(20) and max(ys) == pytest.approx(22)


def test_fill_is_inherited_and_style_wins():
    art = load("""<svg xmlns="http://www.w3.org/2000/svg">
      <g fill="#ff0000"><rect width="2" height="2"/>
      <rect width="2" height="2" style="fill:#00ff00"/></g></svg>""")
    assert [s.rgb for s in art.shapes] == [(255, 0, 0), (0, 255, 0)]


@pytest.mark.parametrize("cap,width", [("butt", 11.0), ("round", 12.0)])
def test_a_stroke_with_no_fill_still_prints_something(cap, width):
    # Plenty of line art has no fills at all; printing nothing would be a
    # poor answer to "paint this on my case".
    art = load(f'<svg xmlns="http://www.w3.org/2000/svg"><path fill="none" '
               f'stroke="#000" stroke-width="2" stroke-linecap="{cap}" '
               f'd="M0 0 L10 0 L10 10"/></svg>')
    assert art.shapes and art.shapes[0].origin.endswith(":stroke")
    x0, y0, x1, y1 = art.shapes[0].bbox()
    assert x1 - x0 == pytest.approx(width, abs=0.6)


def test_text_is_reported_rather_than_silently_dropped():
    art = load('<svg xmlns="http://www.w3.org/2000/svg"><text>hi</text></svg>')
    assert any("text" in w for w in art.warnings)
    assert any("convert text to paths" in w for w in art.warnings)


# --------------------------------------------------------------------------
# colour
# --------------------------------------------------------------------------

def test_the_nearest_filament_is_the_one_a_human_would_pick():
    pal = Palette.parse(["#ffffff:white", "#000000:black", "#d32f2f:red",
                         "#1565c0:blue"])
    assert pal.match((250, 250, 245)) == 0
    assert pal.match((20, 18, 22)) == 1
    assert pal.match((200, 40, 40)) == 2
    assert pal.match((30, 90, 190)) == 3


def test_a_palette_with_gaps_is_refused():
    with pytest.raises(ValueError):
        Palette.parse(["0=#ffffff:a", "2=#000000:b"])
    with pytest.raises(ValueError):
        Palette.parse(["0=#ffffff:a", "0=#000000:b"])


def test_the_artwork_is_mirrored_for_a_face_down_print():
    # The case prints back down, so a shape drawn top-left of the page has to
    # go into the g-code at +x to read top-left on the finished case. Get
    # this wrong and every case comes out backwards.
    spec = spec_for()
    pal = Palette.parse(["#1b1b1f:ink", "#e03131:red", "#1c7ed6:blue"])
    paint = plan_paint(load(_SVG), pal, spec.outer_w, spec.outer_l)
    # The red square is top-left on the page.
    assert paint.slot_at(spec.outer_w / 4, spec.outer_l / 3) == 1
    flipped = plan_paint(load(_SVG), pal, spec.outer_w, spec.outer_l,
                         mirror=False)
    assert flipped.slot_at(-spec.outer_w / 4, spec.outer_l / 3) == 1


def test_artwork_that_misses_the_case_is_reported_as_area():
    spec = spec_for()
    pal = Palette.parse(["#1b1b1f:ink", "#e03131:red", "#1c7ed6:blue"])
    paint = plan_paint(load(_SVG), pal, spec.outer_w, spec.outer_l)
    area = paint.raster.area_mm2()
    assert sum(area.values()) == pytest.approx(
        spec.outer_w * spec.outer_l, rel=0.03)
    assert area[1] > 100 and area[2] > 100


def test_splitting_a_line_by_colour_keeps_it_continuous():
    spec = spec_for()
    pal = Palette.parse(["#1b1b1f:ink", "#e03131:red", "#1c7ed6:blue"])
    paint = plan_paint(load(_SVG), pal, spec.outer_w, spec.outer_l)
    line = [(-spec.outer_w / 2 + 1, spec.outer_l / 3),
            (spec.outer_w / 2 - 1, spec.outer_l / 3)]
    runs = split(line, paint)
    assert len(runs) > 1, "the line crosses a colour boundary"
    assert runs[0][1][0] == pytest.approx(line[0])
    assert runs[-1][1][-1] == pytest.approx(line[1])
    for (_, a), (_, b) in zip(runs, runs[1:]):
        assert a[-1] == pytest.approx(b[0]), "a gap between two colours"


def test_a_placement_with_no_art_is_the_identity():
    p = Placement(1, 1, 0, 0, 0, False)
    assert p.apply((3.0, 4.0)) == (3.0, -4.0)


# --------------------------------------------------------------------------
# g-code and the purge tower
# --------------------------------------------------------------------------

def _gcode(spec, paint, printer="bambu-p1s-ams", filament="pla", **kw):
    path = build(spec, paint, **kw)
    pr, fl = PRINTERS[printer], FILAMENTS[filament]
    tower = plan_tower(spec, path, fl)
    return path, tower, write_gcode(spec, path, pr, fl, paint, tower=tower)


def test_one_colour_needs_no_purge_tower(band):
    spec, paint, _ = band
    _, tower, text = _gcode(spec, paint, test_fit=1.0)
    assert not tower.active
    assert "no purge tower" in text


def test_a_tool_change_purges_before_it_prints_on_the_case():
    spec = spec_for(section_res=0.9)
    paint = plan_paint(load(_SVG), PALETTES["primary"], spec.outer_w,
                       spec.outer_l)
    path, tower, text = _gcode(spec, paint, test_fit=1.0)
    assert tower.active
    # Skip the preamble: the first tool is selected before anything is in
    # the nozzle, so it has nothing to flush.
    lines = text.split(";LAYER_CHANGE", 1)[1].splitlines()
    changes = [i for i, ln in enumerate(lines) if ln.startswith("T")
               and ln[1:].isdigit()]
    assert changes
    for i in changes:
        after = "\n".join(lines[i:i + 40])
        assert ";TYPE:purge" in after, \
            "a tool change that goes straight back to the case bleeds colour"


def test_the_tower_never_sits_on_the_case():
    spec = spec_for(section_res=0.9)
    paint = plan_paint(load(_SVG), PALETTES["primary"], spec.outer_w,
                       spec.outer_l)
    _, tower, _ = _gcode(spec, paint, test_fit=1.0)
    assert tower.x - tower.w / 2 > spec.outer_w / 2


def test_the_tower_is_built_on_every_layer_it_has_to_be():
    # A tower with a hole in it prints the next purge into mid air.
    spec = spec_for(section_res=0.9)
    paint = plan_paint(load(_SVG), PALETTES["primary"], spec.outer_w,
                       spec.outer_l)
    path, tower, text = _gcode(spec, paint, test_fit=2.5)
    assert tower.active
    blocks = text.split(";LAYER_CHANGE")[1:]
    for layer in path.layers:
        if tower.first <= layer.index <= tower.last:
            body = blocks[layer.index]
            assert ";TYPE:purge" in body or ";TYPE:tower-sparse" in body


def test_extrusion_only_ever_goes_forwards_apart_from_retracts():
    spec = spec_for(section_res=0.9)
    paint = plan_paint(load(_SVG), PALETTES["primary"], spec.outer_w,
                       spec.outer_l)
    _, _, text = _gcode(spec, paint, test_fit=1.0)
    e = 0.0
    fl = FILAMENTS["pla"]
    # Scan the body only: the prime line before it is zeroed by a G92, and
    # the end g-code retracts in relative mode.
    body = text.split(";LAYER_CHANGE", 1)[1].split("\nG91", 1)[0]
    for line in body.splitlines():
        if not line.startswith("G1 ") or " E" not in line:
            continue
        val = float(line.split(" E")[1].split()[0])
        assert val >= e - fl.retract_mm - 1e-6, "extruder ran backwards"
        e = max(e, val)
    assert e > 0


def test_a_case_that_does_not_fit_the_bed_with_its_tower_is_refused():
    spec = spec_for("iphone-16-pro-max", section_res=0.9)
    paint = plan_paint(load(_SVG), PALETTES["primary"], spec.outer_w,
                       spec.outer_l)
    path = build(spec, paint, test_fit=1.0)
    small = replace(PRINTERS["generic-mmu"], bed_x=120.0, bed_y=300.0)
    with pytest.raises(ValueError, match="bed"):
        write_gcode(spec, path, small, FILAMENTS["pla"], paint)


def test_the_header_accounts_for_every_slot(band):
    spec, _, _ = band
    paint = plan_paint(load(_SVG), PALETTES["primary"], spec.outer_w,
                       spec.outer_l)
    _, _, text = _gcode(spec, paint, test_fit=1.0)
    head = text.split("\n\n")[0]
    for s in PALETTES["primary"].slots:
        assert f"T{s.index} {s.name}" in head


def test_the_purge_tower_cost_is_reported():
    spec = spec_for(section_res=0.9)
    paint = plan_paint(load(_SVG), PALETTES["primary"], spec.outer_w,
                       spec.outer_l)
    path, tower, _ = _gcode(spec, paint, test_fit=2.0)
    cost = tower_stats(spec, path, tower, PRINTERS["bambu-p1s-ams"],
                       FILAMENTS["pla"])
    assert cost["grams"] > 0
    assert cost["layers"] == tower.last - tower.first + 1


# --------------------------------------------------------------------------
# the command line
# --------------------------------------------------------------------------

def test_list_runs():
    assert cli.main(["--list"]) == 0


def test_check_only_writes_nothing(tmp_path):
    out = tmp_path / "nope.gcode"
    rc = cli.main(["--phone", "iphone-se-3", "--check-only", "--res", "0.9",
                   "--out", str(out)])
    assert rc == 0 and not out.exists()


def test_an_impossible_case_is_refused_at_the_command_line(tmp_path):
    out = tmp_path / "nope.gcode"
    rc = cli.main(["--phone", "iphone-15", "--wall", "0.4", "--res", "0.9",
                   "--out", str(out)])
    assert rc == 1 and not out.exists()


def test_the_whole_thing_end_to_end(tmp_path):
    out = tmp_path / "case.gcode"
    prev = tmp_path / "case.svg"
    art = tmp_path / "art.svg"
    art.write_text(_SVG)
    rc = cli.main(["--phone", "iphone-se-3", "--art", str(art),
                   "--palette", "primary", "--res", "0.9",
                   "--test-fit", "2.0", "--out", str(out),
                   "--preview", str(prev)])
    assert rc == 0
    text = out.read_text()
    assert text.startswith("; parametric iPhone case")
    assert "T0" in text and ";LAYER_CHANGE" in text
    assert prev.read_text().startswith("<svg")
