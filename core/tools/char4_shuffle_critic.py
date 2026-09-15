#!/usr/bin/env python3
"""Build the blind-critic materials for character_4 mouth QA (viseme axis).

For a given mood (happy|sad) and character (default character_4):
  - writes labelled reference tiles for character_1's 10 visemes (that mood)
  - writes SHUFFLED, randomly-lettered, UNLABELLED tiles for character_4's 10 visemes
  - writes a hidden answer key (letter -> true viseme) to a file the critic never sees

Usage:
  ../.venv/bin/python tools/char4_shuffle_critic.py happy round1
  ../.venv/bin/python tools/char4_shuffle_critic.py sad round1
Writes into build/qa/character_4/critic_<round>_<mood>/
"""
import json
import os
import random
import string
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from image_manager.CharacterManager import CharacterManager  # noqa: E402

BASE = "images/characters"
META = "images/metadata/metadata.json"
VISEMES = ["a_e", "d_j_ch", "f", "l", "m_b_close", "o_big", "o_small", "oh", "th", "trans"]


def font(size=20):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()


def headzoom(meta, char, im):
    m = meta[char]
    explain_dir = f"images/characters/{char}/body/explain"
    bfile = sorted(os.listdir(explain_dir))[0]
    stem = os.path.splitext(bfile)[0]
    b0 = m["body"][stem]
    white_dir = f"images/characters/{char}/background/white"
    wfile = sorted(os.listdir(white_dir))[0]
    wstem = os.path.splitext(wfile)[0]
    bg0 = m["background"][wstem]
    body_w, body_h = Image.open(f"{explain_dir}/{bfile}").size
    sx, sy = bg0["size"][0] / body_w, bg0["size"][1] / body_h
    hx_raw, hy_raw = b0["position"]
    hw_raw, hh_raw = b0["size"]
    hw, hh = hw_raw * sx, hh_raw * sy
    hx_scaled = hx_raw * sx
    hx = bg0["size"][0] - hx_scaled - hw
    hy = hy_raw * sy
    x0 = bg0["position"][0] + hx - 60
    y0 = max(0, bg0["position"][1] + hy - 40)
    return im.crop((int(x0), int(y0), int(x0 + hw + 120), int(y0 + hh + 90)))


def tile(im, label=None, tw=340, th=340):
    top = 30 if label else 0
    canvas = Image.new("RGB", (tw, th + top), (25, 25, 25))
    canvas.paste(im.convert("RGB").resize((tw, th)), (0, top))
    if label:
        d = ImageDraw.Draw(canvas)
        d.text((6, 4), label, fill=(255, 230, 0), font=font())
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
    char = sys.argv[3] if len(sys.argv) > 3 else "character_4"
    suf = "h" if mood == "happy" else "s"
    out_dir = f"build/qa/character_4/critic_{round_name}_{mood}"
    os.makedirs(out_dir, exist_ok=True)

    mgr = CharacterManager(BASE, META)
    meta = json.load(open(META))

    # reference: character_1, labelled, in canonical viseme order
    ref_tiles = []
    for vis in VISEMES:
        key = f"{vis}_{suf}"
        im, _ = mgr.get_character("character_1", mood, "explain", "M", f"{mood}_M", "white", mood, key, 0)
        z = headzoom(meta, "character_1", im)
        ref_tiles.append(tile(z, vis))
    grid(ref_tiles, f"{out_dir}/reference_character_1_{mood}.png")

    # candidates: char, shuffled, random letters, unlabelled
    letters = random.sample(string.ascii_uppercase, len(VISEMES))
    mapping = dict(zip(letters, VISEMES))
    order = list(letters)
    random.shuffle(order)

    cand_tiles = []
    for letter in order:
        vis = mapping[letter]
        key = f"{vis}_{suf}"
        im, _ = mgr.get_character(char, mood, "explain", "M", f"{mood}_M", "white", mood, key, 0)
        z = headzoom(meta, char, im)
        cand_tiles.append(tile(z, letter))
    grid(cand_tiles, f"{out_dir}/candidates_{char}_{mood}_shuffled.png")

    with open(f"{out_dir}/ANSWER_KEY_do_not_show_critic.json", "w") as f:
        json.dump({"mapping_letter_to_true_viseme": mapping, "shown_order": order}, f, indent=2)
    print("answer key (hidden from critic):", mapping)


if __name__ == "__main__":
    main()
