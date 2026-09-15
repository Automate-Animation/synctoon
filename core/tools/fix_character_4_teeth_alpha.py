"""Real bug found by Kamal: mouth teeth render as invisible/washed-out. Root cause is in
tools/char4_key.py's key_green_adaptive(strip_white_halo=True): it flood-fills the
background through any near-white, low-saturation pixel to also catch a white
sticker-outline artifact Gemini sometimes drew -- but teeth are ALSO white/low-saturation,
and any single-pixel anti-aliasing gap in the black ink outline (near-universal on
line art) lets that flood-fill leak straight through the outline into the teeth, so the
whole (also near-white) teeth region gets absorbed into the same "background" component
and keyed to alpha=0. Confirmed: 18 of 20 mouth files have this -- every white teeth
pixel sits at alpha<3, not just faint, fully invisible.

Fix: on the CURRENT files (no need to re-run generation), find every alpha==0 connected
component that does NOT touch the canvas border -- the true background always touches
the border by definition, so any interior alpha==0 island is something that was wrongly
stripped -- and restore it to fully opaque. This is targeted and safe: it cannot touch
the real background, only enclosed islands the outline was supposed to protect.
"""
import glob

import cv2
import numpy as np
from PIL import Image


def repair(path):
    im = Image.open(path).convert("RGBA")
    a = np.array(im)
    transparent = a[:, :, 3] == 0
    n, lab = cv2.connectedComponents(transparent.astype(np.uint8), connectivity=4)
    border_labels = set(np.unique(lab[0, :])) | set(np.unique(lab[-1, :])) | \
        set(np.unique(lab[:, 0])) | set(np.unique(lab[:, -1]))
    border_labels.discard(0)
    interior = transparent & ~np.isin(lab, list(border_labels))
    if not interior.any():
        return 0
    a[:, :, 3] = np.where(interior, 255, a[:, :, 3])
    Image.fromarray(a, "RGBA").save(path)
    return int(interior.sum())


def main():
    total = 0
    for p in sorted(glob.glob("images/characters/character_4/mouth/*/*.png")):
        n = repair(p)
        if n:
            print(f"{p}: restored {n} interior px")
            total += 1
    print(f"repaired {total} mouth files")


if __name__ == "__main__":
    main()
