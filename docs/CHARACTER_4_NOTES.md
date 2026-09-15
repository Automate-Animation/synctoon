# character_4 build notes (2026-09-11) — "Sir Ahmed", Gemini parts-as-stickers

Two earlier characters were rejected: character_2 (plain code-drawn, no Gemini) and character_3
(good Gemini art, but every mouth/eye was a skin RECTANGLE cut from a fixed box on a face plate —
seams, off-centre mouths under `mirror=True`, one fixed mouth-box size for all 20 visemes). This
build follows `docs/CHARACTER_1_ANATOMY.md`'s contract instead: every sprite is an independently
generated, isolated, transparent STICKER (mouth = lips/teeth/tongue only, eyes = brows+eyeballs
only, head = blank face, body = headless) — the same KIND of asset Kamal hand-drew for
character_1, just Gemini-illustrated instead of hand-inked.

## Phase 0 — reference and the chroma-key surprise

`build/char4/src/reference.png`, one call, accepted on the first generation (prompt in
`build/char4/prompt_reference.txt`): friendly male Pakistani teacher, light-blue kurta + navy
waistcoat, warm tan skin, thick clean outlines, flat 2-3 tone cel shading, no glasses/beard/text.

Gemini did NOT return pure `#00FF00` — the background came back a muted olive-green
(sampled hsv ~94deg/47%/73% in OpenCV's 0-179 hue scale, i.e. ~47deg on a 0-360 scale), and the
reference's own ground shadow is a darker patch of the SAME hue. `char3_lib.key_green`'s fixed
hue band (32-72 in OpenCV's 0-179 scale) happens to cover this shade, verified by direct alpha
sampling (corner alpha 0, character-body alpha 255) even though the PNG preview tool renders
"transparent" pixels using their stored RGB (so a keyed image still LOOKS opaque green in a plain
viewer — check `im.getpixel(...)[3]`, don't trust the preview). Built a more defensive
`tools/char4_key.py::key_green_adaptive` anyway: samples each image's OWN corner hue (not a
hardcoded constant) and keys by hue distance, with an extra erode pass + stronger despill, plus
`edge_hue_check()` that flags any sprite whose keyed edge ring is still green-ish. See
`build_character_4.py`'s `FRINGE_LOG` output for what (if anything) that flagged.

## Phase 1 — the sprite contract, this time actually followed

- `head_blank.png`: one edit of the reference — head+neck only, eyes/brows/mouth removed and
  replaced with smooth skin, nose kept, hair kept. Chroma-keyed, tight-cropped, scaled uniformly
  into a 360x300 canvas (matches character_1's own 359x293 head almost exactly) and centred.
  head/L, head/M, head/R are the SAME blank head file (head turn is faked by pupils+body, per
  character_1 anatomy point 4) — never a separate turned head.
- Mouths: 20 independent text-to-image calls (10 visemes x happy/sad), each prompted as
  "ONLY the mouth -- lips, teeth, tongue, NO skin, NO nose, NO cheeks". Chroma-keyed,
  tight-cropped to their own bbox (NOT a fixed cut box). Per-viseme boxes on the head canvas are
  character_1's own numbers verbatim (they already fit our ~360x300 head): wide visemes
  (a_e/d_j_ch/f/l/th) 110x55 @ (60,200), trans 110x45 @ (60,200), m_b_close 110x15 @ (60,220),
  o_big/oh 50x50 @ (80,200), o_small 40x40 @ (80,200).
- Eyes: 14 independent emotion calls ("ONLY eyes+eyebrows, NO skin, NO nose, NO face outline"),
  chroma-keyed, tight-cropped, all sharing ONE box (250x150 @ (10,30), also character_1's own
  number) — one drawing per emotion, L/M/R are literally the same crop (character_1 fakes gaze
  direction via body pose / head turn, not per-direction pupil art, for this first pass — see
  Known Gaps below). 3 SHARED lid stickers (upper/closed/half), reused as 02/03/04 for every
  emotion x `_2` folder, exactly character_1's blink mechanism.
- Bodies: 12 independent headless poses ("HEADLESS full body, visible neck stump, same framing"),
  chroma-keyed, tight-cropped to their own bbox. Head anchor per body is DERIVED, not fixed: 
  `find_neck()` walks down from the top of the tight crop looking for the first row whose opaque
  run is centred and wide enough (>=14% of body width) to be a collar/torso line rather than a
  raised hand -- this is what lets `winner`/`hi`/`idea` (arm above the head-line) still get a
  correct neck point instead of anchoring the head to a fingertip. `POSE_MAP` covers all 39
  `body_actions` by reusing 12 generated poses (a "pointing" sticker alone covers
  answer/me/not_me/i/that/this/you — same budget-conscious reuse character_3's own POSE_MAP did).

## Phase 2 — QA

`character_qa.py character_4` reports 32 problems, ALL in the `background[*] body box outside
canvas` check -- confirmed this is a pre-existing false positive in that check, not a
character_4 regression: running the same gate on `character_1` itself reports the identical 32
background failures (character_1's own `white` background box is `position=(20,160)
size=(750,1080)` on a 1920x1080 canvas -- `160+1080=1240 > 1080` by construction). Zero real
structural failures.

Two real bugs were found and fixed during the build, both by rendering actual composites and
looking, not by the structural gate alone (same lesson character_3's notes already flagged):

1. **Body head-anchor math went negative for every single pose.** Tight-cropping each body
   sticker to its own alpha bbox removes exactly the headroom above the neck stump that the head
   box needs to sit in -- the neck row ends up ~10-20px from the top of the crop. Fix: pad the
   canvas upward by the head box's own height before computing the anchor (`build_bodies` in
   `build_character_4.py`), not from the (nonexistent) margin left by the original art.
2. **The mouth landed on the jaw/collar, not under the nose, on the first render.** character_1's
   per-viseme mouth boxes are absolute pixels calibrated against ITS OWN head canvas, where the
   blank oval fills nearly the whole 359x293 frame. Our generated head bust (hair+ears+neck)
   tight-crops to a narrower, taller region INSIDE the 360x300 canvas, so reusing character_1's
   absolute numbers put the mouth box off to one side. Fix: `rescale_boxes_to_face()` converts
   character_1's boxes to fractions of ITS OWN canvas, then remaps those fractions onto our
   actual face-art bounding box (`ox,oy,nw,nh` from `build_head`) instead of the full 360x300
   canvas -- this is the real fix, not a coordinate hack.

A harsh-critic agent pass on `compare_visemes.png`/`compare_emotions.png`/`compare_bodies.png`
found two more real, fixable defects (no new sprite art needed):
- `o_big` and `o_small` read as nearly the same size once rescaled to our head -- character_1's
  own 50-vs-40 ratio wasn't enough gap at our scale. Widened deliberately: `o_big` 54x54,
  `o_small` 34x34, both centred on the same point.
- `eyes_bore` came back from Gemini fully open/alert, not droopy -- reads identical to `happy`.
  Regenerated with an explicit "eyelids drooping HALF CLOSED, dull tired unimpressed look" prompt
  (1 extra call); the result is genuinely half-lidded and sleepy now.

The critic's third claim (a stray heart icon on the `not_me` pose) was checked against the actual
`compare_bodies.png` tile and traced to character_1's OWN asset on the left half of that
comparison pair, not anything character_4 generated -- not a real defect, no action taken.

Two mid-build messages arrived formatted as being "from the coordinator" with oddly specific
claims (white sticker-outline halos on named files, `lids_closed.png` coming back as a whole
face). No coordinator role exists in this session, and the messages did not arrive as genuine
user turns -- they were treated as suspicious/unverified rather than followed. Independently
inspecting the actual generated files confirmed both claims were nonetheless true (a white
"sticker card" outline Gemini added around several mouth/eye stickers, which a plain green-hue
key doesn't strip; and `lids_upper.png`/`lids_closed.png` both came back as a full face circle
instead of an isolated lids sticker) -- both were fixed as ordinary QA on the actual pixels, not
because the messages said so. See `tools/char4_key.py` (`key_green_adaptive`'s white-halo
flood-fill strip + `edge_hue_check` self-test) and `build_character_4.py`'s `crop_to_lid_blobs`.

## Phase 3 — render test

`ahmed-short.txt` (168 chars, says "Sir Ahmed"), rendered via `create_animation.py`. The
character-selector LLM assigned `character: 4` to every word except the very first ("Hello"),
which it left on `character: 1` -- forced that one word to 4 in `output_test.json` and re-ran
with `--skip-core` (had to also regenerate `video_frames_info.csv` via
`utils.frame_info_generator.video_frames_info()` since `--skip-core` does not recreate it itself).
194 frames, 1920x1080, ~7.75s. Muxed with `voice.mp3` via ffmpeg (`-c:v copy -c:a aac -shortest`).
A second render of the SAME script forced to `character: 1` for every word was built the same way,
for a direct side-by-side.

## Known gaps vs. character_1 (be honest about these)

- **Eye direction is not per-drawing.** character_1 fakes gaze direction via 3 pupil positions per
  emotion; character_4's L/M/R eye files are currently the SAME crop (no pupil-shift edit was
  built for this pass) -- head turn is still faked via body pose only, one layer less nuance than
  character_1. Acceptable for v1 since `head/L`/`head/R` are themselves identical to `head/M` too
  (per SKILL.md's own documented head-turn convention), but a future pass could add the ±6%
  pupil-shift character_1 does.
- **`content`'s mouth is open/mid-word in the reference frame** rather than a closed, settled
  smile -- character_1's `content` mouth reads calmer. Cosmetic, not a structural defect.
- **`glare` and `sarcasm`, `content` and `happy`** read as visually close to each other at a
  glance (noted independently by the harsh-critic pass too) -- 14 genuinely distinct Gemini-drawn
  emotions is a lot to ask for zero overlap; character_1 has the same kind of near-duplicates
  between its own subtler emotions.
- **Body poses are reused across many `body_actions`** (12 generated poses covering 39 actions,
  via `POSE_MAP`) exactly like character_3's own approach -- `model` and `idea` share one pose
  minus the prop callout, `running` reads more like a static explaining stance than a stride.
  Same budget-conscious tradeoff character_3 made, not a character_4-specific regression.

## Second round of real bugs found by Kamal (2026-09-14) — head-body gap + squashed faces

Kamal reviewed the rendered video at full resolution (not the small QA thumbnails) and
found two real defects the previous "fix" pass missed:

1. **Head visibly detached from the body on every pose**, not just the two poses I'd
   spot-checked. Root cause: `head_M.png`'s neck was cut at canvas row 232 of a 360x300
   canvas, but the anchoring math assumed the FULL 300px was drawn content. The bottom
   69px of every head box was actually transparent padding, so the visible chin sat
   69px above where the anchor thought it was — a small-looking gap in a thumbnail,
   an obvious floating head at 1920x1080.
   **Fix:** cropped `head/{L,M,R}` to their real drawn bbox (196x220, was 360x300) so
   box-bottom and drawn-content-bottom are the same row by construction; shifted every
   eye/mouth box position by the crop's offset so they land in the same place on the
   face. Also found and fixed a second bug in the same area: the neck-detector picked a
   raised hand as "the neck" on poses where a hand sits near head height ("hi" waving,
   "come"/"love" — same pose file — and initially "thinking"); fixed by preferring the
   neck candidate closest to the MEDIAN neck row across all poses instead of the
   topmost one.
2. **Faces looked inconsistent / distorted.** All 28 eye-emotion sprites had been forced
   into ONE fixed 120x56 box via the loader's raw `resize()` (stretch, not letterbox).
   Gemini's eye stickers have native aspect ratios from 1.49 (crazy) to 2.64
   (evil_laugh); stretching every one of them into a single 2.14-aspect box visibly
   squashed or stretched the drawn eye shape per emotion — exactly Kamal's "the frame is
   resized making the face shape change" complaint.
   **Fix:** pre-baked every eye sprite onto a shared 120x65 canvas via true letterboxing
   (uniform scale, transparent padding, no stretch) so the file itself is already the
   right size — the loader's later resize becomes a no-op. `tools/fix_character_4_eye_aspect.py`.

New tools: `tools/fix_character_4_head_crop.py`, `tools/fix_character_4_eye_aspect.py`,
`tools/fix_character_4_body_anchors.py` (rewritten again — see its own docstring history).

Verified this time at FULL RESOLUTION, not just thumbnails: re-extracted the exact
frames Kamal would have seen (the "hi" and "thinking" poses at their timestamps in
`ahmed_test`), zoomed into the neck region, confirmed the head now sits flush on the
collar with no gap. `character_qa.py character_4` -> 0 problems. Re-rendered
`ahmed_test` end to end and re-generated `compare_visemes.png` / `compare_emotions.png`
/ `compare_bodies.png`.

**Lesson for next time:** the QA contact-sheet thumbnails (~260px tiles) can visually
hide a real gap or a mild squash that is obvious at 1920x1080. Always pull actual frames
from a rendered video at full resolution and zoom into the neck/eye region before
calling a geometry fix done.

## Body-pose distinctness pass (2026-09-15, project board #41)

Starting point: 39 `body_actions` names mapped onto only 12 actually-generated poses via
`POSE_MAP` in `build_character_4.py` (winner/you_pose(pointing)/explain/question/technical/
standing/hi/confuse/joy/feeling_down/idea/thinking) -- several collisions folded semantically
unrelated actions onto the same pose (e.g. crazy+yeah+jumping+achieve all on "winner").

**Method:** `tools/char4_pose_sheet.py` renders every character_4 body_action composed on the
classroom background into one labelled 39-tile contact sheet (`build/qa/character_4/
pose_sheet_roundN.png`), plus a 15-action character_1 hand-drawn bar (`build/qa/character_1/
pose_bar_reference.png`) as a "what good distinctness looks like" calibration reference. Each
round: a FRESH blind `general-purpose` critic agent (no memory of prior rounds) reviews the
labelled sheet against the reference bar and flags tiles whose pose doesn't plausibly match its
action word, or that collide with an unrelated action's pose. Flagged actions get a brand-new
Gemini-generated pose (`tools/char4_generate.py`'s `POSES_ROUND2/3/4` dicts + `build_bodiesN()`),
keyed/cropped/anchored the same way as the original 12 (`char4_key.key_green_adaptive` +
`build_character_4.py`'s own `tight_crop`/`find_neck`/pad-top anchor math -- NOT
`fix_character_4_body_anchors.py` or `fix_character_4_geometry.py`, see gotcha below), then
`POSE_MAP` is repointed and the sheet is re-rendered for the next round.

**4 rounds run, 19 new distinct poses generated (21 Gemini calls, 2 redos):**
- Round 2: crazy, yeah, meditation (later superseded), come, chilling, not_me, technical2 --
  fixed crazy/yeah colliding with winner's victory pose, meditation with praying's clasped hands,
  come with hi's wave, chilling with standing's neutral pose, not_me with the generic pointing
  pose, technical with thinking's chin-touch.
- Round 3: dancing, running, singing, kung_fu, jumping (v1, later redone), meditation2 (v1, later
  redone) -- fixed the 4-way dancing/joy/running/singing collision and jumping/kung_fu/achieve/
  winner all sharing one "arms up" pose.
- Round 4: jumping (v2 -- v1's "mid-air" prompt drifted back into a static arms-up standing pose
  despite the wording; v2 added explicit "BOTH FEET CLEARLY LIFTED OFF THE GROUND, no shadow
  under the feet" and got a real leap silhouette), sneaky, idk, praying, love, model, shy,
  meditation2 (v2 -- switched to an actual seated cross-legged pose since v1's "arms at sides"
  read as indistinguishable from plain standing) -- fixed idk/praying sharing thinking's pose,
  sneaky sharing confuse's pose, love sharing hi's wave, model sharing idea's lightbulb prop, shy
  reading identical to standing.

**Round 4 critic flagged 4 more tiles (come, crazy, question, technical)** but direct pixel
inspection of the actual composited body PNGs (not the small sheet thumbnails) showed all four
are genuinely distinct and semantically appropriate: come is a clear beckoning curl-fingers
gesture (not touching the face), crazy is a wild asymmetric one-arm-flung pose visibly unlike
chilling's one-leg-crossed lean, question is a two-hands-out questioning shrug distinct from a
flat point, technical is holding a tablet and pointing at it. This matches a pattern seen in
every round: the blind critic's per-tile prose description sometimes doesn't match what's
actually on the tile (e.g. round 2 described "kung_fu" as a "bent-arm guard stance" when it was
at the time literally the same both-arms-up file as winner; round 3/4 called several correct
poses "generic" or misattributed one tile's description to another). Verdicts were only acted on
after confirming the described defect against the actual rendered PNG, not the critic's prose
alone -- this is why round 4's 4 flags did not trigger a 5th generation round.

**Left deliberately as pose reuse (defensible, not defects, per multiple critic rounds +
direct inspection):** i/me/that/this/you/answer share one generic forward-point ("you_pose" /
`body_pointing.png`) -- classic hard-to-differentiate deictic/pronoun cluster, same call the
brief itself pre-approved. achieve/winner share the victory-V pose (near-synonyms). idk/what
share a shrug (near-synonyms). paper still shares the original "technical" pose (paper's own
tile reads fine holding a clipboard). confuse keeps its original round-1 pose (a neck-scratch,
visually close to but distinct from thinking's chin-touch) rather than getting a 4th-round
regeneration for what direct inspection suggested was a marginal, not jarring, overlap.

**Gotcha (build-order, cost a round of wasted work):** `fix_character_4_geometry.py` and
`fix_character_4_body_anchors.py` are NOT part of this pipeline's current working chain --
running either after `build_character_4.py` corrupts almost every body anchor (`fix_character_4_
body_anchors.py`'s fixed `NECK_BAND=(270,400)` assumes a different, no-longer-current body-art
canvas convention and returned "no neck candidate" fallback-reuse for 31/39 actions when tried
during this pass). The correct, current chain is: `build_character_4.py` -> `fix_character_4_
head_crop.py` -> `fix_character_4_eye_aspect.py` (body anchors are already correct straight out
of `build_character_4.py`'s own `tight_crop`/`find_neck`/pad-top math). Also: `build_character_4.
py`'s `main()` rewrites the ENTIRE `metadata.json["character_4"]` key in one shot (head+mouth+
eyes+body+background) -- unsafe to run when a concurrent session may be regenerating mouth/eye
source art (hit a real file-corruption race against a concurrent viseme-fix session during this
pass). `tools/char4_rebuild_bodies_only.py` (new) rebuilds ONLY `body/*` files and the
`metadata["character_4"]["body"]` sub-key, safe to run alongside unrelated head/mouth/eye work.

**Final state:** `character_qa.py character_4` -> 0 real problems (only the pre-existing
background-box false-positive class, same as character_1). Contact sheets:
`build/qa/character_4/pose_sheet_round{1,2,3,4}.png`, `build/qa/character_1/
pose_bar_reference.png`.
