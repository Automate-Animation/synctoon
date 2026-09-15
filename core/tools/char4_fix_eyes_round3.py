#!/usr/bin/env python3
"""Round 3 emotion-differentiation fix (project board #39): the round-3 blind critic (run on
an improved tight eyes-only crop) found happy/sad/sarcasm reading as three near-identical
"default round eyes, thin straight brow" drawings. Keeps happy as the plain anchor; pushes sad
and sarcasm each in their own clearly distinct direction.

Run from core/: ../.venv/bin/python tools/char4_fix_eyes_round3.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tools.gemini_img as gi  # noqa: E402

SRC = "build/char4/src"
REF = f"{SRC}/reference.png"

PROMPTS = {
    "sad": (
        "Generate ONLY a sticker of this character's EYES AND EYEBROWS showing genuine SADNESS -- "
        "eyes looking DOWNWARD (pupils shifted toward the bottom of the eye, gaze cast down, NOT "
        "looking straight ahead), eyebrows tilted into a classic sad 'tent' shape (inner corners "
        "pulled UP and together, outer corners drooping down), a single large glistening TEARDROP "
        "welling in the corner of one eye. This must NOT look like a plain neutral round-eyed face -- "
        "the downcast gaze, tented inner-up brows, and visible teardrop are the key identifying "
        "features that make it unmistakably sad rather than just a default expression. Same art style "
        "as the reference (thick black outlines, flat colours), same eye/iris colour as the reference "
        "character. Absolutely NO skin around them, NO nose, NO face outline -- just the isolated "
        "eyes+eyebrows sticker. Solid flat pure green background (#00FF00)."
    ),
    "sarcasm": (
        "Generate ONLY a sticker of this character's EYES AND EYEBROWS showing dry SARCASM -- ONE "
        "eyebrow (the character's right, image-left) raised HIGH and sharply arched in classic "
        "skeptical disbelief, the OTHER eyebrow (image-right) staying flat and low -- a strongly "
        "ASYMMETRIC single-raised-eyebrow smirk look. The eye under the raised brow is opened wider "
        "and more alert; the eye under the flat brow is narrowed/half-lidded in a knowing smirk. This "
        "must be strongly asymmetric left-vs-right (NOT the same shape mirrored on both sides like a "
        "plain neutral face) -- the one-eyebrow-cocked asymmetry is the single defining feature of "
        "sarcasm and must be obvious at a glance. Same art style as the reference (thick black "
        "outlines, flat colours), same eye/iris colour as the reference character. Absolutely NO skin "
        "around them, NO nose, NO face outline -- just the isolated eyes+eyebrows sticker. Solid flat "
        "pure green background (#00FF00)."
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
