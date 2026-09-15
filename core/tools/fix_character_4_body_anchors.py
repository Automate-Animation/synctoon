"""Fix TWO real, visible bugs in character_4's head-to-body attachment, found by looking
at full-resolution rendered frames (not just the small QA contact-sheet thumbnails,
which hid both of these at their viewing scale):

BUG 1 -- gap on EVERY pose. `fix_head()` cuts the head sprite's neck at canvas row 232
(of a 360x300 canvas) -- the DRAWN content only fills rows 0-231, the rest of the 300px
box is transparent padding. The previous version of this script placed the box assuming
the full 300px was drawn (`by = neck_y + OVERLAP - HEAD_H`), so the actual visible
bottom edge of the head lands `HEAD_H - HEAD_DRAWN_BOTTOM` = 300-231 = 69px too high --
a visible gap between chin and collar on every single pose. Fixed: position from where
the head is ACTUALLY drawn to end, not the box's nominal height.

BUG 2 -- neck misdetected on poses with a raised hand near head height ("hi": waving,
"thinking": hand at chin). The skin-blob detector picked the hand as "the neck" because
it satisfied the same filters and happened to sit higher in the search band. Fixed:
instead of preferring the topmost qualifying blob, prefer the one whose y is closest to
the MEDIAN neck-row across all poses (the neck is consistently placed; a hand is not).
"""
import glob
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CH = "images/characters/character_4"
META = "images/metadata/metadata.json"
HEAD_W, HEAD_H = 210, 281  # cropped-to-content head canvas (see fix_character_4_head_crop.py) --
# re-measured 2026-09-15 after a full build_character_4.py rebuild; the exact bbox can shift
# slightly run-to-run of build_head()'s tight_crop+resize math, so this must match whatever
# fix_character_4_head_crop.py just printed, not a stale prior-session number.
NECK_BAND = (270, 400)   # absolute canvas rows to search
OVERLAP = 25             # the head's drawn bottom edge sits this far below the neck-blob top

# BUG 3 (found 2026-09-15 by a blind-critic pass on full-res neck-seam crops) -- 4 actions
# where the general "closest to median neck row" heuristic still picks the WRONG skin-blob:
# confuse/sneaky (hand raised to chin/ear, holding a mug) and paper/technical (raised fist
# off to the side) each have exactly 2 skin-blob candidates -- the real neck stump, and the
# raised hand/fist, which happens to sit CLOSER to the global median_y than the real neck
# does for these two specific poses (median_y=322; hand rows 314/313 beat neck rows 334/337).
# The x-centering (cx) is actually the more reliable signal here -- the real neck consistently
# lands at cx~502-505 across every other pose in this pose family, while the wrong hand/fist
# blob sits well off that (cx~439/394). Rather than generalize the heuristic further (risks
# regressing the 33 actions that already pick correctly via median-y), these 4 stubborn poses
# get a manually-measured override: (cx, y) of the correct neck-stump blob, read directly off
# `find_neck_candidates()`'s own output for each pose. confuse/sneaky share one body art file
# (POSE_MAP reuse) and so does paper/technical -- one override per underlying pose.
MANUAL_NECK_OVERRIDES = {
    "confuse": (503.5, 334),
    "sneaky": (503.5, 334),
    "paper": (505.5, 337),
    "technical": (505.5, 337),
}


def head_drawn_bottom():
    im = Image.open(f"{CH}/head/M/head_M.png").convert("RGBA")
    a = np.asarray(im)[:, :, 3] > 8
    rows = np.where(a.any(1))[0]
    return int(rows.max())  # 231 for the current head_M.png


def skin_mask(rgb):
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    lo = np.array([3, 25, 60], dtype=np.uint8)
    hi = np.array([28, 200, 255], dtype=np.uint8)
    return cv2.inRange(hsv, lo, hi) > 0


def find_neck_candidates(rgba):
    rgb = np.asarray(rgba.convert("RGB"))
    a = np.asarray(rgba)[:, :, 3] > 8
    mask = (skin_mask(rgb) & a).astype(np.uint8)
    band = np.zeros_like(mask)
    band[NECK_BAND[0]:NECK_BAND[1], :] = 1
    mask = mask & band
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
    w_img = rgba.width
    out = []
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        if area < 400 or area > 20000:
            continue
        if bw < 20 or bw > 130 or bh < 15 or bh > 160:
            continue
        cx = x + bw / 2
        if not (0.25 * w_img < cx < 0.75 * w_img):
            continue
        out.append((int(x), int(y), int(bw), int(bh), int(area), float(cx)))
    return out


def main():
    drawn_bottom = head_drawn_bottom()
    print(f"head drawn content ends at local row {drawn_bottom} (canvas {HEAD_H})")

    paths = sorted(glob.glob(f"{CH}/body/*/*.png"))
    per_action = {}
    for p in paths:
        action = os.path.basename(os.path.dirname(p))
        im = Image.open(p).convert("RGBA")
        cands = find_neck_candidates(im)
        per_action[action] = cands

    # first pass: median neck-row across poses that have exactly one unambiguous candidate
    unambiguous = [c[0][1] for c in per_action.values() if len(c) == 1]
    median_y = float(np.median(unambiguous)) if unambiguous else 320.0
    print(f"median neck row from {len(unambiguous)} unambiguous poses: {median_y:.0f}")

    all_meta = json.load(open(META))
    meta = all_meta["character_4"]
    meta["body"] = {}
    missing, corrected = [], []
    for action, cands in per_action.items():
        if not cands:
            missing.append(action)
            continue
        if action in MANUAL_NECK_OVERRIDES:
            cx, y = MANUAL_NECK_OVERRIDES[action]
            corrected.append(action + " (manual override)")
        else:
            # prefer the candidate closest to the reference neck row, not simply the topmost --
            # a raised hand near the head is usually further from the typical neck row
            x, y, bw, bh, area, cx = min(cands, key=lambda c: abs(c[1] - median_y))
            if len(cands) > 1 and y != min(c[1] for c in cands):
                corrected.append(action)
        by = y + OVERLAP - drawn_bottom
        bx = int(cx - HEAD_W / 2)
        meta["body"][action] = {
            "position": [bx, by], "size": [HEAD_W, HEAD_H], "neck": [int(cx), y],
        }

    fallback = next(iter(meta["body"].values())) if meta["body"] else None
    for action in missing:
        print("WARN no neck candidate for", action, "- reusing", fallback)
        if fallback:
            meta["body"][action] = dict(fallback)

    json.dump(all_meta, open(META, "w"), indent=4)
    bad = [a for a, v in meta["body"].items() if v["position"][0] < 0 or v["position"][1] < 0]
    print(f"wrote {len(meta['body'])} body anchors (drawn-bottom-aware, median-preferred neck pick)")
    print(f"negative origin: {bad}")
    print(f"missing neck detection (used fallback): {missing}")
    print(f"picked a non-topmost candidate (multi-blob poses, likely fixed): {corrected}")


if __name__ == "__main__":
    main()
