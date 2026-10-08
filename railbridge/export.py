"""Build the footbridge and write STEP (mm), GLB (metres, coloured), STL (mm) and previews:
python railbridge/export.py OUT_DIR"""
import os
import sys

import cadquery as cq
import trimesh

import footbridge as fb
import render

out = sys.argv[1]
fb.main(out)
render.main(out)
for name in ("Rail_Footbridge", "Rail_Footbridge_Site"):
    step = os.path.join(out, name + ".step")
    shape = cq.importers.importStep(step)
    solids = shape.solids().vals()
    print(name, "solids", len(solids), "all valid", all(s.isValid() for s in solids))
    asm = cq.Assembly.load(step)
    glb = os.path.join(out, name + ".glb")
    asm.export(glb)
    scene = trimesh.load(glb)
    scene.apply_scale(0.001)
    scene.export(glb)
    cq.exporters.export(shape, os.path.join(out, name + ".stl"), tolerance=2, angularTolerance=0.3)
    print(name, "glb extents m", [round(v, 2) for v in trimesh.load(glb).extents])
