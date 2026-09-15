#!/usr/bin/env python3
"""Round 2 emotion-differentiation fix (project board #39), after the round-1 blind critic
found NEW confusions once content/lust/silly/glare/shock were fixed: sad<->worried (near
identical downcast-tented-brow look), bore<->glare (both read as a warm-brown half-lidded
side-glance), angry<->evil_laugh (both a sharp downward brow with narrowed eyes).

Keeps sad, glare, angry as the anchor drawings; regenerates worried, bore, evil_laugh with
prompts that push each expression in a specific direction AWAY from its confused partner.

Run from core/: ../.venv/bin/python tools/char4_fix_eyes_round2.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tools.gemini_img as gi  # noqa: E402

SRC = "build/char4/src"
REF = f"{SRC}/reference.png"

PROMPTS = {
    "worried": (
        "Generate ONLY a sticker of this character's EYES AND EYEBROWS showing nervous ANXIETY/WORRY "
        "-- eyes WIDE OPEN and alert (NOT downcast or drooping), eyebrows raised UP and pulled together "
        "in the middle into a tight anxious knot (inner eyebrow corners raised HIGH, close together, "
        "creating worry creases), small nervous SWEAT DROP beside one eye, pupils slightly small and "
        "darting. This must look distinctly more wide-eyed, raised-brow and alert than a downcast, "
        "half-closed sad look -- the raised knotted brows, sweat drop, and open alert eyes (not tented "
        "downward-drooping ones) are the key identifying features, unmistakably different from sadness. "
        "Same art style as the reference (thick black outlines, flat colours), same eye/iris colour as "
        "the reference character. Absolutely NO skin around them, NO nose, NO face outline -- just the "
        "isolated eyes+eyebrows sticker. Solid flat pure green background (#00FF00)."
    ),
    "bore": (
        "Generate ONLY a sticker of this character's EYES AND EYEBROWS showing pure BOREDOM/DULLNESS -- "
        "eyelids drooping HEAVILY half-shut, pupils looking straight ahead in a flat, dull, half-asleep "
        "stare (NOT glancing sideways/suspiciously to one corner), eyebrows completely FLAT, LOW and "
        "relaxed with zero tension, mouth-corner-adjacent skin totally slack. The eyes must look straight "
        "ahead and dull/sleepy, distinctly different from a narrowed sideways suspicious glare -- no "
        "sideways pupil shift at all, just heavy tired half-closed lids looking blankly forward. Same "
        "art style as the reference (thick black outlines, flat colours), same eye/iris colour as the "
        "reference character. Absolutely NO skin around them, NO nose, NO face outline -- just the "
        "isolated eyes+eyebrows sticker. Solid flat pure green background (#00FF00)."
    ),
    "evil_laugh": (
        "Generate ONLY a sticker of this character's EYES AND EYEBROWS showing a SINISTER, MISCHIEVOUS "
        "evil laugh/scheming look -- both eyes squeezed into tight upward-curving HAPPY-SINISTER SLITS "
        "(like a delighted villain's chuckle, eyes almost closed and curved UP at the corners in a "
        "gleeful crescent shape, NOT a wide-open direct stare), eyebrows swept into a dramatic pointed "
        "high arch with a hooked flourish at the outer tip. The defining difference from a straightforward "
        "furious angry stare is that the eyes are nearly SHUT in a curved gleeful chuckle shape (crescent "
        "slits), not wide open and narrowed in direct rage. Same art style as the reference (thick black "
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
