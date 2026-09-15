#!/usr/bin/env python3
"""Render labelled pose contact sheets for the body-pose-distinctness pass (project board #41).

1. character_4: EVERY body_action (39 names), composed on the classroom background at full
   1920x1080 resolution, downscaled per-tile, labelled ONLY with the action name (no pose-source
   info) -- this file is handed to a blind harsh-critic agent.
2. character_1: a curated ~15-action bar-reference sheet, same composition, for contrast.

Run from core/: ../.venv/bin/python tools/char4_pose_sheet.py [out_suffix]
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from image_manager.CharacterManager import CharacterManager  # noqa: E402
from utils.constants import body_actions  # noqa: E402

BASE = "images/characters"
META = "images/metadata/metadata.json"
TILE_W, TILE_H = 320, 220  # downscaled from the full 1920x1080 render, label bar included


def render_tile(mgr, char, action, mood="happy", vis="trans_h"):
    img, _ = mgr.get_character(char, mood, action, "M", f"{mood}_M", "classroom", mood, vis, 0)
    return img.convert("RGB")


def label_tile(img, label, w=TILE_W, h=TILE_H):
    body_h = h - 22
    thumb = img.resize((w, body_h))
    canvas = Image.new("RGB", (w, h), (20, 20, 20))
    canvas.paste(thumb, (0, 22))
    d = ImageDraw.Draw(canvas)
    d.rectangle([0, 0, w, 22], fill=(0, 0, 0))
    d.text((4, 4), label, fill=(255, 255, 0), font=ImageFont.load_default())
    return canvas


def grid(tiles, path, cols=6):
    if not tiles:
        return
    w, h = tiles[0].size
    rows = (len(tiles) + cols - 1) // cols
    im = Image.new("RGB", (cols * w, rows * h), (10, 10, 10))
    for i, t in enumerate(tiles):
        im.paste(t, ((i % cols) * w, (i // cols) * h))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
    print("wrote", path, im.size)


def build_character_4_sheet(mgr, out_path):
    actions = sorted(set(body_actions.values()))
    tiles = []
    for a in actions:
        img = render_tile(mgr, "character_4", a)
        tiles.append(label_tile(img, a))
    grid(tiles, out_path, cols=6)
    print(f"character_4 sheet: {len(actions)} actions")


BAR_ACTIONS = [
    "achieve", "explain", "question", "thinking", "idea", "hi", "standing",
    "winner", "feeling_down", "confuse", "joy", "dancing", "praying", "shy", "search",
]


def build_character_1_bar(mgr, out_path):
    tiles = []
    used = []
    for a in BAR_ACTIONS:
        d = f"{BASE}/character_1/body/{a}"
        if not os.path.isdir(d) or not os.listdir(d):
            continue
        img = render_tile(mgr, "character_1", a)
        tiles.append(label_tile(img, a))
        used.append(a)
    grid(tiles, out_path, cols=5)
    print(f"character_1 bar reference: {used}")


def main():
    suffix = sys.argv[1] if len(sys.argv) > 1 else "round1"
    mgr = CharacterManager(BASE, META)
    build_character_4_sheet(mgr, f"build/qa/character_4/pose_sheet_{suffix}.png")
    build_character_1_bar(mgr, "build/qa/character_1/pose_bar_reference.png")


if __name__ == "__main__":
    main()
