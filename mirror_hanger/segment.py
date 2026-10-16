"""Step 1 of the mirror hanger: split the logo into black / white / red.

    python3 mirror_hanger/segment.py path/to/logo.png [--out segmentation.png]

Writes a check image: original | segmented (flat colours) | the three masks.
The full model script (next step) imports segment() from here.
"""
import argparse
import sys

import cv2
import numpy as np

# --- tunables -------------------------------------------------------------
METHOD = "kmeans"        # "kmeans" or "hsv"
WORK_WIDTH = 1600        # px; image is resized to this width before segmenting
MORPH_KERNEL = 3         # px; open/close kernel (odd). Bigger = more cleanup
MIN_BLOB_AREA = 40       # px; specks smaller than this are dropped
# HSV mode only
RED_S_MIN, RED_V_MIN = 90, 70        # saturation / value floor for red
WHITE_S_MAX, WHITE_V_MIN = 60, 170   # white = low saturation, bright
# ---------------------------------------------------------------------------

BLACK, WHITE, RED = 0, 1, 2
NAMES = ("black", "white", "red")
PREVIEW_BGR = {BLACK: (25, 25, 25), WHITE: (245, 245, 245), RED: (40, 30, 210)}


def _kmeans_labels(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.2)
    _, lbl, centres = cv2.kmeans(lab, 3, None, crit, 5, cv2.KMEANS_PP_CENTERS)
    # OpenCV Lab: a* is offset by 128; red = largest a*, black = darkest of rest
    a = centres[:, 1] - 128
    red = int(np.argmax(a))
    rest = [i for i in range(3) if i != red]
    black = min(rest, key=lambda i: centres[i, 0])
    white = max(rest, key=lambda i: centres[i, 0])
    remap = np.empty(3, np.uint8)
    remap[[black, white, red]] = [BLACK, WHITE, RED]
    return remap[lbl.ravel()].reshape(img.shape[:2])


def _hsv_labels(img):
    h, s, v = cv2.split(cv2.cvtColor(img, cv2.COLOR_BGR2HSV))
    red = ((h <= 10) | (h >= 170)) & (s >= RED_S_MIN) & (v >= RED_V_MIN)
    white = (s <= WHITE_S_MAX) & (v >= WHITE_V_MIN) & ~red
    out = np.full(img.shape[:2], BLACK, np.uint8)
    out[white] = WHITE
    out[red] = RED
    return out


def _clean(mask):
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (MORPH_KERNEL, MORPH_KERNEL))
    m = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    n, cc, stats, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    keep = np.zeros(n, bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= MIN_BLOB_AREA
    return (keep[cc] * 255).astype(np.uint8)


def segment(path, method=METHOD):
    """Return (resized BGR image, {"white": mask, "red": mask}) with 0/255 masks."""
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        sys.exit(f"cannot read {path}")
    if img.ndim == 3 and img.shape[2] == 4:          # transparent -> black bg
        alpha = img[:, :, 3:] / 255.0
        img = (img[:, :, :3] * alpha).astype(np.uint8)
    elif img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    scale = WORK_WIDTH / img.shape[1]
    img = cv2.resize(img, None, fx=scale, fy=scale,
                     interpolation=cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA)
    labels = _kmeans_labels(img) if method == "kmeans" else _hsv_labels(img)
    masks = {"white": _clean(((labels == WHITE) * 255).astype(np.uint8)),
             "red": _clean(((labels == RED) * 255).astype(np.uint8))}
    masks["red"][masks["white"] > 0] = 0             # never overlap
    return img, masks


def preview(img, masks):
    flat = np.empty_like(img)
    flat[:] = PREVIEW_BGR[BLACK]
    flat[masks["white"] > 0] = PREVIEW_BGR[WHITE]
    flat[masks["red"] > 0] = PREVIEW_BGR[RED]
    black = 255 - np.maximum(masks["white"], masks["red"])
    tiles = [img, flat] + [cv2.cvtColor(m, cv2.COLOR_GRAY2BGR)
                           for m in (black, masks["white"], masks["red"])]
    labels = ["original", "segmented", "black mask", "white mask", "red mask"]
    pad = 10
    out = []
    for t, name in zip(tiles, labels):
        t = cv2.copyMakeBorder(t, 50, pad, pad, pad, cv2.BORDER_CONSTANT,
                               value=(128, 128, 128))
        cv2.putText(t, name, (pad + 5, 38), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                    (255, 255, 255), 2, cv2.LINE_AA)
        out.append(t)
    top = np.hstack(out[:2])
    bottom = np.hstack(out[2:])
    w = max(top.shape[1], bottom.shape[1])
    top = cv2.copyMakeBorder(top, 0, 0, 0, w - top.shape[1], cv2.BORDER_CONSTANT,
                             value=(128, 128, 128))
    bottom = cv2.resize(bottom, (w, int(bottom.shape[0] * w / bottom.shape[1])))
    return np.vstack([top, bottom])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--out", default="segmentation.png")
    ap.add_argument("--method", choices=("kmeans", "hsv"), default=METHOD)
    a = ap.parse_args()
    img, masks = segment(a.image, a.method)
    cv2.imwrite(a.out, preview(img, masks))
    total = img.shape[0] * img.shape[1]
    for k, m in masks.items():
        print(f"{k:6s} {100 * np.count_nonzero(m) / total:5.1f}% of pixels")
    print(f"wrote {a.out}")
