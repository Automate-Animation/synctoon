#!/usr/bin/env python3
"""Build character_4 ('Sir Ahmed') from Gemini isolated-sticker sources in build/char4/src/.

Method: PARTS-AS-STICKERS (SKILL.md sec 3 / character_1 contract) -- every mouth/eye/body source is
an independently-generated sticker of ONLY that part (chroma-keyed, tight-cropped to its own alpha
bbox). NOT character_3's plate+fixed-box cut. Per-viseme mouth boxes and a single shared eye box are
reused directly from character_1's own numbers (same head canvas proportions, ~360x300).

Run from core/: ../.venv/bin/python tools/build_character_4.py
Re-runnable: pure post-processing of build/char4/src/*; no network calls.
"""
import argparse
import json
import os
import shutil
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.char3_lib import bbox  # noqa: E402
from tools.char4_key import key_green_adaptive as key_green, edge_hue_check  # noqa: E402
from utils.constants import body_actions, emotions, screen_mode  # noqa: E402

BUILD = "build/char4"
SRC = f"{BUILD}/src"
OUT = "images/characters/character_4"
CHAR1 = "images/characters/character_1"

HEAD_W, HEAD_H = 360, 300  # matches character_1's head canvas (359x293) closely, per SKILL.md step B

# character_1's own per-viseme boxes, AS FRACTIONS of ITS OWN head canvas (359x293) -- not
# absolute pixels. character_1's blank oval fills nearly the whole 359x293 canvas, but our
# generated head bust (hair + ears) tight-crops to a narrower, taller region WITHIN the 360x300
# canvas (see build_head's `ox,oy,nw,nh`) -- reusing character_1's ABSOLUTE pixel numbers landed
# the mouth box on the jaw/collar instead of under the nose (verified: full_a_e_h.png render).
# Fix: keep character_1's per-viseme size/position RATIOS (this is the real contract -- different
# box per viseme) but remap them onto our own face-art bounding box, not the full head canvas.
_C1_W, _C1_H = 359, 293
_MOUTH_BOX_C1 = {
    "a_e": ((110, 55), (60, 200)), "d_j_ch": ((110, 55), (60, 200)), "f": ((110, 55), (60, 200)),
    "l": ((110, 55), (60, 200)), "th": ((110, 55), (60, 200)),
    "trans": ((110, 45), (60, 200)),
    "m_b_close": ((110, 15), (60, 220)),
    "o_big": ((54, 54), (78, 198)), "oh": ((50, 50), (80, 200)),
    # o_small shrunk further vs character_1's own 40x40 (kept centred on the same point) -- a
    # harsh-critic pass on the first build found o_big/o_small read as "nearly identical size" at
    # our head scale; character_1's own 50-vs-40 ratio wasn't enough headroom once rescaled down
    # to our narrower face bbox, so widen the gap here instead of matching C1 literally.
    "o_small": ((34, 34), (88, 208)),  # centred on o_big's own centre (105,225), just smaller
}
_EYE_BOX_C1 = ((250, 150), (10, 30))  # size, position

MOUTH_BOX = None  # filled in by rescale_boxes_to_face(), once build_head() knows the face bbox
EYE_BOX = None


def rescale_boxes_to_face(ox, oy, nw, nh):
    """Map character_1's mouth/eye box ratios (defined against ITS OWN 359x293 canvas) onto our
    face art's actual bounding box (ox,oy,nw,nh) inside the 360x300 head canvas, instead of the
    full canvas -- this is what keeps the mouth centred under the nose regardless of how much
    hair/ear margin the generated head bust carries around the actual face."""
    global MOUTH_BOX, EYE_BOX

    def remap(size, pos):
        fx0, fy0 = pos[0] / _C1_W, pos[1] / _C1_H
        fw, fh = size[0] / _C1_W, size[1] / _C1_H
        return (round(fw * nw), round(fh * nh)), (round(ox + fx0 * nw), round(oy + fy0 * nh))

    MOUTH_BOX = {v: remap(*box) for v, box in _MOUTH_BOX_C1.items()}
    EYE_BOX = remap(*_EYE_BOX_C1)

VISEMES = ["a_e", "d_j_ch", "f", "l", "m_b_close", "o_big", "o_small", "oh", "th", "trans"]
HAPPY_MOODS = {"happy", "content", "sarcasm", "crazy", "evil_laugh", "lust", "silly"}

POSE_MAP = {
    "achieve": "winner", "answer": "you_pose", "explain": "explain", "me": "you_pose", "not_me": "not_me",
    "question": "question", "technical": "technical2", "why": "explain", "chilling": "chilling",
    "come": "come", "confuse": "confuse", "crazy": "crazy", "dancing": "dancing",
    "feeling_down": "feeling_down", "hi": "hi", "i": "you_pose", "idea": "idea", "idk": "idk",
    "joy": "joy", "jumping": "jumping", "kung_fu": "kung_fu", "love": "love", "meditation": "meditation2",
    "model": "model", "paper": "technical", "praying": "praying", "question2": "question",
    "running": "running", "search": "explain", "shy": "shy", "singing": "singing", "sneaky": "sneaky",
    "standing": "standing", "that": "you_pose", "thinking": "thinking", "this": "you_pose",
    "what": "question", "winner": "winner", "yeah": "yeah", "you": "you_pose",
}
# Round 4 (2026-09-15, project board #41, 3rd critic pass): idk/praying/sneaky/love/model/shy each
# got their OWN new generated pose after a critic pass found they collapsed onto thinking's
# chin-touch (idk, praying), confuse's neck-scratch (sneaky), hi's wave (love), idea's lightbulb
# (model), or a plain neutral standing pose (shy). "jumping" and "meditation" (-> meditation2) were
# REGENERATED under the same pose name because their round-2/3 art drifted back into a generic
# static pose that didn't read as jumping/meditating at all (see char4_generate.py POSES_ROUND4).
# Round 2 (2026-09-15, project board #41): crazy/yeah/meditation/come/chilling/not_me/technical
# each got their OWN new generated pose (see docs/CHARACTER_4_NOTES.md) after a blind critic pass
# flagged them as visually colliding with an unrelated action's pose (crazy/yeah were indistinguishable
# from winner's victory pose; meditation from praying; come from hi; chilling from standing; not_me
# from the generic pointing pose; technical from thinking's chin-touch). Every other action that
# still shares a pose (achieve/winner/jumping/kung_fu on "winner"; idk/praying/thinking on "thinking";
# answer/me/i/that/this/you on "you_pose"; shy/standing on "standing"; love/hi on "hi";
# confuse/sneaky on "confuse"; paper on "technical"; dancing/joy/running/singing on "joy") was
# reviewed by the same critic pass and judged plausible/defensible as-is -- left untouched.
# "you_pose" is the generated "pointing" sticker (file: body_pointing.png) -- reused for
# answer/me/not_me/i/that/this/you/you (pointing-forward gesture covers all of them, budget-conscious
# reuse in the spirit of character_3's own POSE_MAP).
POSE_FILE = {"you_pose": "pointing"}


def load_keyed(path):
    """Chroma-key a green-screen source, EXCEPT a PIL-fallback sticker (already has real alpha
    baked in -- detected by any fully-transparent pixel already present) which loads as-is."""
    raw = Image.open(path)
    if raw.mode == "RGBA":
        a = np.asarray(raw.getchannel("A"))
        if (a == 0).any() and (a == 255).any():
            return raw
    return key_green(raw.convert("RGB"))


FRINGE_LOG = []


def tight_crop(rgba, pad=4, label=""):
    b = bbox(rgba)
    x0, y0, x1, y1 = b
    x0 = max(0, x0 - pad); y0 = max(0, y0 - pad)
    x1 = min(rgba.width, x1 + pad); y1 = min(rgba.height, y1 + pad)
    out = rgba.crop((x0, y0, x1, y1))
    eh = edge_hue_check(out)
    if eh is not None and 32 <= eh <= 100:  # green-ish hue surviving on the edge ring
        FRINGE_LOG.append((label, round(eh, 1)))
    return out


def build_head(meta):
    src = load_keyed(f"{SRC}/head_blank.png")
    crop = tight_crop(src, pad=10, label="head")
    # uniform scale (never stretch) to fit inside HEAD_W x HEAD_H, then center on a transparent canvas
    scale = min(HEAD_W / crop.width, HEAD_H / crop.height) * 0.94
    nw, nh = int(crop.width * scale), int(crop.height * scale)
    resized = crop.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", (HEAD_W, HEAD_H), (0, 0, 0, 0))
    ox = (HEAD_W - nw) // 2
    oy = max(0, (HEAD_H - nh) // 2)  # vertically centred, clamped so a tall crop never clips off-canvas
    canvas.alpha_composite(resized, (ox, oy))
    for d in "LMR":
        p = f"{OUT}/head/{d}/head_{d}.png"
        os.makedirs(os.path.dirname(p), exist_ok=True)
        canvas.save(p)
    rescale_boxes_to_face(ox, oy, nw, nh)
    print("head canvas", (HEAD_W, HEAD_H), "art placed at", (ox, oy), "size", (nw, nh))


def build_mouths(meta):
    for vis in VISEMES:
        for mood, suf in (("happy", "h"), ("sad", "s")):
            key = f"{vis}_{suf}"
            path = f"{SRC}/mouth_{vis}_{suf}.png"
            if not os.path.exists(path):
                path = f"{SRC}/mouth_m_b_close_{suf}.png"
            crop = tight_crop(load_keyed(path), pad=2, label=key)
            size, pos = MOUTH_BOX[vis]
            os.makedirs(f"{OUT}/mouth/{mood}", exist_ok=True)
            crop.save(f"{OUT}/mouth/{mood}/{key}.png")
            meta["mouth"][key] = {"position": list(pos), "size": list(size)}


def crop_to_lid_blobs(rgba, margin=45):
    """lids_upper.png and lids_closed.png both came back as a WHOLE FACE (outer circle stroke
    included) instead of an isolated lids-only sticker (verified by direct inspection -- the
    prompt asked for "no other facial features" and Gemini drew a face outline anyway). Fix:
    find the two skin-tone lid blobs (NOT the black circle stroke, which has near-zero
    saturation) and crop to their combined bbox + margin, discarding the circle entirely."""
    a = np.asarray(rgba.getchannel("A")) > 128
    rgb = np.asarray(rgba.convert("RGB"))
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    skin = (h > 5) & (h < 25) & (s > 60) & (v > 100) & a
    n, lab, stats, _ = cv2.connectedComponentsWithStats(skin.astype(np.uint8))
    comps = sorted(range(1, n), key=lambda i: -stats[i][4])[:2]
    if not comps:
        return rgba  # nothing found, fall back to the whole (uncropped) sticker
    xs0 = min(stats[i][0] for i in comps)
    ys0 = min(stats[i][1] for i in comps)
    xs1 = max(stats[i][0] + stats[i][2] for i in comps)
    ys1 = max(stats[i][1] + stats[i][3] for i in comps)
    x0, y0 = max(0, xs0 - margin), max(0, ys0 - margin)
    x1, y1 = min(rgba.width, xs1 + margin), min(rgba.height, ys1 + margin)
    return rgba.crop((x0, y0, x1, y1))


def build_eyes(meta):
    size, pos = EYE_BOX
    half = tight_crop(load_keyed(f"{SRC}/lids_half.png"), pad=2, label="lids_half")
    closed_full = load_keyed(f"{SRC}/lids_closed.png")
    closed = tight_crop(crop_to_lid_blobs(closed_full), pad=2, label="lids_closed")
    upper_full = load_keyed(f"{SRC}/lids_upper.png")
    upper = tight_crop(crop_to_lid_blobs(upper_full), pad=2, label="lids_upper")
    for name in emotions.values():
        src = f"{SRC}/eyes_{name}.png"
        if not os.path.exists(src):
            src = f"{SRC}/eyes_happy.png"
        crop = tight_crop(load_keyed(src), pad=2, label=f"eyes_{name}")
        for folder in (name, name + "_2"):
            base = f"{OUT}/eyes/{folder}"
            blink_dir = f"{base}/{folder}_blink"
            os.makedirs(blink_dir, exist_ok=True)
            for look in "LMR":
                crop.save(f"{base}/{folder}_{look}.png")
                crop.save(f"{blink_dir}/{folder}_{look}.png")
            upper.save(f"{blink_dir}/02.png")   # upper lids only, closing
            closed.save(f"{blink_dir}/03.png")  # fully closed
            half.save(f"{blink_dir}/04.png")    # half open, reopening (character_1's own 02/03/04 semantics)
            meta["eyes"][folder] = {"position": list(pos), "size": list(size)}


def find_neck(rgba):
    """Topmost row with a wide-enough centred opaque run = collar/neck line (skips a raised hand)."""
    a = np.asarray(rgba.getchannel("A")) > 128
    h, w = a.shape
    cx = w / 2
    for y in range(h):
        row = a[y]
        xs = np.where(row)[0]
        if len(xs) < 1:
            continue
        run_w = xs.max() - xs.min()
        run_cx = (xs.max() + xs.min()) / 2
        if run_w > w * 0.14 and abs(run_cx - cx) < w * 0.25:
            return float(run_cx), float(y)
    ys, xs = np.where(a)
    return float(xs.mean()), float(ys.min())


def build_bodies(meta):
    done = set()
    for action in sorted(set(body_actions.values())):
        pose = POSE_MAP.get(action, "standing")
        fname = POSE_FILE.get(pose, pose)
        srcfile = f"{SRC}/body_{fname}.png"
        if not os.path.exists(srcfile):
            srcfile = f"{SRC}/body_standing.png"
        img = tight_crop(load_keyed(srcfile), pad=6, label=f"body_{action}")
        ncx, ncy = find_neck(img)
        bw, bh = img.size
        hw = int(bw * 0.30)
        hh = int(hw / (HEAD_W / HEAD_H))
        # tight-cropping to the body's own opaque bbox removes exactly the headroom the head
        # box needs to sit in (the neck line ends up a few px from row 0) -- pad the canvas
        # upward by the head box's own height + margin before placing the anchor, instead of
        # trying to fit the head box into space that was cropped away.
        pad_top = int(hh * 0.95)
        padded = Image.new("RGBA", (bw, bh + pad_top), (0, 0, 0, 0))
        padded.paste(img, (0, pad_top))
        ncy += pad_top
        hx = int(ncx - hw / 2)
        hy = int(ncy - hh * 0.88)
        d = f"{OUT}/body/{action}"
        os.makedirs(d, exist_ok=True)
        padded.save(f"{d}/{action}.png")
        meta["body"][action] = {
            "position": [hx, hy], "size": [hw, hh],
            "neck": [ncx, ncy],
        }
        done.add(action)
    print("bodies built:", len(done))


def build_backgrounds(meta):
    names = {m["name"] for m in screen_mode.values()} | {"gardan"}
    for name in sorted(names):
        src_dir = os.path.join(CHAR1, "background", "garden" if name == "gardan" else name)
        if not os.path.isdir(src_dir):
            continue
        srcs = [f for f in os.listdir(src_dir) if f.endswith(".png")]
        if not srcs:
            continue
        dst = os.path.join(OUT, "background", name, f"{name}.png")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(os.path.join(src_dir, srcs[0]), dst)
        # copy character_1's own metadata for this background name verbatim (same body scale target)
        c1meta = json.load(open("images/metadata/metadata.json"))["character_1"]["background"]
        key = os.path.splitext(srcs[0])[0]
        if key in c1meta:
            meta["background"][name] = c1meta[key]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata", default="images/metadata/metadata.json")
    a = ap.parse_args()
    meta = {"eyes": {}, "mouth": {}, "body": {}, "background": {}}
    build_head(meta)
    build_mouths(meta)
    build_eyes(meta)
    build_bodies(meta)
    build_backgrounds(meta)
    if FRINGE_LOG:
        print(f"FRINGE WARNING on {len(FRINGE_LOG)} sprites (green-ish hue survived on edge ring):")
        for label, hue in FRINGE_LOG:
            print(f"  {label}: edge hue {hue}")
    else:
        print("fringe check: clean on every sprite")
    all_meta = json.load(open(a.metadata))
    all_meta["character_4"] = meta
    json.dump(all_meta, open(a.metadata, "w"), indent=4)
    n = sum(len(fs) for _, _, fs in os.walk(OUT))
    print(f"built {n} files under {OUT}; metadata updated")


if __name__ == "__main__":
    main()
