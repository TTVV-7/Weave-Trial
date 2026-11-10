"""General 3D search for anything thinner than 0.8 mm (not only the named walls): voxels,
erode by R, grow back by R; what does not come back is thinner than 2R there.
Usage: python3 voxel_thin.py <part name> [voxel=0.05] [model=full|strip]"""
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from lib import cb

name = sys.argv[1]
H = float(sys.argv[2]) if len(sys.argv) > 2 else 0.05
which = sys.argv[3] if len(sys.argv) > 3 else "full"
parts, joints, info = cb.make_capybara() if which == "full" else cb.make_test()
m = parts[name]
bb = m.bounding_box()
lo = np.array(bb[:3]) - 3 * H
lo[2] = -3 * H
hi = np.array(bb[3:]) + 3 * H
n = np.ceil((hi - lo) / H).astype(int)
vol = np.zeros((n[2], n[1], n[0]), bool)
for k in range(n[2]):
    z = lo[2] + (k + 0.5) * H
    if z <= bb[2] or z >= bb[5]:
        continue
    acc = np.zeros((n[1], n[0]), bool)
    for p in m.slice(float(z)).to_polygons():
        p = (np.asarray(p) - lo[:2]) / H - 0.5
        im = Image.new("1", (int(n[0]), int(n[1])), 0)
        ImageDraw.Draw(im).polygon([tuple(q) for q in p], fill=1)
        acc ^= np.array(im, bool)
    vol[k] = acc
print(f"=== {which} / {name}: voxel {H} mm, grid {n.tolist()}, voxel volume {vol.sum() * H ** 3:.1f} mm3 (solid {m.volume():.1f})", flush=True)
edt = ndi.distance_transform_edt(vol, sampling=H).astype(np.float32) - H / 2
S = np.ones((3, 3, 3), bool)
for R in (0.4, 0.3):
    core = edt > R
    lab, k = ndi.label(core, structure=S)
    sizes = np.sort(ndi.sum(core, lab, range(1, k + 1)) * H ** 3)[::-1] if k else np.array([])
    big = sizes[sizes > 0.02]
    print(f"   minus a {R} mm skin: {len(big)} piece(s) over 0.02 mm3" + (f" [{', '.join(f'{s:.2f}' for s in big[:8])}]" if len(big) > 1 else ""))
    del lab
    far = ndi.distance_transform_edt(~core, sampling=H).astype(np.float32)
    thin = vol & (far > R + 1.5 * H)
    tl, tn = ndi.label(thin, structure=S)
    rows = []
    if tn:
        idx = np.arange(1, tn + 1)
        tv = ndi.sum(thin, tl, idx) * H ** 3
        pmax = ndi.maximum(far, tl, idx) - R
        emax = ndi.maximum(edt, tl, idx)
        sl = ndi.find_objects(tl)
        for i in np.argsort(-tv):
            if tv[i] < 0.01:
                break
            s = sl[i]
            x0, x1 = lo[0] + s[2].start * H, lo[0] + s[2].stop * H
            y0, y1 = lo[1] + s[1].start * H, lo[1] + s[1].stop * H
            z0, z1 = lo[2] + s[0].start * H, lo[2] + s[0].stop * H
            rows.append((tv[i], pmax[i], 2 * emax[i], x0, x1, y0, y1, z0, z1))
    print(f"   thinner than {2 * R:.1f}: {thin.sum() * H ** 3:.2f} mm3 in {tn} bits; listing those over 0.01 mm3 that reach more than 0.45 mm beyond the thick part ({sum(1 for r in rows if r[1] > 0.45)} of {len(rows)})")
    for tvv, pm, th, x0, x1, y0, y1, z0, z1 in rows:
        if pm > 0.45:
            print(f"      {tvv:7.3f} mm3, reaches {pm:.2f} mm past the thick part, thickest place in it {th:.2f} mm, x {x0:.2f}..{x1:.2f} y {y0:.2f}..{y1:.2f} z {z0:.2f}..{z1:.2f}")
    sys.stdout.flush()
