"""Crop character_4's head sprite to its actual drawn content (bbox), instead of leaving
it padded inside a 360x300 canvas. The padding was the real cause of the head-floating-
above-the-body bug: `character_qa.py` (correctly) assumes a body's head box "bottom" is
where the head's drawn content ends, but the previous anchor script was measuring the
box's NOMINAL height (300px) while the drawn content actually stopped at row 231 -- 69px
of transparent padding sat below the chin, inside the box, pushing the visible head
89px above the neck it was supposedly anchored to.

Cropping to bbox removes the ambiguity structurally: after this, box height == drawn
content height, so "box bottom" and "visible chin" are the same row by construction.
Eye/mouth positions (which were authored relative to the old 360x300 canvas) are
shifted by the crop's top-left offset so they land in the same place on the face.
"""
import json

from PIL import Image

CH = "images/characters/character_4"
META = "images/metadata/metadata.json"


def main():
    im = Image.open(f"{CH}/head/M/head_M.png").convert("RGBA")
    bbox = im.getbbox()
    ox, oy, x1, y1 = bbox
    new_w, new_h = x1 - ox, y1 - oy
    print(f"head bbox {bbox} -> cropped size {new_w}x{new_h}, offset ({ox},{oy})")

    for d in "LMR":
        p = f"{CH}/head/{d}/head_{d}.png"
        Image.open(p).convert("RGBA").crop(bbox).save(p)

    all_meta = json.load(open(META))
    m = all_meta["character_4"]
    for k in m["eyes"]:
        pos = m["eyes"][k]["position"]
        m["eyes"][k]["position"] = [pos[0] - ox, pos[1] - oy]
    for k in m["mouth"]:
        pos = m["mouth"][k]["position"]
        m["mouth"][k]["position"] = [pos[0] - ox, pos[1] - oy]
    json.dump(all_meta, open(META, "w"), indent=4)
    print(f"shifted {len(m['eyes'])} eye boxes and {len(m['mouth'])} mouth boxes by (-{ox},-{oy})")
    print(f"NEW HEAD_W={new_w} HEAD_H={new_h} -- use these in fix_character_4_body_anchors.py")


if __name__ == "__main__":
    main()
