#!/usr/bin/env python3
"""Targeted patch: re-key + tight-crop a SPECIFIC set of already-regenerated mouth src stickers
(build/char4/src/mouth_<v>_<s>.png) and drop them straight into
images/characters/character_4/mouth/<mood>/<key>.png -- WITHOUT touching head/eyes/body/
background files or their metadata boxes (those are the committed-good geometry; a full
build_character_4.py rebuild was found to shift head/eye/body anchors nondeterministically
and is NOT safe to rerun here). metadata.json mouth position/size entries are left exactly as
committed -- they describe the per-viseme DESIGN box, independent of the art file's own crop size.

Usage: ../.venv/bin/python tools/char4_patch_mouths.py f_h f_s l_h l_s th_h th_s a_e_s o_big_h o_big_s
"""
import sys

sys.path.insert(0, ".")
from tools.build_character_4 import load_keyed, tight_crop  # noqa: E402

SRC = "build/char4/src"
OUT = "images/characters/character_4"


def main():
    keys = sys.argv[1:]
    for key in keys:
        vis, suf = key.rsplit("_", 1)
        mood = "happy" if suf == "h" else "sad"
        src = f"{SRC}/mouth_{vis}_{suf}.png"
        crop = tight_crop(load_keyed(src), pad=2, label=key)
        out = f"{OUT}/mouth/{mood}/{key}.png"
        crop.save(out)
        print("patched", out, crop.size)


if __name__ == "__main__":
    main()
