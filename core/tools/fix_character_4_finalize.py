"""Reconcile character_4's metadata after 4 axis-agents ran concurrently and clobbered
each other's box coordinates on the shared metadata.json (the eyes/emotion and mouth/
viseme axes each recomputed positions using a stale, pre-head-crop coordinate system,
undoing the earlier head_crop fix's -82,-12 shift and the eye letterbox-size fix; some
regenerated emotion sprites -- crazy, angry -- are still at the old 146x144 canvas while
others are at the correct 120x65).

Ground truth used here: the CURRENT actual file contents (this session's real art
improvements from all 4 axes must be preserved), and the CURRENT head canvas size
(196x220, confirmed still correctly cropped). Recomputes eye and mouth boxes from
scratch against that reality, rather than trying to re-derive which historical number
was "correct" -- multiple independent renumberings make that unrecoverable.
"""
import glob
import json
import os

from PIL import Image

CH = "images/characters/character_4"
META = "images/metadata/metadata.json"
HEAD_W, HEAD_H = 196, 220

EYE_BOX = (110, 58)      # shared eye box: width, height
EYE_POS = (43, 58)       # shared eye box position on the head canvas
MOUTH_CY = 160           # mouth box vertical centre
MOUTH_W_FRAC = {         # per-viseme width as a fraction of HEAD_W (character_1's own scheme)
    "a_e": 0.40, "d_j_ch": 0.38, "l": 0.38, "th": 0.38, "trans": 0.34,
    "f": 0.30, "m_b_close": 0.34, "o_big": 0.26, "oh": 0.18, "o_small": 0.18,
}


def letterbox(im, w, h):
    s = min(w / im.width, h / im.height)
    r = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    c.paste(r, ((w - r.width) // 2, (h - r.height) // 2), r)
    return c


def fix_eyes(meta):
    for emo_dir in sorted(glob.glob(f"{CH}/eyes/*/")):
        emo = os.path.basename(emo_dir.rstrip("/"))
        m_path = f"{emo_dir}/{emo}_M.png"
        m = Image.open(m_path).convert("RGBA")
        bb = m.getbbox()
        if bb:
            m = m.crop(bb)
        boxed = letterbox(m, *EYE_BOX)
        for d in "LMR":
            boxed.save(f"{emo_dir}/{emo}_{d}.png")
        blink = f"{emo_dir}/{emo}_blink"
        for f in ("02", "03", "04"):
            p = f"{blink}/{f}.png"
            if os.path.exists(p):
                lid = Image.open(p).convert("RGBA")
                bb2 = lid.getbbox()
                if bb2:
                    lid = lid.crop(bb2)
                letterbox(lid, *EYE_BOX).save(p)
        for d in "LMR":
            boxed.save(f"{blink}/{emo}_{d}.png")
        meta["eyes"][emo] = {"size": list(EYE_BOX), "position": list(EYE_POS)}
    print(f"eyes: {len(meta['eyes'])} emotions -> shared box {EYE_BOX} @ {EYE_POS}")


def fix_mouths(meta):
    for p in sorted(glob.glob(f"{CH}/mouth/*/*.png")):
        stem = os.path.basename(p)[:-4]
        vis = stem[:-2]
        im = Image.open(p).convert("RGBA")
        bb = im.getbbox()
        if bb:
            im = im.crop(bb)
            im.save(p)
        w = int(MOUTH_W_FRAC[vis] * HEAD_W)
        h = max(6, round(w * im.height / im.width))
        MAX_H = 66  # keep clear of the eye box bottom (58+58=116) with margin
        if h > MAX_H:
            h = MAX_H
            w = max(10, round(h * im.width / im.height))
        cy = MOUTH_CY + (4 if vis == "m_b_close" else 0)
        meta["mouth"][stem] = {
            "size": [w, h], "position": [(HEAD_W - w) // 2, cy - h // 2],
        }
    print(f"mouth: {len(meta['mouth'])} files, centre y {MOUTH_CY}")


def main():
    all_meta = json.load(open(META))
    meta = all_meta["character_4"]
    fix_eyes(meta)
    fix_mouths(meta)
    json.dump(all_meta, open(META, "w"), indent=4)
    print("metadata written")


if __name__ == "__main__":
    main()
