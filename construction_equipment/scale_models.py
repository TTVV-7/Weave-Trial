#!/usr/bin/env python3
"""Put the hi3D construction equipment models at real-world size.

    python construction_equipment/scale_models.py            # every model in MACHINES
    python construction_equipment/scale_models.py Wheel_Loader_18t

hi3D returns each model about one unit tall, centred on the origin. This wraps
the model in one new root node that scales it to metres, turns it to face +Z
(glTF's forward), centres it on X/Z and stands it on the ground at Y = 0. The
mesh, textures and materials are not touched: only the JSON chunk of the GLB is
rewritten, so the binary chunk stays byte-for-byte what hi3D produced.

Each machine is scaled by one dimension that does not depend on its pose (the
width over the tracks or bucket, or the overall length of a truck), taken from
typical published specs for that class. The other two dimensions follow from
the model's own proportions, and the script prints all three so they can be
checked. Running it again is safe: it replaces its own root node rather than
adding another.
"""

from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MARK = "construction_equipment/scale_models.py"

# name -> (dimension to fit, metres, turn about Y in degrees so the front faces +Z)
MACHINES = {
    "Crawler_Excavator_20t":        ("width", 2.99, 0),   # over 600 mm track shoes
    "Mini_Excavator_3.5t":          ("width", 1.74, 0),   # over tracks / dozer blade
    "Wheel_Loader_18t":             ("width", 2.95, 0),   # over the bucket
    "Crawler_Dozer_20t":            ("width", 3.30, 0),   # semi-U blade
    "Backhoe_Loader":               ("width", 2.35, 0),   # over the loader bucket
    "Skid_Steer_Loader":            ("width", 1.83, 0),   # 72 in bucket
    "Articulated_Dump_Truck_30t":   ("length", 10.3, 0),  # mirrors make its width unreliable
    "Concrete_Mixer_Truck":         ("length", 8.8, 0),   # 3-axle, 8-9 m3 drum
    "Vibratory_Soil_Compactor_12t": ("length", 5.85, 0),
    "Scissor_Lift_26ft":            ("length", 2.44, 0),  # stowed, deck retracted
}

JSON_CHUNK, BIN_CHUNK = 0x4E4F534A, 0x004E4942


def read_glb(path: Path) -> tuple[dict, bytes]:
    data = path.read_bytes()
    magic, version, _ = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF" or version != 2:
        raise ValueError(f"{path.name}: not a glTF 2.0 binary")
    n, kind = struct.unpack_from("<II", data, 12)
    if kind != JSON_CHUNK:
        raise ValueError(f"{path.name}: first chunk is not JSON")
    return json.loads(data[20:20 + n]), data[20 + n:]   # rest: BIN chunk, header and all


def write_glb(path: Path, gltf: dict, rest: bytes) -> None:
    js = json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    head = struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + len(rest))
    path.write_bytes(head + struct.pack("<II", len(js), JSON_CHUNK) + js + rest)


# --- 4x4 matrices as row-major lists, just enough for node transforms ---

def matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def node_matrix(node: dict):
    if "matrix" in node:                      # glTF stores column-major
        m = node["matrix"]
        return [[m[c * 4 + r] for c in range(4)] for r in range(4)]
    tx, ty, tz = node.get("translation", [0, 0, 0])
    x, y, z, w = node.get("rotation", [0, 0, 0, 1])
    sx, sy, sz = node.get("scale", [1, 1, 1])
    r = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    return [[r[0][0] * sx, r[0][1] * sy, r[0][2] * sz, tx],
            [r[1][0] * sx, r[1][1] * sy, r[1][2] * sz, ty],
            [r[2][0] * sx, r[2][1] * sy, r[2][2] * sz, tz],
            [0, 0, 0, 1]]


IDENTITY = [[float(i == j) for j in range(4)] for i in range(4)]


def bounds(gltf: dict, roots: list[int]):
    """World-space box of every mesh under `roots`, from the POSITION accessors'
    min/max (which glTF requires). Exact when the nodes carry no rotation."""
    lo, hi = [math.inf] * 3, [-math.inf] * 3

    def visit(i, parent):
        node = gltf["nodes"][i]
        m = matmul(parent, node_matrix(node))
        if "mesh" in node:
            for prim in gltf["meshes"][node["mesh"]]["primitives"]:
                acc = gltf["accessors"][prim["attributes"]["POSITION"]]
                a, b = acc["min"], acc["max"]
                for corner in ((x, y, z) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])):
                    p = [sum(m[r][c] * v for c, v in enumerate(corner)) + m[r][3] for r in range(3)]
                    for k in range(3):
                        lo[k], hi[k] = min(lo[k], p[k]), max(hi[k], p[k])
        for child in node.get("children", []):
            visit(child, m)

    for root in roots:
        visit(root, IDENTITY)
    return lo, hi


def scale_model(path: Path, fit: str, metres: float, turn_deg: float) -> dict:
    gltf, rest = read_glb(path)
    scene = gltf["scenes"][gltf.get("scene", 0)]
    roots = scene["nodes"]
    idx = len(gltf["nodes"])                  # where the new root goes
    # reuse the root this script added last time, so a re-run starts from hi3D's own
    if len(roots) == 1 and gltf["nodes"][roots[0]].get("extras", {}).get("scaled_by") == MARK:
        idx = roots[0]
        roots = gltf["nodes"][idx]["children"]
    lo, hi = bounds(gltf, roots)

    t = math.radians(turn_deg)
    c, s_ = math.cos(t), math.sin(t)
    # extents after turning about Y: X is width, Z is length (front at +Z)
    corners = [(x, z) for x in (lo[0], hi[0]) for z in (lo[2], hi[2])]
    xs = [c * x + s_ * z for x, z in corners]
    zs = [-s_ * x + c * z for x, z in corners]
    size = {"width": max(xs) - min(xs), "height": hi[1] - lo[1], "length": max(zs) - min(zs)}
    k = metres / size[fit]

    cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
    rx, rz = c * cx + s_ * cz, -s_ * cx + c * cz          # rotated centre
    root = {
        "name": path.stem,
        "translation": [-k * rx, -k * lo[1], -k * rz],
        "rotation": [0.0, math.sin(t / 2), 0.0, math.cos(t / 2)],
        "scale": [k, k, k],
        "children": roots,
        "extras": {"scaled_by": MARK, "fit": f"{fit} = {metres} m"},
    }
    if idx == len(gltf["nodes"]):
        gltf["nodes"].append(root)
    else:
        gltf["nodes"][idx] = root
    scene["nodes"] = [idx]
    write_glb(path, gltf, rest)
    return {d: v * k for d, v in size.items()}


def main(names: list[str]) -> int:
    names = names or list(MACHINES)
    for name in names:
        path = HERE / f"{name}.glb"
        if not path.exists():
            print(f"{name}: no {path.name}, skipped")
            continue
        fit, metres, turn = MACHINES[name]
        d = scale_model(path, fit, metres, turn)
        ft = {k: v / 0.3048 for k, v in d.items()}
        print(f"{name:30s} L {d['length']:5.2f} x W {d['width']:4.2f} x H {d['height']:4.2f} m"
              f"   ({ft['length']:4.1f} x {ft['width']:4.1f} x {ft['height']:4.1f} ft, fit {fit})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
