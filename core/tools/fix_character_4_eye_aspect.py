"""Fix eye distortion: the previous pass forced every emotion's eye sprite into ONE
fixed 120x56 box regardless of its own drawn aspect ratio. The loader does a raw
`img.resize(box_size)` (stretch, not letterbox) -- Gemini's eye stickers have native
aspects from 1.49 (crazy) to 2.64 (evil_laugh), so stretching them all into one 2.14
aspect box visibly squashes/stretches the drawn eye shape per emotion.

Fix: pre-bake each emotion's sprite onto a shared-size transparent canvas via true
letterboxing (uniform scale, no stretch, centred) -- the FILE becomes a consistent
120x65 size with the art scaled-not-squashed inside it, so the loader's later resize
to the same box is a no-op and never distorts the drawn shape. Box height is capped at
65 (worst case that still clears the mouth top, ~130 with margin) so no emotion
overlaps the mouth regardless of its native aspect.
"""
import glob
import os

from PIL import Image

CH = "images/characters/character_4"
BOX_W, BOX_H = 120, 65


def letterbox(im, w, h):
    s = min(w / im.width, h / im.height)
    r = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    c.paste(r, ((w - r.width) // 2, (h - r.height) // 2), r)
    return c


def main():
    n = 0
    for p in glob.glob(f"{CH}/eyes/*/*.png") + glob.glob(f"{CH}/eyes/*/*/*.png"):
        im = Image.open(p).convert("RGBA")
        bb = im.getbbox()
        if bb:
            im = im.crop(bb)
        if im.size == (BOX_W, BOX_H):
            continue
        letterbox(im, BOX_W, BOX_H).save(p)
        n += 1
    print(f"letterboxed {n} eye sprites onto a shared {BOX_W}x{BOX_H} canvas (no stretch)")


if __name__ == "__main__":
    main()
