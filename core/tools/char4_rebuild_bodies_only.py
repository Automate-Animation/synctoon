#!/usr/bin/env python3
"""Rebuild ONLY character_4's body sprites + metadata['body'] key, leaving head/mouth/eyes/
background untouched on disk and in metadata.json. Needed because build_character_4.py's main()
rewrites the ENTIRE character_4 metadata key in one shot -- unsafe to run when another process may
be concurrently regenerating mouth/eye source art (a real race hit during the round-4 body-pose
pass on 2026-09-15: a concurrent viseme-fix session's mouth_th_h.png write got read mid-write and
corrupted images/characters/character_4/mouth/happy/th_h.png). This script only reads/writes the
body/* files and the metadata['body'] sub-key, so it is safe to run alongside mouth/eye work.
Run from core/: ../.venv/bin/python tools/char4_rebuild_bodies_only.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.build_character_4 import build_bodies  # noqa: E402

META = "images/metadata/metadata.json"


def main():
    all_meta = json.load(open(META))
    meta = {"body": {}}
    build_bodies(meta)
    all_meta["character_4"]["body"] = meta["body"]
    json.dump(all_meta, open(META, "w"), indent=4)
    print(f"rebuilt body-only: {len(meta['body'])} actions written to metadata['character_4']['body']")


if __name__ == "__main__":
    main()
