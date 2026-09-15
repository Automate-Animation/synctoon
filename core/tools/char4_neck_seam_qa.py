#!/usr/bin/env python3
"""Render full-resolution (1920x1080 canvas) neck/collar-seam crops for EVERY character_4
body action (all 39, not just spot-checked ones) plus a few character_1 reference actions,
for a blind-critic pass on head-to-body attachment quality.

Run from core/: ../.venv/bin/python tools/char4_neck_seam_qa.py
Writes crops to build/qa/character_4/neck_seam/{character_4,character_1}/<action>.png
plus a labeled contact sheet build/qa/character_4/neck_seam_contact_sheet.png (for human review
only -- the blind critic agent gets the individual unlabeled crops, not this sheet).
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from image_manager.CharacterManager import CharacterManager  # noqa: E402
from utils.constants import body_actions  # noqa: E402

BASE = "images/characters"
META = "images/metadata/metadata.json"
OUT = "build/qa/character_4/neck_seam"

C4_ACTIONS = sorted(set(body_actions.values()))  # 39 actions, on-disk for character_4
C1_ACTIONS = ["explain", "achieve", "hi", "thinking", "winner", "idea"]  # reference bar sample


def neck_crop(mgr, meta, char, action, body_folder="body"):
    """Compose head+body+background at full res, then crop tightly to the neck/collar seam
    region using the same body-metadata head-anchor math char4_compare.py uses (mirrored,
    per-axis scaled to background size), independent of each body file's own on-disk size."""
    img, _ = mgr.get_character(char, "happy", action, "M", "happy_M", "classroom",
                                "happy", "m_b_close_h", 0)

    m = meta[char]
    body_dir = f"images/characters/{char}/body/{action}"
    bfile = sorted(f for f in os.listdir(body_dir) if f.endswith(".png"))[0]
    stem = os.path.splitext(bfile)[0]
    b0 = m["body"][stem]
    white_dir = f"images/characters/{char}/background/classroom"
    wfile = sorted(f for f in os.listdir(white_dir) if f.endswith(".png"))[0]
    wstem = os.path.splitext(wfile)[0]
    bg0 = m["background"][wstem]

    body_w, body_h = Image.open(f"{body_dir}/{bfile}").size
    sx, sy = bg0["size"][0] / body_w, bg0["size"][1] / body_h
    hx_raw, hy_raw = b0["position"]
    hw_raw, hh_raw = b0["size"]
    hw, hh = hw_raw * sx, hh_raw * sy
    hx_scaled = hx_raw * sx
    hx = bg0["size"][0] - hx_scaled - hw  # mirrored within the resized bg box
    hy = hy_raw * sy
    x0 = bg0["position"][0] + hx - 140
    y0 = max(0, bg0["position"][1] + hy - 20)
    # Neck/collar seam sits at the BOTTOM of the head box -- crop a band spanning from
    # near the TOP of the head (so a held prop/hand near the face reads in context, not as an
    # ambiguous disembodied blob) down through the shoulders/collar, generous width margin so
    # raised arms/hands stay visible relative to the torso instead of being cropped out.
    seam_y0 = y0
    seam_y1 = y0 + hh + 280  # well past the collar into the torso
    x1 = x0 + hw + 280
    seam_y0 = max(0, seam_y0)
    seam_y1 = min(img.height, seam_y1)
    x1 = min(img.width, x1)
    return img.crop((int(x0), int(seam_y0), int(x1), int(seam_y1)))


def label(im, text):
    canvas = Image.new("RGB", (im.width, im.height + 22), (25, 25, 25))
    canvas.paste(im.convert("RGB"), (0, 22))
    d = ImageDraw.Draw(canvas)
    d.text((4, 4), text, fill=(255, 255, 0), font=ImageFont.load_default())
    return canvas


def main():
    import json
    mgr = CharacterManager(BASE, META)
    meta = json.load(open(META))

    os.makedirs(f"{OUT}/character_4", exist_ok=True)
    os.makedirs(f"{OUT}/character_1", exist_ok=True)

    c4_crops = {}
    for a in C4_ACTIONS:
        crop = neck_crop(mgr, meta, "character_4", a)
        crop.save(f"{OUT}/character_4/{a}.png")
        c4_crops[a] = crop
        print("character_4", a, crop.size)

    c1_crops = {}
    for a in C1_ACTIONS:
        crop = neck_crop(mgr, meta, "character_1", a)
        crop.save(f"{OUT}/character_1/{a}.png")
        c1_crops[a] = crop
        print("character_1", a, crop.size)

    # contact sheet for human review (labeled) -- NOT what the blind critic sees
    tw, th = 220, 260
    tiles = []
    for a, im in c1_crops.items():
        t = im.convert("RGB").resize((tw, th))
        tiles.append(label(t, f"REF character_1/{a}"))
    for a, im in c4_crops.items():
        t = im.convert("RGB").resize((tw, th))
        tiles.append(label(t, f"c4/{a}"))
    cols = 6
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (th + 22)), (10, 10, 10))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * tw, (i // cols) * (th + 22)))
    sheet.save("build/qa/character_4/neck_seam_contact_sheet.png")
    print("wrote build/qa/character_4/neck_seam_contact_sheet.png")
    print(f"character_4 crops: {len(c4_crops)}  character_1 crops: {len(c1_crops)}")


if __name__ == "__main__":
    main()
