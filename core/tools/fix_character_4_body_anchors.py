"""Fix the head-anchor bug from fix_character_4_geometry.py: it measured head size from
head_blank.png (a head-and-shoulders CLOSEUP) and applied it to body_*.png (FULL-BODY
shots) -- different framings, so the head box came out ~4x too big with a negative y.

Second attempt derived box_h per-pose from "neck_row - figure_top", which breaks on any
pose whose topmost alpha pixel is a raised hand or held prop (idea's lightbulb, paper's
raised fist) rather than empty air above an absent head -- fig_h then measures the gap
between neck and prop, not head height, giving a tiny or huge box.

Since Gemini was prompted "same framing and scale" for every body pose and character_qa
confirmed most poses (standing/explain/achieve/...) land correctly with ONE fixed box
size (measured: 360x300, i.e. exactly HEAD_W x HEAD_H) and a box-bottom that sits
~50px below the detected neck-skin-blob's top row, the robust fix is to stop deriving
box size from each sprite's own alpha bbox at all: use the fixed size + fixed overlap
for every pose, and only vary the box's (x) by that pose's own neck x-centre (poses do
lean/shift left-right) and (y) by its own neck y-row (poses differ slightly in scale/
vertical placement -- e.g. a seated pose sits lower). This is both simpler and more
robust than trying to re-derive scale per pose from noisy alpha geometry.
"""
import glob
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from char4_key import key_green_adaptive  # noqa: E402

CH = "images/characters/character_4"
META = "images/metadata/metadata.json"
HEAD_W, HEAD_H = 360, 300
NECK_BAND = (270, 400)   # absolute canvas rows, from the reference measurement
OVERLAP = 50             # box-bottom sits this far below the neck-blob's top row (measured
                          # across 6 already-correct poses: 46-53px, median ~50)


def skin_mask(rgb):
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    lo = np.array([3, 25, 60], dtype=np.uint8)
    hi = np.array([28, 200, 255], dtype=np.uint8)
    return cv2.inRange(hsv, lo, hi) > 0


def find_neck(rgba):
    """Largest plausible neck-shaped skin blob in the fixed absolute row band. Returns
    (x, y, w, h, area, cx) of its bbox, or None."""
    rgb = np.asarray(rgba.convert("RGB"))
    a = np.asarray(rgba)[:, :, 3] > 8
    mask = (skin_mask(rgb) & a).astype(np.uint8)
    band = np.zeros_like(mask)
    band[NECK_BAND[0]:NECK_BAND[1], :] = 1
    mask = mask & band
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    w_img = rgba.width
    best = None
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area < 400 or area > 20000:
            continue
        if bw < 20 or bw > 130 or bh < 15 or bh > 160:
            continue
        cx = x + bw / 2
        if not (0.25 * w_img < cx < 0.75 * w_img):
            continue
        if best is None or y < best[1]:
            best = (int(x), int(y), int(bw), int(bh), int(area), float(cx))
    return best


def main():
    all_meta = json.load(open(META))
    meta = all_meta["character_4"]
    meta["body"] = {}
    missing = []
    computed = {}
    for p in sorted(glob.glob(f"{CH}/body/*/*.png")):
        action = os.path.basename(os.path.dirname(p))
        im = Image.open(p).convert("RGBA")
        neck = find_neck(im)
        if neck is None:
            missing.append(action)
            continue
        _, ny, _, _, _, cx = neck
        by = ny + OVERLAP - HEAD_H
        bx = int(cx - HEAD_W / 2)
        meta["body"][action] = {
            "position": [bx, by], "size": [HEAD_W, HEAD_H], "neck": [int(cx), ny],
        }
        computed[action] = meta["body"][action]

    fallback = next(iter(computed.values())) if computed else None
    for action in missing:
        print("WARN no neck found for", action, "- reusing", fallback)
        if fallback:
            meta["body"][action] = dict(fallback)

    json.dump(all_meta, open(META, "w"), indent=4)
    bad = [a for a, v in meta["body"].items() if v["position"][0] < 0 or v["position"][1] < 0]
    print(f"wrote {len(meta['body'])} body anchors (fixed {HEAD_W}x{HEAD_H} box, overlap {OVERLAP})")
    print(f"negative origin: {bad}")
    print(f"missing neck detection (used fallback): {missing}")


if __name__ == "__main__":
    main()
