"""The real bug behind Kamal's "head looks off / looking different places" report:
not a per-asset art problem, but the COORDINATION metadata itself. Audited every
body[*] box in metadata.json and found 37 of 39 poses size the head box at aspect
ratio ~1.20 (width/height) while the actual head sprite is 196x220 = aspect 0.891 --
every one of those 37 poses stretches the head wider and flatter than it is drawn,
because whichever fix pass touched each pose computed box width and height from two
different, uncoordinated measurements (a skin-blob's own bounding box, rather than
the head sprite's real proportions) instead of deriving width from height by ONE
fixed ratio. Only the 2 poses (hi, thinking) that were manually re-measured by hand
happened to get the right aspect, because that fix explicitly used HEAD_W/HEAD_H.

The fix: ONE coherent rule for all 39 poses, applied uniformly --
  box_h stays whatever this pose's own calibration already determined (that part
    reflects a real measurement: how big the head appears in THIS pose's own
    artwork/framing, which legitimately varies pose to pose)
  box_w is ALWAYS box_h * (HEAD_W/HEAD_H) -- never independently sized
  box stays centred on the same neck x/y anchor already recorded
This is "consistent" in the sense the user means: not identical numbers, but one
same rule producing every number.
"""
import json

META = "images/metadata/metadata.json"
HEAD_W, HEAD_H = 196, 220
HEAD_ASPECT = HEAD_W / HEAD_H


def main():
    d = json.load(open(META))
    m = d["character_4"]
    fixed = []
    for action, v in m["body"].items():
        w, h = v["size"]
        aspect = w / h
        if abs(aspect - HEAD_ASPECT) <= 0.01:
            continue  # already correct (hi, thinking)
        cx = v["position"][0] + w / 2
        cy_bottom = v["position"][1] + h  # keep the same bottom edge (same overlap/anchor)
        new_w = round(h * HEAD_ASPECT)
        new_x = round(cx - new_w / 2)
        v["size"] = [new_w, h]
        v["position"] = [new_x, cy_bottom - h]
        fixed.append((action, w, new_w))
    json.dump(d, open(META, "w"), indent=4)
    print(f"fixed aspect on {len(fixed)}/{len(m['body'])} body poses (width only, height/anchor unchanged)")
    for a, old_w, new_w in fixed[:5]:
        print(f"  {a}: width {old_w} -> {new_w}")


if __name__ == "__main__":
    main()
