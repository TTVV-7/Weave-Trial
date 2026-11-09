"""3D erosion test on voxels: each part minus a skin of R mm must stay in one piece, and
whatever an 'opening' of radius R removes is a feature thinner than 2R.
Usage: python3 erode.py [model: full|test] [voxel mm]"""
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from common import cb

which = sys.argv[1] if len(sys.argv) > 1 else "full"
H = float(sys.argv[2]) if len(sys.argv) > 2 else 0.06
parts, joints, info = cb.make_capybara() if which == "full" else cb.make_test()

def voxels(m, h):
    bb = m.bounding_box()
    lo = np.array(bb[:3]) - 2 * h
    hi = np.array(bb[3:]) + 2 * h
    n = np.ceil((hi - lo) / h).astype(int)
    vol = np.zeros((n[2], n[1], n[0]), bool)
    for k in range(n[2]):
        z = lo[2] + (k + 0.5) * h
        if z <= bb[2] or z >= bb[5]:
            continue
        acc = np.zeros((n[1], n[0]), bool)
        for p in m.slice(float(z)).to_polygons():
            p = (np.asarray(p) - lo[:2]) / h - 0.5
            im = Image.new("1", (int(n[0]), int(n[1])), 0)
            ImageDraw.Draw(im).polygon([tuple(q) for q in p], fill=1)
            acc ^= np.array(im, bool)
        vol[k] = acc
    return vol, lo

S26 = np.ones((3, 3, 3), bool)
print(f"=== {which}: voxel {H} mm ===")
for name, m in parts.items():
    vol, lo = voxels(m, H)
    v_mm3 = vol.sum() * H ** 3
    edt = ndi.distance_transform_edt(vol, sampling=H) - H / 2        # distance to the surface, roughly
    line = [f"{name}: voxel volume {v_mm3:.1f} mm3 (solid {m.volume():.1f})"]
    for R in (0.2, 0.3, 0.4):
        core = edt > R
        lab, n = ndi.label(core, structure=S26)
        sizes = np.sort(ndi.sum(core, lab, range(1, n + 1)) * H ** 3)[::-1] if n else np.array([])
        big = sizes[sizes > 0.02]
        line.append(f"   minus {R} mm skin: {len(big)} piece(s) > 0.02 mm3" + (f" [{', '.join(f'{s:.2f}' for s in big[:6])}]" if len(big) > 1 else ""))
        if R in (0.2, 0.4):
            far = ndi.distance_transform_edt(~core, sampling=H)       # distance to the eroded core
            thin = vol & (far > R + 1.5 * H)
            tl, tn = ndi.label(thin, structure=S26)
            if tn:
                idx = range(1, tn + 1)
                tv = ndi.sum(thin, tl, idx) * H ** 3
                pmax = ndi.maximum(far, tl, idx) - R
                sl = ndi.find_objects(tl)
                rows = []
                for i in np.argsort(-pmax):
                    if pmax[i] < 0.75 or tv[i] < 0.01:
                        continue
                    s = sl[i]
                    zz, yy, xx = [(lo[a] + s[2 - a].start * H, lo[a] + s[2 - a].stop * H) for a in (2, 1, 0)][::-1][::-1]
                    x0, x1 = lo[0] + s[2].start * H, lo[0] + s[2].stop * H
                    y0, y1 = lo[1] + s[1].start * H, lo[1] + s[1].stop * H
                    z0, z1 = lo[2] + s[0].start * H, lo[2] + s[0].stop * H
                    rows.append(f"      thinner than {2*R:.1f}: {tv[i]:.3f} mm3, sticks {pmax[i]:.2f} mm beyond the thick part, "
                                f"x {x0:.2f}..{x1:.2f} y {y0:.2f}..{y1:.2f} z {z0:.2f}..{z1:.2f}")
                line.append(f"   opening {R}: {thin.sum()*H**3:.2f} mm3 thinner than {2*R:.1f} in {tn} bits; those reaching > 0.75 mm past the thick part: {len(rows)}")
                line += rows[:14]
    print("\n".join(line), flush=True)
