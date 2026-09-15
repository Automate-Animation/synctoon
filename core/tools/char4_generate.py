#!/usr/bin/env python3
"""Generate character_4 ('Sir Ahmed') Gemini source stickers into build/char4/src/.
Route: parts-as-stickers (SKILL.md sec 3) -- NOT plate+fixed-box-cut (that was character_3's mistake).
Every call passes the style reference PNG as inlineData + repeats the palette hex codes.
Re-runnable: skips any output file that already exists. Logs to build/char4/calls.log (separate from char3).
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tools.gemini_img as gi  # noqa: E402

SRC = "build/char4/src"
REF = f"{SRC}/reference.png"
LOG = "build/char4/calls.log"

PALETTE = ("kurta light-blue #A9D6E5 with #6FB6D9 shading, navy waistcoat #1E2A4A, "
           "dark grey trousers #3B3F47, warm tan skin #C98E5E, short black hair #1A1A1A")

STYLE = ("thick clean black outlines, flat cel-shaded colours (2-3 tone shading only), "
         "bold sticker-style digital illustration, same exact character design as the reference image")


def _log(name, ok, note=""):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(f"{time.strftime('%H:%M:%S')}\t{name}\t{'ok' if ok else 'FAIL'}\t{note}\n")


def gen_once(out, prompt, images=(REF,)):
    if os.path.exists(out):
        print("skip (exists)", out)
        return out
    try:
        gi.gen(prompt, out, images=list(images))
        _log(out, True)
        print("OK", out)
    except Exception as ex:  # noqa: BLE001
        _log(out, False, str(ex)[:200])
        print("FAIL", out, ex)
    return out


VISEME_DESC = {
    # NOTE: mood (happy/sad) is applied separately via mood_word below -- these descriptions
    # describe SHAPE ONLY and must not bake in a smile/frown, or the mood modifier fights the
    # shape description (round-1 bug: a_e's "smile"/"corners pulled up" made the sad variant
    # read as happy regardless of the sad mood_word appended after it).
    "a_e": ("mouth open very wide in a large vocal opening, both upper and lower rows of teeth "
            "clearly visible, mouth held open wide as if singing a loud vowel sound"),
    "d_j_ch": "upper and lower teeth held together and touching, lips parted just enough to show the teeth line, relaxed jaw",
    "f": ("EXTREME CLOSE-UP of a lip-biting shape, like saying the letter F: ONLY the upper "
          "front teeth are visible, resting down and pressing firmly onto the lower lip. "
          "The LOWER TEETH MUST NOT BE VISIBLE AT ALL -- the lower lip covers them completely. "
          "This is NOT a smile and NOT a grin -- do not draw two rows of teeth. Draw exactly "
          "ONE row of upper teeth touching the pink lower lip, mouth corners neutral (not "
          "upturned), a distinctly asymmetric bite silhouette, unmistakably different from a "
          "symmetric open smile"),
    "l": ("mouth open, and INSIDE the dark mouth cavity there is a separate raised pink tongue "
          "shape shaped like an upside-down V or a small pink triangle/hump, curling UP AND "
          "BACK to touch the ridge behind the upper front teeth. The tongue must be drawn as "
          "its own clearly-outlined raised shape floating in the upper-middle of the mouth "
          "cavity, with visible dark empty space around/below it -- NOT a flat pink lower lip "
          "filling the whole bottom of the mouth. Think of the tongue-tip emoji shape."),
    "m_b_close": "lips fully closed pressed together, a simple closed line, no teeth visible",
    "o_big": ("mouth wide open in a perfectly round, large dark oval hole shape like a shocked "
               "'O', lips form a big round ring shape, no teeth visible, exaggerated roundness"),
    "o_small": "mouth open in a small round pursed 'o' shape like whistling, noticeably smaller and more puckered than a big O",
    "oh": "mouth open in a tall vertical oval shape, narrower side to side than top to bottom, some teeth visible at the top",
    "th": ("mouth open just enough that a flat pink tongue tip STICKS OUT PAST THE LIPS, "
           "protruding forward and DOWNWARD over the lower lip edge, clearly extending OUTSIDE "
           "the mouth silhouette -- like the classic 'blep' or tongue-out emoji. The pink tongue "
           "tip must visibly overlap/extend past the bottom lip's outline, sticking out of the "
           "mouth, not merely visible inside a dark cavity. Upper teeth barely visible above it."),
    "trans": "mouth relaxed, lips slightly parted, small neutral half-open gap, no teeth or tongue emphasized, resting position",
}

EMOTIONS = ["happy", "sad", "angry", "bore", "content", "glare", "sarcasm", "worried",
            "crazy", "evil_laugh", "lust", "shock", "silly", "spoked"]


def build_reference():
    prompt = open("build/char4/prompt_reference.txt").read()
    if not os.path.exists(REF):
        if os.path.exists(f"{SRC}/reference_raw.png"):
            os.rename(f"{SRC}/reference_raw.png", REF)
        else:
            gen_once(REF, prompt, images=())
    print("reference ready:", os.path.exists(REF))


def build_head():
    prompt = (f"Edit this character sticker: crop to HEAD AND NECK ONLY (shoulders barely visible), "
              f"then REMOVE the eyes, eyebrows and mouth completely -- replace that area with smooth "
              f"plain skin, same {PALETTE.split(',')[3].strip()} tone, keep the nose, keep the hairstyle "
              f"and hair colour, keep ears. A perfectly blank featureless face from eyebrow-line to chin "
              f"except the nose. {STYLE}. Solid flat pure green background (#00FF00), no shadow.")
    gen_once(f"{SRC}/head_blank.png", prompt)


def build_mouths():
    for vis, desc in VISEME_DESC.items():
        for mood, suf in (("happy", "h"), ("sad", "s")):
            mood_word = ("cheerful happy mood, mouth corners turned UP" if suf == "h" else
                         "sad, unhappy, downturned mood -- mouth corners turned DOWN, flatter drooping lower lip, "
                         "NOT smiling, NOT cheerful")
            prompt = (f"Generate ONLY a sticker of this character's MOUTH -- lips, teeth and tongue only, "
                      f"nothing else. {desc}. {mood_word}. Skin/lip colour matches the reference character's "
                      f"warm tan skin tone and natural lip colour. Absolutely NO skin patch around it, NO nose, "
                      f"NO cheeks, NO chin outline -- just the isolated mouth shape as a small sticker, thick "
                      f"clean black outline, flat colours, matching the reference's art style. Centered on a "
                      f"solid flat pure green background (#00FF00).")
            gen_once(f"{SRC}/mouth_{vis}_{suf}.png", prompt)


def build_eyes():
    for emo in EMOTIONS:
        prompt = (f"Generate ONLY a sticker of this character's EYES AND EYEBROWS showing the '{emo}' emotion, "
                  f"looking straight ahead at the viewer. Two eyes with eyebrows, expressive line art, "
                  f"same art style as the reference (thick black outlines, flat colours), same eye/iris colour "
                  f"as the reference character. Absolutely NO skin around them, NO nose, NO face outline -- just "
                  f"the isolated eyes+eyebrows sticker. Solid flat pure green background (#00FF00).")
        gen_once(f"{SRC}/eyes_{emo}.png", prompt)
    # 3 shared lid stickers, reused across every emotion (character_1's approach)
    gen_once(f"{SRC}/lids_upper.png",
             "Generate ONLY a sticker of a pair of closing eyelids -- just the upper eyelid shapes "
             "starting to close over open eyes, same skin tone as reference, thick black outline, "
             "flat colours, matching the reference character's art style. No other facial features. "
             "Solid flat pure green background (#00FF00).")
    gen_once(f"{SRC}/lids_closed.png",
             "Generate ONLY a sticker of a pair of fully closed eyes -- two simple closed-eyelid curved "
             "lines with eyelashes, same skin tone as reference, thick black outline, flat colours, "
             "matching the reference character's art style. No other facial features. "
             "Solid flat pure green background (#00FF00).")
    gen_once(f"{SRC}/lids_half.png",
             "Generate ONLY a sticker of a pair of half-open eyes reopening from a blink -- upper lids "
             "half down AND lower eyelid curves drawn, same skin tone as reference, thick black outline, "
             "flat colours, matching the reference character's art style. No other facial features. "
             "Solid flat pure green background (#00FF00).")


POSES = {
    "explain": "standing, one hand raised with palm up as if explaining a concept, gesturing forward",
    "question": "standing, both hands out to the sides palms up, shoulders slightly raised, questioning gesture",
    "thinking": "standing, one hand touching the chin area (touching the neck stump), head-tilt body lean, thinking pose",
    "idea": "standing, one arm raised straight up with a hand open as if holding a lightbulb above it, excited pose",
    "hi": "standing, one arm raised waving hello, palm facing forward",
    "standing": "standing straight, arms relaxed at sides, neutral resting pose",
    "pointing": "standing, one arm extended forward pointing with index finger",
    "winner": "standing, both arms raised up in a victory cheer, fists or open hands up",
    "feeling_down": "standing, shoulders slumped, arms hanging low, dejected slouched posture",
    "confuse": "standing, one hand scratching the back of the neck stump, shoulders shrugged, confused posture",
    "joy": "standing, arms spread wide open, chest out, joyful open posture",
    "technical": "standing, one hand near the neck stump as if adjusting glasses, other hand holding a small clipboard, focused posture",
}

# Round 2 (2026-09-15, project board #41) -- new poses for actions a blind critic pass flagged as
# generic or visually colliding with an unrelated action's pose (see docs/CHARACTER_4_NOTES.md
# "Round 2" section for the full critic report). Each of these REPLACES a shared pose for exactly
# ONE flagged action; the other actions that shared the old pose (e.g. achieve/winner/jumping/
# kung_fu still share "winner") were judged plausible by the critic and are left untouched.
POSES_ROUND2 = {
    "crazy": ("standing, one arm bent with the hand near the head making a wild circling gesture "
              "next to the temple, the other arm flung out sideways with fingers spread, head "
              "tilted at an odd angle, wide-eyed manic unbalanced energy, asymmetric off-kilter "
              "stance -- must look clearly different from a clean two-armed victory pose"),
    "yeah": ("standing, one arm raised with a single closed fist and thumb up at shoulder height, "
             "a casual relaxed grin energy, the other arm relaxed at the side, weight shifted onto "
             "one hip -- a small casual affirmation gesture, NOT a big two-armed victory cheer"),
    "meditation": ("standing upright, both hands held together in front of the chest with only the "
                   "thumb and index fingertip of each hand touching (a meditation mudra), elbows "
                   "relaxed and slightly out to the sides, calm centered serene stillness, feet "
                   "together -- must look clearly different from two full palms pressed together "
                   "in prayer"),
    "come": ("standing, one arm extended forward and slightly downward with the fingers curling "
             "inward in a beckoning 'come here' gesture, torso leaning slightly forward toward the "
             "gesture, inviting motion -- must look clearly different from an open raised-arm hello "
             "wave"),
    "chilling": ("standing with one hand tucked into a trouser pocket, the other arm hanging loose "
                 "and relaxed, shoulders dropped, one ankle crossed loosely in front of the other, "
                 "casual laid-back lean -- must look clearly different from a neutral straight-up "
                 "standing pose"),
    "not_me": ("standing, both hands raised palms-out in front of the chest at chest height, head "
               "turned slightly to one side as if deflecting, shoulders raised slightly in a "
               "defensive denial gesture -- must look clearly different from a single arm pointing "
               "forward"),
    "technical2": ("standing, holding a small clipboard or tablet out and away from the body at "
                   "waist height with one hand, the other hand pointing down at it with an "
                   "extended index finger, alert focused presenting posture, head upright looking "
                   "at the viewer -- must NOT have a hand anywhere near the face/neck, to look "
                   "clearly different from a chin-touching thinking pose"),
}


POSES_ROUND3 = {
    "jumping": ("captured mid-air jump, both knees bent up sharply as if leaping off the ground, "
                "both arms bent and swinging forward for momentum, feet off the ground, dynamic "
                "athletic energy, body angled slightly forward -- must look clearly different from a "
                "standing pose with both arms raised straight up"),
    "kung_fu": ("wide low fighting stance, one fist pulled back at the hip and the other arm "
                "extended forward in a punching guard position, knees bent, martial-arts ready "
                "posture -- must look clearly different from a standing pose with both arms raised "
                "straight up"),
    "dancing": ("mid dance move, one arm raised and bent overhead and the other arm out to the side "
                "at a low angle, hips shifted to one side, one heel lifted slightly off the ground, "
                "playful asymmetric dance energy -- must look clearly different from a symmetric "
                "open-arms-wide pose"),
    "running": ("captured mid-stride running, torso leaning forward, one arm bent pumping forward "
                "and the other arm bent pumping back, one leg forward bent at the knee and the other "
                "leg trailing back, dynamic sprinting motion -- must look clearly different from a "
                "static open-arms-wide pose"),
    "singing": ("standing, one arm raised with a closed fist held up near chin height but NOT "
                "touching the face, as if holding a microphone at a small distance, torso leaned "
                "back slightly, other arm flung out to the side with an open hand, one knee bent "
                "forward, expressive dynamic performing stance -- must look clearly different from a "
                "hand-touching-the-face thinking pose"),
    "meditation2": ("standing straight and still, both arms relaxed down at the sides with palms "
                    "open and facing forward, shoulders relaxed and dropped, head tilted very "
                    "slightly down, calm serene breathing stillness -- must look clearly different "
                    "from two hands pressed together in prayer at the chest"),
}


# Round 4 (2026-09-15, project board #41, 3rd critic pass) -- "jumping" from round 3 drifted back
# into a generic arms-up standing pose despite the prompt (Gemini ignored "mid-air"/"knees bent");
# this retry is far more explicit that the feet must be off the ground. The other 8 entries fix
# fresh collisions the round-3 critic found: confuse/idk/praying/sneaky all sharing thinking's
# chin-touch pose (only thinking should own it), love sharing hi's wave, model sharing idea's
# lightbulb pose, and meditation/shy both reading as a plain neutral standing pose.
POSES_ROUND4 = {
    "jumping": ("frozen at the exact peak of a jump, BOTH FEET CLEARLY LIFTED OFF THE GROUND, no "
                "shadow directly under the feet, both knees bent up sharply toward the stomach, both "
                "arms bent and pulled in tight near the shoulders for balance, torso upright, a clear "
                "mid-air leaping silhouette like a jump-rope hop -- absolutely NOT a fighting stance, "
                "and NOT a standing pose with arms raised straight overhead, feet must not be planted "
                "flat on the ground"),
    "confuse": ("standing, one hand scratching the back of the head near the ear, the other arm bent "
                "across the body, shoulders raised up in a puzzled hunch, head tilted to one side -- "
                "must look clearly different from a hand resting calmly on the chin"),
    "sneaky": ("crouched slightly forward on tip-toes, both hands drawn in close in front of the "
               "chest like tip-toeing carefully, shoulders hunched forward, head tilted as if peeking "
               "sideways, a furtive creeping posture -- must look clearly different from a hand "
               "resting calmly on the chin"),
    "idk": ("standing, both arms raised out to the sides at shoulder height with palms up in a big "
            "shrug, shoulders raised up toward the ears, head tilted -- must look clearly different "
            "from a hand resting calmly on the chin"),
    "praying": ("standing, both hands pressed flat together in front of the chest in a classic "
                "prayer gesture, head bowed slightly forward, calm reverent stillness -- must look "
                "clearly different from a hand resting calmly on the chin"),
    "love": ("standing, both hands held together over the chest in a heart shape, head tilted "
             "affectionately to one side, warm gentle posture -- must look clearly different from a "
             "single raised open-palm hello wave"),
    "model": ("standing in a confident fashion-model pose, one hand on the hip, the other arm "
              "relaxed at the side, one leg crossed in front of the other at the ankle, chin up -- "
              "must look clearly different from a raised hand holding a glowing lightbulb, no "
              "lightbulb or prop of any kind"),
    "meditation2": ("sitting cross-legged on the ground with a straight back, both hands resting "
                    "open palm-up on the knees, eyes closed, calm serene meditative stillness -- must "
                    "look clearly different from a plain standing pose with arms hanging at the "
                    "sides"),
    "shy": ("standing, shoulders hunched inward, both hands fidgeting together in front of the body, "
            "head tilted downward as if avoiding eye contact, knees turned slightly inward, a timid "
            "awkward posture -- must look clearly different from a plain relaxed standing pose"),
}


def build_bodies():
    for name, desc in POSES.items():
        prompt = (f"Edit this character: same clothing and colours ({PALETTE}), but generate a HEADLESS "
                  f"full body sticker -- remove the head completely, leave a visible flat neck stump where "
                  f"the neck was cut, same body framing and scale as the reference (full body, same camera "
                  f"distance). Pose: {desc}. {STYLE}. Solid flat pure green background (#00FF00), no ground "
                  f"shadow.")
        gen_once(f"{SRC}/body_{name}.png", prompt)


def build_bodies_round2():
    for name, desc in POSES_ROUND2.items():
        prompt = (f"Edit this character: same clothing and colours ({PALETTE}), but generate a HEADLESS "
                  f"full body sticker -- remove the head completely, leave a visible flat neck stump where "
                  f"the neck was cut, same body framing and scale as the reference (full body, same camera "
                  f"distance). Pose: {desc}. {STYLE}. Solid flat pure green background (#00FF00), no ground "
                  f"shadow.")
        gen_once(f"{SRC}/body_{name}.png", prompt)


def build_bodies_round3():
    for name, desc in POSES_ROUND3.items():
        prompt = (f"Edit this character: same clothing and colours ({PALETTE}), but generate a HEADLESS "
                  f"full body sticker -- remove the head completely, leave a visible flat neck stump where "
                  f"the neck was cut, same body framing and scale as the reference (full body, same camera "
                  f"distance). Pose: {desc}. {STYLE}. Solid flat pure green background (#00FF00), no ground "
                  f"shadow.")
        gen_once(f"{SRC}/body_{name}.png", prompt)


def build_bodies_round4():
    for name, desc in POSES_ROUND4.items():
        prompt = (f"Edit this character: same clothing and colours ({PALETTE}), but generate a HEADLESS "
                  f"full body sticker -- remove the head completely, leave a visible flat neck stump where "
                  f"the neck was cut, same body framing and scale as the reference (full body, same camera "
                  f"distance). Pose: {desc}. {STYLE}. Solid flat pure green background (#00FF00), no ground "
                  f"shadow.")
        gen_once(f"{SRC}/body_{name}.png", prompt)


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else "all"
    if only == "bodies4":
        build_bodies_round4()
        return
    if only == "bodies2":
        build_bodies_round2()
        return
    if only == "bodies3":
        build_bodies_round3()
        return
    if only in ("all", "reference"):
        build_reference()
    if only in ("all", "head"):
        build_head()
    if only in ("all", "mouths"):
        build_mouths()
    if only in ("all", "eyes"):
        build_eyes()
    if only in ("all", "bodies"):
        build_bodies()
    n = sum(1 for _ in open(LOG)) if os.path.exists(LOG) else 0
    print(f"calls logged so far (char4): {n}")


if __name__ == "__main__":
    main()
