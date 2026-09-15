#!/usr/bin/env python3
"""Bake this pass's regenerated eye ART (build/char4/src/eyes_<emo>.png) into the CURRENT
committed sprite convention: metadata.json['character_4']['eyes'] already has one shared box
per emotion (position [81,38], size [146,144] as of this pass -- read live from metadata, never
hardcoded, so this stays correct if another concurrent pass changes the box again) -- so every
sprite file is pre-baked (letterboxed, uniform scale, no stretch) to exactly that box size, and
metadata itself is left untouched. This intentionally does NOT touch head/body/mouth files or
run build_character_4.py / fix_character_4_geometry.py (those own box/positioning mechanics,
out of scope for an eyes-only emotion-differentiation pass, and are being actively reworked by
concurrent sessions on other project-board tasks).

Run from core/: ../.venv/bin/python tools/char4_finalize_eyes.py <emo1> <emo2> ...
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image, ImageFilter  # noqa: E402
from tools.char4_key import key_green_adaptive  # noqa: E402
from tools.char3_lib import bbox  # noqa: E402

SRC = "build/char4/src"
CH = "images/characters/character_4"
META = "images/metadata/metadata.json"


def load_keyed(path):
    raw = Image.open(path)
    if raw.mode == "RGBA":
        import numpy as np
        a = np.asarray(raw.getchannel("A"))
        if (a == 0).any() and (a == 255).any():
            return raw
    return key_green_adaptive(raw.convert("RGB"))


def tight_crop(rgba, pad=4):
    b = bbox(rgba)
    x0, y0, x1, y1 = b
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(rgba.width, x1 + pad)
    y1 = min(rgba.height, y1 + pad)
    return rgba.crop((x0, y0, x1, y1))


def letterbox(im, w, h):
    s = min(w / im.width, h / im.height)
    r = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    c.paste(r, ((w - r.width) // 2, (h - r.height) // 2), r)
    return c


def main():
    emos = sys.argv[1:]
    meta = json.load(open(META))
    box = meta["character_4"]["eyes"]  # per-emotion box, may be shared or per-emotion
    for emo in emos:
        src = f"{SRC}/eyes_{emo}.png"
        crop = tight_crop(load_keyed(src), pad=2)
        w, h = box[emo]["size"]
        sprite = letterbox(crop, w, h)
        for folder in (emo, emo + "_2"):
            base = f"{CH}/eyes/{folder}"
            blink_dir = f"{base}/{folder}_blink"
            os.makedirs(blink_dir, exist_ok=True)
            for look in "LMR":
                sprite.save(f"{base}/{folder}_{look}.png")
                sprite.save(f"{blink_dir}/{folder}_{look}.png")
            # lids (02/03/04) are shared across every emotion folder and already sized correctly
            # by whichever pass last touched them -- only re-letterbox them into THIS box if
            # their current size doesn't already match (keeps them in sync, never distorts).
            for lid in ("02", "03", "04"):
                lp = f"{blink_dir}/{lid}.png"
                if os.path.exists(lp):
                    lid_im = Image.open(lp).convert("RGBA")
                    if lid_im.size != (w, h):
                        bb = lid_im.getbbox()
                        if bb:
                            lid_im = lid_im.crop(bb)
                        letterbox(lid_im, w, h).save(lp)
        print(f"finalized {emo}: sprite {sprite.size} into box {w}x{h}")


if __name__ == "__main__":
    main()
