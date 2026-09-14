"""Geometry fix for character_4 (run from core/): the loader STRETCHES every sprite to its
metadata size, so every box must have the sprite's own aspect, be centred on the face, and
every body must share one canvas so poses render at one scale.

What this does (idempotent, re-runnable):
  1. head: cut the head sprite at mid-neck (drop shoulders), centre it; L/R = M
  2. eyes: per emotion, all 9 files on the M sprite's canvas (blink lids letterboxed);
     box = 60 % of face width, height from aspect, centred at 44 % of face height
  3. mouth: per file box, width by viseme class, height from aspect, centred at 77 % face height
  4. bodies: re-key the 1024x1024 sources WITHOUT tight-crop (uniform scale across poses),
     head box per body from the neck stump, size from the reference head height
  5. background: body pasted as 1000x1000 at (460,60) -> no stretch
"""
import glob
import json
import os
import shutil
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())
from build_character_4 import POSE_MAP  # noqa: E402
from char4_key import key_green_adaptive  # noqa: E402

CH = "images/characters/character_4"
META = "images/metadata/metadata.json"
SRC = "build/char4/src"
HEAD_W, HEAD_H = 360, 300
NECK_CUT = 232          # canvas row in head_M where the neck is cut (measured: narrowest at y=220)
FACE_TOP, FACE_BOT = 20, 215   # hair top / chin rows in the head sprite
FACE_CX = 180


def alpha(im):
    return np.asarray(im.convert("RGBA"))[:, :, 3] > 8


def letterbox(im, size):
    """Uniform-scale im to fit inside size, centred on a transparent canvas of exactly size."""
    w, h = size
    s = min(w / im.width, h / im.height)
    r = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    c.paste(r, ((w - r.width) // 2, (h - r.height) // 2), r)
    return c


# ---------------------------------------------------------------- 1. head
def fix_head():
    src = Image.open(f"{CH}/head/M/head_M.png").convert("RGBA")
    a = np.asarray(src).copy()
    a[NECK_CUT:, :, 3] = 0
    im = Image.fromarray(a)
    bb = im.getbbox()
    cx = (bb[0] + bb[2]) // 2
    out = Image.new("RGBA", (HEAD_W, HEAD_H), (0, 0, 0, 0))
    out.paste(im, (FACE_CX - cx, 0), im)
    for d in "LMR":
        for f in glob.glob(f"{CH}/head/{d}/*.png"):
            os.remove(f)
        out.save(f"{CH}/head/{d}/head_{d}.png")
    print("head: cut at", NECK_CUT, "bbox", out.getbbox())


# ---------------------------------------------------------------- 2. eyes
FACE_W = 200
EYE_W = int(0.60 * FACE_W)
EYE_CY = FACE_TOP + int(0.44 * (FACE_BOT - FACE_TOP))


def fix_eyes(meta):
    for emo_dir in sorted(glob.glob(f"{CH}/eyes/*/")):
        emo = os.path.basename(emo_dir.rstrip("/"))
        m = Image.open(f"{emo_dir}/{emo}_M.png").convert("RGBA")
        m = m.crop(m.getbbox())
        size = m.size
        for d in "LMR":
            letterbox(m, size).save(f"{emo_dir}/{emo}_{d}.png")
        blink = f"{emo_dir}/{emo}_blink"
        for f in ("02", "03", "04"):
            p = f"{blink}/{f}.png"
            if os.path.exists(p):
                lid = Image.open(p).convert("RGBA")
                lid = lid.crop(lid.getbbox())
                letterbox(lid, size).save(p)
        for d in "LMR":
            shutil.copy(f"{emo_dir}/{emo}_{d}.png", f"{blink}/{emo}_{d}.png")
        h = int(EYE_W * size[1] / size[0])
        meta["eyes"][emo] = {"size": [EYE_W, h], "position": [FACE_CX - EYE_W // 2, EYE_CY - h // 2]}
    print("eyes: box width", EYE_W, "centre y", EYE_CY)


# ---------------------------------------------------------------- 3. mouths
MOUTH_W = {  # fraction of face width per viseme class (character_1: wide 110/359, round 50/359, small 40/359)
    "a_e": 0.40, "d_j_ch": 0.38, "l": 0.38, "th": 0.38, "trans": 0.34,
    "f": 0.30, "m_b_close": 0.34, "o_big": 0.26, "oh": 0.18, "o_small": 0.18,
}
MOUTH_CY = FACE_TOP + int(0.77 * (FACE_BOT - FACE_TOP))


def fix_mouths(meta):
    meta["mouth"] = {}
    for p in sorted(glob.glob(f"{CH}/mouth/*/*.png")):
        stem = os.path.basename(p)[:-4]
        vis = stem[:-2]
        im = Image.open(p).convert("RGBA")
        im = im.crop(im.getbbox())
        im.save(p)
        w = int(MOUTH_W[vis] * FACE_W)
        h = max(6, int(w * im.height / im.width))
        cy = MOUTH_CY + (4 if vis == "m_b_close" else 0)
        meta["mouth"][stem] = {"size": [w, h], "position": [FACE_CX - w // 2, cy - h // 2]}
    print("mouth: centre y", MOUTH_CY, "boxes", len(meta["mouth"]))


# ---------------------------------------------------------------- 4. bodies
BODY_CANVAS = 1024
HEAD_CONTENT_ROWS = NECK_CUT - 10   # rows of real head art in the 300-row sprite (hair top ~10 .. neck cut)


def ref_head_height():
    """Height of head+hair in the 1024 reference (hair top .. neck) -> the head box scale."""
    ref = key_green_adaptive(Image.open(f"{SRC}/head_blank.png").convert("RGB"))
    a = alpha(ref)
    rows = a.sum(1)
    top = int(np.argmax(rows > 0))
    # neck = narrowest row in the lower half of the head art
    lo, hi = top + 150, top + 500
    seg = rows[lo:hi]
    neck = lo + int(np.argmin(np.where(seg > 0, seg, 10**9)))
    return top, neck


def fix_bodies(meta):
    top, neck = ref_head_height()
    head_h_ref = neck - top
    k = head_h_ref / HEAD_CONTENT_ROWS          # sprite px -> canvas px
    box_w, box_h = int(HEAD_W * k), int(HEAD_H * k)
    print(f"reference head: hair top {top}, neck {neck}, height {head_h_ref}; head box {box_w}x{box_h}")
    meta["body"] = {}
    poses = {}
    for p in sorted(glob.glob(f"{SRC}/body_*.png")):
        pose = os.path.basename(p)[5:-4]
        im = key_green_adaptive(Image.open(p).convert("RGB")).convert("RGBA")
        if im.size != (BODY_CANVAS, BODY_CANVAS):
            im = letterbox(im, (BODY_CANVAS, BODY_CANVAS))
        a = alpha(im)
        band = a[:, 440:584]                      # centre band: the neck stump, never a raised hand
        yn = int(np.argmax(band.any(1)))          # neck top row
        xs = np.where(a[yn + 6])[0]
        xs = xs[(xs > 380) & (xs < 644)]
        cx = int(xs.mean()) if len(xs) else 512
        # the sprite's neck-cut row must land ~30 px below the body's neck top
        y = int(yn + 30 - box_h * NECK_CUT / HEAD_H)
        poses[pose] = (im, {"position": [cx - box_w // 2, y], "size": [box_w, box_h], "neck": [cx, yn]})
    for action_dir in glob.glob(f"{CH}/body/*/"):
        action = os.path.basename(action_dir.rstrip("/"))
        pose = POSE_MAP.get(action, "standing")
        if pose not in poses:
            pose = "standing"
        for f in glob.glob(f"{action_dir}/*.png"):
            os.remove(f)
        im, md = poses[pose]
        im.save(f"{action_dir}/{action}.png")
        meta["body"][action] = md
    print("bodies:", len(meta["body"]), "actions from", len(poses), "poses")


# ---------------------------------------------------------------- 5. background
def fix_backgrounds(meta):
    for k, v in meta["background"].items():
        v["size"] = [1000, 1000]
        v["position"] = [460, 60]
        v["zoom_point"] = [960, 330]
    print("background: body box 1000x1000 @ (460,60)")


def main():
    all_meta = json.load(open(META))
    meta = all_meta["character_4"]
    fix_head()
    fix_eyes(meta)
    fix_mouths(meta)
    fix_bodies(meta)
    fix_backgrounds(meta)
    json.dump(all_meta, open(META, "w"), indent=4)
    print("metadata written")


if __name__ == "__main__":
    main()
