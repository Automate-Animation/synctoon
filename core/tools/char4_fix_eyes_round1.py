#!/usr/bin/env python3
"""Round 1 emotion-differentiation fix (project board #39): regenerate ONLY the eye stickers
the blind critic confused: happy/content/lust/silly (4-way near-duplicate cluster), angry/glare
(near-duplicate furrowed-brow pair), sad/shock (near-duplicate wide-eyed pair).

Keeps happy, angry, sad as the anchor drawings (already visually fine / used as the reference
other emotions must separate FROM) and regenerates content, lust, silly, glare, shock with
prompts that push each expression harder in a specific, distinct direction.

Run from core/: ../.venv/bin/python tools/char4_fix_eyes_round1.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tools.gemini_img as gi  # noqa: E402

SRC = "build/char4/src"
REF = f"{SRC}/reference.png"

STYLE = ("thick clean black outlines, flat cel-shaded colours (2-3 tone shading only), "
         "bold sticker-style digital illustration, same exact character design as the reference image")

PROMPTS = {
    "content": (
        "Generate ONLY a sticker of this character's EYES AND EYEBROWS showing calm, peaceful "
        "CONTENTMENT -- eyelids drooping HALF CLOSED in a relaxed, settled, satisfied way (like "
        "someone quietly at peace, NOT sleepy or bored, NOT wide open and alert like plain happiness). "
        "Eyebrows completely relaxed and LOW, no arch, no lift at all -- flatter and lower than a "
        "wide-awake happy look. The defining feature is the half-closed lids covering roughly the "
        "top third of each eye, giving a soft, gentle, settled expression. Looking straight ahead. "
        "Same art style as the reference (thick black outlines, flat colours), same eye/iris colour "
        "as the reference character. Absolutely NO skin around them, NO nose, NO face outline -- just "
        "the isolated eyes+eyebrows sticker. Solid flat pure green background (#00FF00)."
    ),
    "lust": (
        "Generate ONLY a sticker of this character's EYES AND EYEBROWS showing an exaggerated, "
        "cartoonish LUSTFUL/INFATUATED look -- eyes turned into a distinctly HEART shape (both pupils "
        "drawn as solid heart icons, cartoon-crush style), eyelids heavily HOODED/half-lowered from "
        "above, ONE eyebrow raised suggestively higher than the other in a flirty tilt. This must look "
        "unmistakably different from a plain content or happy look: the heart-shaped pupils and the "
        "asymmetric raised eyebrow are the key identifying features, drawn boldly and large. Looking "
        "straight ahead. Same art style as the reference (thick black outlines, flat colours). "
        "Absolutely NO skin around them, NO nose, NO face outline -- just the isolated eyes+eyebrows "
        "sticker. Solid flat pure green background (#00FF00)."
    ),
    "silly": (
        "Generate ONLY a sticker of this character's EYES AND EYEBROWS showing a goofy, SILLY, "
        "cross-eyed expression -- eyes clearly WALL-EYED/CROSS-EYED (pupils pointed in two different, "
        "mismatched directions, one looking inward/cross-eyed and the other looking off to the side or "
        "up), eyebrows WONKY and asymmetric -- one eyebrow arched high, the other flat or angled down -- "
        "for a lopsided, goofy, silly-faced look. This must be unmistakably different from a plain happy "
        "or content look: the crossed/mismatched pupils and mismatched eyebrows are the key identifying "
        "features. Same art style as the reference (thick black outlines, flat colours). Absolutely NO "
        "skin around them, NO nose, NO face outline -- just the isolated eyes+eyebrows sticker. Solid "
        "flat pure green background (#00FF00)."
    ),
    "glare": (
        "Generate ONLY a sticker of this character's EYES AND EYEBROWS showing a cold, suspicious "
        "GLARE -- eyes NARROWED into tight horizontal SLITS looking sideways/side-eye (both pupils "
        "shifted toward one corner, NOT looking straight ahead), eyebrows drawn as two FLAT, LOW, "
        "STRAIGHT horizontal lines pulled down close over the eyes (NOT a pointed V-shape meeting in "
        "the middle, NOT arched) -- a dirty, distrustful side-eye stare, distinctly different from a "
        "straight-ahead furious angry stare. The sideways-shifted narrow pupils and flat straight-line "
        "low brows are the key identifying features. Same art style as the reference (thick black "
        "outlines, flat colours), same eye/iris colour as the reference character. Absolutely NO skin "
        "around them, NO nose, NO face outline -- just the isolated eyes+eyebrows sticker. Solid flat "
        "pure green background (#00FF00)."
    ),
    "shock": (
        "Generate ONLY a sticker of this character's EYES AND EYEBROWS showing extreme SHOCK/SURPRISE "
        "-- eyes drawn as very large, perfectly round, WIDE OPEN circles with TINY small pupils and a "
        "large ring of visible white sclera all the way around each iris, eyebrows shot up EXTREMELY "
        "HIGH near the top of the forehead in two steep upward arcs, small motion/alarm lines beside "
        "each eyebrow. This must look distinctly more wide-eyed, round, and alarmed than a downcast, "
        "droopy-browed sad look -- the huge round white-ringed eyes and very high eyebrows are the key "
        "identifying features. Same art style as the reference (thick black outlines, flat colours), "
        "same eye/iris colour as the reference character. Absolutely NO skin around them, NO nose, NO "
        "face outline -- just the isolated eyes+eyebrows sticker. Solid flat pure green background "
        "(#00FF00)."
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
