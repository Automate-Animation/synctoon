#!/usr/bin/env python3
"""Round 4 emotion-differentiation fix (project board #39): the round-4 blind critic found
content/bore reading as near-identical (both a brown half-lowered lid over a calm iris -- direct
source comparison confirmed this is real, not a crop artifact), and crazy not reading as manic at
all (plain bulging eyes with only a small jagged brow flourish, easily read as calm/content-family).

Redesigns content as a warm CLOSED-EYE peaceful smile (upward crescents), fully different in KIND
from bore's half-open dead-stare droop. Pushes crazy toward mismatched pupil sizes / bulging wild
eyes so it can no longer be mistaken for a calm expression.

Run from core/: ../.venv/bin/python tools/char4_fix_eyes_round4.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tools.gemini_img as gi  # noqa: E402

SRC = "build/char4/src"
REF = f"{SRC}/reference.png"

PROMPTS = {
    "content": (
        "Generate ONLY a sticker of this character's EYES AND EYEBROWS showing warm, peaceful "
        "CONTENTMENT -- both eyes fully CLOSED in soft upward-curving happy crescent shapes (like a "
        "gentle satisfied smile drawn with the eyes, ^ ^ style, NOT half-open with visible iris/pupil "
        "at all), eyebrows relaxed and slightly raised in a soft, warm, settled way. This must be a "
        "CLOSED-EYE crescent shape, categorically different from a half-open droopy-lidded stare -- "
        "no visible eyeball, iris or pupil at all, just soft closed curved lines, small and gentle (not "
        "the sharp hooked villain-like crescent of a scheming laugh -- soft and warm instead). Same art "
        "style as the reference (thick black outlines, flat colours). Absolutely NO skin around them, "
        "NO nose, NO face outline -- just the isolated eyes+eyebrows sticker. Solid flat pure green "
        "background (#00FF00)."
    ),
    "crazy": (
        "Generate ONLY a sticker of this character's EYES AND EYEBROWS showing WILD, MANIC craziness "
        "-- the two eyes drawn DIFFERENT SIZES from each other (one eye bulging huge and wide open with "
        "a tiny pinprick pupil, the other eye small/squinted with a large dilated pupil) for an unhinged, "
        "unbalanced look, eyebrows wildly mismatched in angle (one shooting straight up, the other "
        "crooked/jagged like a lightning bolt), small motion/energy lines radiating around the eyes. "
        "This must look obviously unhinged and mismatched at a glance -- NOT two calm symmetric round "
        "eyes -- the defining feature is that the LEFT and RIGHT eyes are clearly different sizes/shapes "
        "from each other, exaggerated and wild. Same art style as the reference (thick black outlines, "
        "flat colours), same eye/iris colour as the reference character. Absolutely NO skin around "
        "them, NO nose, NO face outline -- just the isolated eyes+eyebrows sticker. Solid flat pure "
        "green background (#00FF00)."
    ),
}


def main():
    only = sys.argv[1:] or list(PROMPTS.keys())
    for emo in only:
        out = f"{SRC}/eyes_{emo}.png"
        if os.path.exists(out):
            os.remove(out)
        gi.gen(PROMPTS[emo], out, images=[REF])
        print("regenerated", out)


if __name__ == "__main__":
    main()
