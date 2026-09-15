#!/usr/bin/env python3
"""Render all 14 base emotions (neutral 'trans' mouth) for one character as a labelled grid,
for the emotion-differentiation axis (project board task #39: character_4's content/happy and
glare/sarcasm read too close). Writes build/qa/character_4/emotion_grid_<char>_labelled.png
(labelled, for humans) and a matching build/qa/character_4/emotion_grid_<char>_crops/<LETTER>.png
set with a caller-supplied letter->emotion mapping (for the blind critic pass) plus the mapping
json (kept OUT of what the critic sees).

Usage:
    ../.venv/bin/python tools/emotion_diff_grid.py character_1
    ../.venv/bin/python tools/emotion_diff_grid.py character_4
    ../.venv/bin/python tools/emotion_diff_grid.py character_4 --shuffle roundN
"""
import json
import os
import random
import string
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from image_manager.CharacterManager import CharacterManager  # noqa: E402
from utils.constants import emotions  # noqa: E402

BASE = "images/characters"
META = "images/metadata/metadata.json"
OUTDIR = "build/qa/character_4"
HAPPY = {"happy", "content", "sarcasm", "crazy", "evil_laugh", "lust", "silly"}


def headzoom(char, im, meta):
    """Crop to the eyes/eyebrows/forehead region. Metadata-math crops (old approach) go stale
    the moment head/body geometry is reworked by a concurrent pass, so this instead finds the
    character's own silhouette via alpha/background-diff detection and crops a fixed-ratio
    band relative to its own top (hair) -- robust to whatever geometry constants are current,
    since every render in a batch uses the same fixed body='explain'/background='white' anyway.
    """
    import numpy as np
    a = np.asarray(im.convert("RGB"))
    bg = a[0, 0].astype(int)
    diff = np.abs(a.astype(int) - bg).sum(2)
    mask = diff > 20
    ys, xs = np.where(mask)
    y0 = ys.min()
    # sample the row at eye-level (measured empirically: ~50px below the hair top for this
    # rig's current head crop) for the face-width reference -- rows near the very top are
    # hair-silhouette-narrow, rows well below flare into ears/shoulders; y0+50 sits in between.
    row_xs = np.where(mask[y0 + 50])[0]
    hx0, hx1 = row_xs.min(), row_xs.max()
    top = y0 + 30
    bot = y0 + 105
    left = hx0 - 45
    right = hx1 + 45
    return im.crop((left, top, right, bot))


def fit_tile(im, w, h, bg=(20, 20, 20)):
    """Uniform-scale fit into (w, h) -- never distort the aspect ratio (that's exactly the
    stretch-not-letterbox bug this whole axis is about; the grid renderer must not repeat it)."""
    s = min(w / im.width, h / im.height)
    nw, nh = max(1, round(im.width * s)), max(1, round(im.height * s))
    r = im.convert("RGB").resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGB", (w, h), bg)
    canvas.paste(r, ((w - nw) // 2, (h - nh) // 2))
    return canvas


def render_face(mgr, meta, char, emo):
    mood = "happy" if emo in HAPPY else "sad"
    suf = "h" if mood == "happy" else "s"
    im, _ = mgr.get_character(char, emo, "explain", "M", f"{emo}_M", "white", mood, f"trans_{suf}", 0)
    return headzoom(char, im, meta)


def main():
    char = sys.argv[1]
    shuffle_tag = None
    rest = sys.argv[2:]
    for i, a in enumerate(rest):
        if a.startswith("--shuffle"):
            if "=" in a:
                shuffle_tag = a.split("=", 1)[1]
            elif i + 1 < len(rest):
                shuffle_tag = rest[i + 1]
            else:
                shuffle_tag = "round"

    os.makedirs(OUTDIR, exist_ok=True)
    mgr = CharacterManager(BASE, META)
    meta = json.load(open(META))

    emo_list = list(emotions.values())
    crops = {}
    for emo in emo_list:
        crops[emo] = render_face(mgr, meta, char, emo)

    # labelled grid (for humans / evidence) -- tight eye-region crop, larger tiles so lid/brow
    # subtlety (e.g. content's half-closed lids) survives downscaling into the grid montage
    tw, th = 320, 320
    cols = 5
    rows = (len(emo_list) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * tw, rows * (th + 24)), (20, 20, 20))
    d = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    for i, emo in enumerate(emo_list):
        r, c = divmod(i, cols)
        x, y = c * tw, r * (th + 24)
        canvas.paste(fit_tile(crops[emo], tw, th - 24), (x, y + 24))
        d.text((x + 4, y + 4), emo, fill=(255, 255, 0), font=font)
    labelled_path = f"{OUTDIR}/emotion_grid_{char}_labelled.png"
    canvas.save(labelled_path)
    print("wrote", labelled_path)

    if shuffle_tag:
        letters = list(string.ascii_uppercase[:len(emo_list)])
        random.shuffle(letters)
        mapping = dict(zip(letters, emo_list))  # letter -> emotion (secret)
        inv = {v: k for k, v in mapping.items()}

        crop_dir = f"{OUTDIR}/shuffled_{shuffle_tag}_{char}"
        os.makedirs(crop_dir, exist_ok=True)
        # unlabelled grid, letters only
        canvas2 = Image.new("RGB", (cols * tw, rows * (th + 24)), (20, 20, 20))
        d2 = ImageDraw.Draw(canvas2)
        order = letters  # grid position order == shuffled letters, not emotion order
        for i, letter in enumerate(order):
            emo = mapping[letter]
            r, c = divmod(i, cols)
            x, y = c * tw, r * (th + 24)
            canvas2.paste(crops[emo].convert("RGB").resize((tw, th - 24)), (x, y + 24))
            d2.text((x + 4, y + 4), letter, fill=(0, 255, 255), font=font)
            crops[emo].save(f"{crop_dir}/{letter}.png")
        unlabelled_path = f"{OUTDIR}/emotion_grid_{char}_shuffled_{shuffle_tag}.png"
        canvas2.save(unlabelled_path)
        map_path = f"{OUTDIR}/shuffle_map_{shuffle_tag}_{char}.json"
        with open(map_path, "w") as f:
            json.dump(mapping, f, indent=2)
        print("wrote", unlabelled_path)
        print("wrote (SECRET, do not show critic)", map_path)
        print("wrote per-letter crops in", crop_dir)


if __name__ == "__main__":
    main()
