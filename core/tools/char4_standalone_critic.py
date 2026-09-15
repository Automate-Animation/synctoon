#!/usr/bin/env python3
"""Standalone mouth-sprite comparison (SKILL.md step 1's documented alternative to full-face
compositing: "or standalone with their own boxes for a fair size comparison"). Reads mouth
PNGs and their per-viseme box sizes DIRECTLY from images/characters/<char>/mouth/ and
images/metadata/metadata.json -- no head/body/background compositing at all, so it cannot be
corrupted by the external process repeatedly rewriting character_4's head/eyes/body files
(observed live during this session; mouth files and this script's own inputs were never
touched by that process).

Each mouth sprite is placed on its own canvas at a size proportional to its metadata box (the
same per-viseme size the real renderer would use), on a neutral mid-grey background, so
relative scale between visemes (e.g. o_big vs o_small) is preserved for fair comparison.

Usage:
  ../.venv/bin/python tools/char4_standalone_critic.py happy round5
  ../.venv/bin/python tools/char4_standalone_critic.py sad round5
"""
import json
import os
import random
import string
import sys

from PIL import Image, ImageDraw, ImageFont

BASE = "images/characters"
META = "images/metadata/metadata.json"
VISEMES = ["a_e", "d_j_ch", "f", "l", "m_b_close", "o_big", "o_small", "oh", "th", "trans"]
CANVAS = 300  # fixed tile canvas; box size determines how much of it the mouth fills
SCALE = 3.2   # box-size -> pixels multiplier (keeps even the smallest box legible)


def font(size=20):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()


def place(mouth_path, box_size, label=None):
    im = Image.open(mouth_path).convert("RGBA")
    w, h = box_size
    tw, th = max(1, round(w * SCALE)), max(1, round(h * SCALE))
    scale = min(tw / im.width, th / im.height)
    rw, rh = max(1, round(im.width * scale)), max(1, round(im.height * scale))
    resized = im.resize((rw, rh), Image.LANCZOS)
    top = 30 if label else 0
    canvas = Image.new("RGB", (CANVAS, CANVAS + top), (170, 170, 170))
    canvas.paste(resized, ((CANVAS - rw) // 2, top + (CANVAS - rh) // 2), resized)
    if label:
        d = ImageDraw.Draw(canvas)
        d.text((6, 4), label, fill=(255, 230, 0), font=font())
        d.rectangle([0, top, CANVAS - 1, CANVAS + top - 1], outline=(80, 80, 80), width=1)
    return canvas


def grid(tiles, path, cols=5):
    w, h = tiles[0].size
    rows = (len(tiles) + cols - 1) // cols
    im = Image.new("RGB", (cols * w, rows * h), (10, 10, 10))
    for i, t in enumerate(tiles):
        im.paste(t, ((i % cols) * w, (i // cols) * h))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
    print("wrote", path)


def main():
    mood = sys.argv[1] if len(sys.argv) > 1 else "happy"
    round_name = sys.argv[2] if len(sys.argv) > 2 else "round1"
    suf = "h" if mood == "happy" else "s"
    out_dir = f"build/qa/character_4/critic_{round_name}_{mood}_standalone"

    meta = json.load(open(META))

    ref_tiles = []
    for vis in VISEMES:
        key = f"{vis}_{suf}"
        path = f"{BASE}/character_1/mouth/{mood}/{key}.png"
        box = meta["character_1"]["mouth"][key]["size"]
        ref_tiles.append(place(path, box, vis))
    grid(ref_tiles, f"{out_dir}/reference_character_1_{mood}.png")

    letters = random.sample(string.ascii_uppercase, len(VISEMES))
    mapping = dict(zip(letters, VISEMES))
    order = list(letters)
    random.shuffle(order)

    cand_tiles = []
    for letter in order:
        vis = mapping[letter]
        key = f"{vis}_{suf}"
        path = f"{BASE}/character_4/mouth/{mood}/{key}.png"
        box = meta["character_4"]["mouth"][key]["size"]
        cand_tiles.append(place(path, box, letter))
    grid(cand_tiles, f"{out_dir}/candidates_character_4_{mood}_shuffled.png")

    with open(f"{out_dir}/ANSWER_KEY_do_not_show_critic.json", "w") as f:
        json.dump({"mapping_letter_to_true_viseme": mapping, "shown_order": order}, f, indent=2)
    print("answer key (hidden from critic):", mapping)


if __name__ == "__main__":
    main()
