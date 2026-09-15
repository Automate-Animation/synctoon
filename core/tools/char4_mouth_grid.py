#!/usr/bin/env python3
"""Render ALL 20 mouth files (10 visemes x happy/sad) composed on a face, full resolution,
for character_1 and character_4, in two separate labelled grids per character.
Also crops a face-only zoom per tile so mouth shape/size is directly comparable.
Usage: ../.venv/bin/python tools/char4_mouth_grid.py
Writes: build/qa/character_4/mouth_grid_<char>_<mood>.png (4 files)
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from image_manager.CharacterManager import CharacterManager  # noqa: E402

BASE = "images/characters"
META = "images/metadata/metadata.json"
OUT_DIR = "build/qa/character_4"
VISEMES = ["a_e", "d_j_ch", "f", "l", "m_b_close", "o_big", "o_small", "oh", "th", "trans"]


def font():
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
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


def tile(im, label, tw=340, th=340):
    canvas = Image.new("RGB", (tw, th + 30), (25, 25, 25))
    canvas.paste(im.convert("RGB").resize((tw, th)), (0, 30))
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
    mgr = CharacterManager(BASE, META)
    meta = json.load(open(META))
    for char in ("character_1", "character_4"):
        for mood, suf in (("happy", "h"), ("sad", "s")):
            tiles = []
            for vis in VISEMES:
                key = f"{vis}_{suf}"
                im, _ = mgr.get_character(char, mood, "explain", "M", f"{mood}_M", "white", mood, key, 0)
                z = headzoom(meta, char, im)
                tiles.append(tile(z, f"{vis} ({mood})"))
            grid(tiles, f"{OUT_DIR}/mouth_grid_{char}_{mood}.png")


if __name__ == "__main__":
    main()
