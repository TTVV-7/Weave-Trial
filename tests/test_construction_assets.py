"""The construction-site assets: drawn to the published sizes, and printable.

The print files are what people pay for, so the tests that matter are the
ones on them: one connected piece, closed, flat on the bed, at the scale it
says. These need the optional CAD stack (cadquery, manifold3d, trimesh) and
are skipped without it.
"""

from __future__ import annotations

import math
import struct
import sys
from pathlib import Path

import pytest

pytest.importorskip("cadquery")
pytest.importorskip("manifold3d")
trimesh = pytest.importorskip("trimesh")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "construction_site"))

import build_assets as B  # noqa: E402
import numpy as np  # noqa: E402

import zipfile  # noqa: E402
import re  # noqa: E402

from cadkit import (FILAMENT_NAMES, IN, Finish, Model, box, count_bad_edges, export_print,  # noqa: E402
                    filament_of, prism, slots, weld_float32)


def asset(key):
    return next(a for a in B.all_assets() if a.key == key)


@pytest.mark.parametrize("axis", ["x", "y", "z"])
@pytest.mark.parametrize("winding", [1, -1])
def test_prism_is_never_inside_out(axis, winding):
    pts = [(0, 0), (40, 0), (40, 20), (0, 20)][::winding]
    assert prism(pts, axis, 5, 15).Volume() == pytest.approx(40 * 20 * 10)


def test_jersey_profile_is_the_nj_shape():
    pts = B.jersey_profile()
    ys = [y for y, _ in pts]
    zs = [z for _, z in pts]
    assert max(zs) == pytest.approx(32 * IN)
    assert max(ys) - min(ys) == pytest.approx(24 * IN)
    top = [y for y, z in pts if z == max(zs)]
    assert max(top) - min(top) == pytest.approx(6 * IN, abs=1)
    (y0, z0), (y1, z1) = pts[1], pts[2]
    assert math.degrees(math.atan2(z1 - z0, y0 - y1)) == pytest.approx(55)


def test_every_asset_has_a_unique_key_and_file_name():
    assets = B.all_assets()
    assert len({a.key for a in assets}) == len(assets)
    assert len({a.stem for a in assets}) == len(assets)


def test_set3_modules_follow_the_contract(capsys):
    folder = Path(B.HERE) / "set3"
    files = sorted(f.stem for f in folder.glob("*.py") if not f.stem.startswith("_"))
    loaded = B.load_module_assets("set3", 3)
    assert "skipping" not in capsys.readouterr().err
    assert sorted(a.key for a in loaded) == files
    order = (folder / "ORDER").read_text().split()
    assert len(order) == len(set(order)), "ORDER lists a key twice"
    assert set(files) <= set(order), "ORDER must list every set 3 module"
    for a in loaded:
        assert a.set == 3 and a.stem and a.title and callable(a.build)
        assert (Path(B.HERE) / f"{a.stem}.glb").exists(), f"{a.key} has not been built"


@pytest.mark.parametrize("key", ["jersey_barrier", "wheelbarrow", "type3_barricade", "traffic_drum", "trench_box",
                                 "water_filled_barrier"])
def test_print_file_is_one_closed_piece_flat_on_the_bed(key, tmp_path):
    m = Model(print_mode=True, scale=50)
    asset(key).build(m)
    stl = tmp_path / "part.stl"
    report = export_print(m, stl, 50)
    assert report["pieces"] == 1
    assert report["skipped_solids"] == 0
    assert report["nonmanifold_edges"] == 0

    data = stl.read_bytes()
    (count,) = struct.unpack_from("<I", data, 80)
    assert len(data) == 84 + 50 * count

    mesh = trimesh.load(stl)
    assert mesh.is_watertight
    assert mesh.volume > 0
    assert mesh.bounds[0][2] == pytest.approx(0, abs=1e-4)
    assert mesh.bounds[0][:2] == pytest.approx(-mesh.bounds[1][:2], abs=1e-3)   # centred


def test_welding_at_float32_collapses_edges_it_cannot_resolve():
    # two vertices 1e-9 mm apart are one point in float32: their triangle has to go
    v = np.array([[0, 0, 0], [1, 0, 0], [1 + 1e-9, 0, 0], [0, 1, 0]], float)
    t = np.array([[0, 1, 3], [1, 2, 3]])
    vw, tw = weld_float32(v, t)
    assert len(vw) == 3 and len(tw) == 1
    assert vw[tw[0]].tolist() == [[0, 0, 0], [1, 0, 0], [0, 1, 0]]   # the surviving triangle, same winding


def test_edge_count_flags_two_boxes_touching_on_a_line():
    tetra = np.array([[0, 1, 2], [0, 3, 1], [1, 3, 2], [2, 3, 0]])
    assert count_bad_edges(tetra) == 0
    assert count_bad_edges(tetra[:3]) == 3          # an open surface


def test_parts_touching_only_along_a_line_still_print_clean(tmp_path):
    # the case that left pinched edges in the print files: two blocks sharing one edge
    m = Model(print_mode=True, scale=50)
    m.add("a", None, box(0, 1000, 0, 1000, 0, 1000), box(1000, 2000, 1000, 2000, 0, 1000),
          box(0, 2000, 0, 2000, 900, 1100))
    report = export_print(m, tmp_path / "x.stl", 50)
    assert report["nonmanifold_edges"] == 0 and report["pieces"] == 1


def test_print_mode_thickens_thin_parts_to_a_printable_wall():
    shown, printed = Model(), Model(print_mode=True, scale=50, min_wall=0.8)
    assert shown.t(2.5) == 2.5
    assert printed.t(2.5) == pytest.approx(40)          # 0.8 mm at 1:50
    assert printed.t(300) == 300
    assert printed.r(5) == pytest.approx(20)


def test_barrier_prints_at_its_scale():
    m = Model(print_mode=True, scale=50)
    asset("jersey_barrier").build(m)
    m2 = Model(print_mode=True, scale=87)
    asset("jersey_barrier").build(m2)
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        r50 = export_print(m, Path(d) / "a.stl", 50)
        r87 = export_print(m2, Path(d) / "b.stl", 87)
    assert r50["size_mm"][2] == pytest.approx(32 * IN / 50, abs=0.05)
    assert r87["size_mm"][2] == pytest.approx(32 * IN / 87, abs=0.05)


def _painted(tmp_path, key):
    m = Model(print_mode=True, scale=50)
    asset(key).build(m)
    report = export_print(m, tmp_path / "x.stl", 50, painted=tmp_path / "x.3mf")
    with zipfile.ZipFile(tmp_path / "x.3mf") as z:
        xml = z.read("3D/3dmodel.model").decode()
    return report, xml


def test_painted_3mf_paints_every_triangle_with_one_of_four_slots(tmp_path):
    report, xml = _painted(tmp_path, "type3_barricade")
    codes = re.findall(r'paint_color="([0-9A-F]+)"', xml)
    assert len(codes) == xml.count("<triangle ") == report["triangles"]
    assert set(codes) <= {"4", "8", "0C", "1C"}
    names = [f.split(" ", 1)[1].rsplit(" #", 1)[0] for f in report["filaments"]]
    # the sign's lettering stays black and the rails stay striped
    assert {"Black", "White", "Safety orange"} <= set(names) and len(names) <= 4


def test_mixer_drum_stripes_survive_into_the_painted_print(tmp_path):
    report, _ = _painted(tmp_path, "concrete_mixer_truck")
    assert any("Safety orange" in f for f in report["filaments"])


def test_finishes_map_to_stock_filaments():
    assert FILAMENT_NAMES[filament_of(Finish((0.24, 0.33, 0.4), rough=0.05, alpha=0.45))] == "Black"   # glass
    assert FILAMENT_NAMES[filament_of(Finish((0.87, 0.89, 0.9), metal=1.0))] == "Silver grey"         # chrome
    assert FILAMENT_NAMES[filament_of(Finish((0.94, 0.68, 0.0)))] == "Construction yellow"


def test_slots_keep_a_small_saturated_colour_over_a_near_duplicate_grey():
    # white, light grey (nearly white) and silver at 50 mm2 each, orange at 15, a little black:
    # folding the grey into white is the smaller visible change, so the orange keeps its slot
    v = np.array([[0, 0, 0], [10, 0, 0], [0, 10, 0], [0, 0, 1], [6, 0, 1], [0, 5, 1], [0, 0, 2], [3, 0, 2], [0, 3, 2]],
                 float)
    t = np.array([[0, 1, 2], [0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 1, 2]])
    names = ["White", "Light grey", "Safety orange", "Black", "Silver grey"]
    labels = np.array([FILAMENT_NAMES.index(n) for n in names])
    _, kept = slots(v, t, labels)
    kept = [FILAMENT_NAMES[k] for k in kept]
    assert "Safety orange" in kept and "Black" in kept and len(kept) == 4
