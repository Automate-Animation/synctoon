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

## Viseme distinctness pass (2026-09-15, blind-critic gauntlet)

Axis: are the 10 happy + 10 sad mouth visemes shaped distinctly enough that a viewer blind to
the labels can match each to its intended sound, per `docs/CHARACTER_1_ANATOMY.md` sec 2's
shape table? Method: render all 20 mouths per mood, shuffle character_4's set with random
letters, hand a fresh Sonnet agent the character_1 reference (labelled) + character_4
candidates (unlabelled) and ask it to match blind. Repeated until confident or stuck 3+ real
attempts on a given viseme (this went to 4 for `f` — see below).

**Round 1 (original build_character_4.py art, before this pass) — confidence 35/happy,
28/sad.** Flagged: `f` showed no lip-bite at all (read as generic soft smile); `l`/`th` showed
no tongue at all (neither raised-inside nor poking-out); `o_big` didn't read as round;
`a_e_s` (sad) read as an outright HAPPY smiling mouth — a real mood bug traced to the shape
description itself hard-coding "smile"/"corners pulled up" for `a_e`, which fought the sad
mood modifier appended after it.

**Fix 1** (`tools/char4_generate.py` `VISEME_DESC`): rewrote descriptions to be mood-neutral
(shape only, mood applied separately via `mood_word`), added explicit "the tongue must be
plainly visible" language for `l`/`th`. Regenerated `f_h/s`, `l_h/s`, `th_h/s`, `a_e_s`,
`o_big_h/s` via Gemini, re-keyed with the existing `tools/build_character_4.py` helpers
(`load_keyed`/`tight_crop` — NOT a full pipeline rebuild, see gotcha below).

**Round 2 — confidence 25/happy, 42/sad.** `a_e_s` mood bug fixed (confirmed reads sad now).
Still flagged: `f` still generic/no bite; `l`/`th` still no clearly-separated tongue; `o_big`
still not reading as a clean round pucker.

**Fix 2:** far more explicit, physically-descriptive prompts — `f` as "an unmistakable overbite
of teeth-on-lip, NOT a generic open mouth"; `l` as "a separate raised pink tongue shape...
floating in the upper-middle of the cavity, think of the tongue-tip emoji"; `th` as "the tongue
tip STICKS OUT PAST THE LIPS... like the classic blep emoji". Regenerated the same 6 files.

**Round 3 — confidence 35/happy, 38/sad, direct inspection confirms `l` and `th` now genuinely
distinct** (raised tongue INSIDE for `l` vs. tongue poking OUTSIDE the lip line for `th` — both
read correctly in every subsequent round). `f` still flagged as a generic open-teeth grin
indistinguishable from `d_j_ch`/`trans`/`a_e`.

**Fix 3 (attempt 3 on `f` specifically):** rewrote `f`'s prompt to force a MOSTLY CLOSED
mouth silhouette (no dark cavity, no two rows of teeth) with only a sliver of upper teeth
resting on the lower lip — closer to `m_b_close`'s closed-ness than to the open-mouth family.
Direct inspection: correct shape, but round-6's critic still couldn't confidently separate it
from `trans`/`m_b_close` at thumbnail scale, and a mild upturn read as borderline "smiling" on
the sad variant.

**Fix 4 (attempt 4, final):** made the closed-ness and flat corners explicit and forbade any
visible cavity outright ("if you are drawing any dark interior, that is WRONG"). Direct
inspection of the result: clean, correctly flat/closed-ish bite shape with a visible single
tooth-sliver, no smile curl, for both moods.

**Round 4-6 environment problem (important — read before re-running this pass):** a SEPARATE,
concurrent session was simultaneously rebuilding character_4's body poses (this file's own
"Body-pose distinctness pass" section above, landed as commit `b57f6b8`) and repeatedly
overwrote `head/`, `eyes/`, `body/` and `images/metadata/metadata.json` out from under this
pass's full-face composite renders mid-flight — confirmed by diffing against git, not assumed
(their own notes above independently confirm "hit a real file-corruption race against a
concurrent viseme-fix session during this pass" — that concurrent session was this one). This
produced at least one badly broken evidence render (head detached, single eye, mouth on the
collar) that was NOT a real defect in this pass's work, just a torn read of files mid-write by
the other session. **Fix:** switched verification to `tools/char4_standalone_critic.py`, which
reads mouth PNGs directly from `images/characters/<char>/mouth/` and their box sizes from
`images/metadata/metadata.json`, laid out on a plain grey tile per viseme (no head/eyes/body/
background compositing at all) — the SKILL's own documented fallback ("or standalone with
their own boxes for a fair size comparison"). This is immune to the other session's churn and
is what rounds 5-6's verdicts above are based on. `tools/char4_shuffle_critic_isolated.py`
(rsync snapshot to `/tmp/c4_snapshot`) was an earlier, abandoned attempt at the same isolation
problem — it still composited through `CharacterManager`, and the snapshot itself caught the
other session's assets in a self-inconsistent mid-write state (a "surfing" background pose
appeared from nowhere). Not part of the final method; kept only as a documented dead end.

**Final round (6) confidence: 28/happy, 35/sad — genuinely close, and NOT a rubber-stamp
pass.** Real remaining gaps, all investigated against character_1's own reference art (not
assumed):
- **`f` vs `trans`/`m_b_close`:** still occasionally read as ambiguous at thumbnail scale. Checked
  character_1's own `f_h.png` directly (pixel dims 412x129, same "wide" family box as `a_e`/
  `d_j_ch`/`l`/`th` per `CHARACTER_1_ANATOMY.md`, NOT `m_b_close`'s thin-line family) — but the
  actual drawn content is itself a thin, mostly-closed black line, visually subtle by nature.
  This is 4 real regeneration attempts on `f` (the SKILL's own "stuck after 3, report why"
  threshold) — verdict: **stuck at a shape ceiling inherent to the viseme**, not an unexplored
  fix. `f` (a bilabial/labiodental near-closure) is subtle in character_1's own source art too;
  making character_4's version more dramatic would stop being an accurate "teeth on lower lip"
  shape and become a different, incorrect shape. Recommend accepting current `f` art as final
  unless a future pass wants to try enlarging `f`'s metadata box specifically (untouched by this
  pass — see below) to buy more separation from `trans`/`m_b_close` at render scale.
- **`o_big` vs `oh`:** flagged as a near-duplicate pair in 2 of 3 late rounds. Character_1's own
  `o_big_h.png`/`oh_h.png` share an IDENTICAL metadata box (50x50) and differentiate PURELY by
  drawn shape (a plain solid black circle for `o_big` vs. a pointed/angular abstract mark for
  `oh`) — character_4's versions both draw a "dark oval + white cap + teeth top" family that is
  shape-similar by construction. Not attempted this pass (would need a 5th art regeneration
  round outside this pass's remaining budget); flagged for a follow-up pass specifically on
  `oh` to make it visibly narrower/more angular than `o_big`'s round pucker.
- **`l` vs `a_e`:** one round-3 critic read `l`'s raised tongue as just "tongue at the base of a
  generic open mouth" rather than confidently "raised, touching the upper teeth" — a boundary
  call, not a repeat failure (round 5 and round 6 critics both gave `l` a clean, confident match).
  Left as-is.

**Not touched, not in scope:** a REAL, unrelated structural regression was found while
re-running `character_qa.py`'s geometry check after the concurrent session's `b57f6b8` landed —
every eye box and every mouth box (not just the 9 files this pass touched) now reports
"outside head canvas" (e.g. `mouth[a_e_h]` box bottom at y=254 vs. a 220px-tall head). Confirmed
via `git show` that this did NOT exist in the prior commit (`8af430e`, this pass's actual
starting point) and was introduced by whatever geometry step `b57f6b8`'s own rebuild ran. This
is a head/eye/mouth-box POSITIONING bug, unrelated to viseme shape/art (this pass's axis) and
outside `body/`, so it was left for whoever owns that commit rather than fixed here — flagging
it explicitly per the "never claim done without verifying" rule rather than silently ignoring a
real `character_qa.py` regression.

Evidence (this pass): `build/qa/character_4/mouth_grid_character_{1,4}_{happy,sad}.png` (full
20-mouth contact sheets), `build/qa/character_4/critic_round{1..6}_{happy,sad}[_standalone]/`
(reference + shuffled-candidate sheets + hidden answer keys per round).

## Emotion-differentiation pass (2026-09-15, project board #39)

Starting point: `content` read too close to `happy`, `glare` too close to `sarcasm` (the two
pairs a prior pass had already flagged as near-duplicate). Method: rendered all 14 base emotions
for character_1 and character_4 as labelled grids, ran a FRESH blind agent each round on a
randomly-relettered, unlabelled crop of the character_4 grid (no character_1 reference, no
emotion names given first) to (a) freely cluster tiles it thought were duplicates and (b) guess
the word→tile mapping from the 14-word list — a genuinely distinct set should let a blind viewer
mostly succeed at (b); a collapsed set won't. New tool: `tools/emotion_diff_grid.py`.

**Round 1** confirmed the problem was bigger than the two named pairs: `happy`/`content`/`lust`/
`silly` were a 4-way near-duplicate cluster (all plain round eyes), plus `angry`/`glare` and
`sad`/`shock`. Fixed: `content` → half-closed peaceful droop: `lust` → heart-shaped pupils +
hooded lid; `silly` → wall-eyed/wonky mismatched pupils (needed 2 regenerations — first attempt
didn't actually go cross-eyed); `glare` → narrowed sideways side-eye, flat brow; `shock` → huge
round eyes + tiny pupils + brows shot up.

**Rounds 2–4** each surfaced a NEW pair the fix for the previous round exposed (an inherent
side-effect of always re-testing all 14 against each other): `sad`/`worried` (fixed: sweat drop +
wide alert eyes on `worried`, vs. `sad`'s downcast tented brow + added a literal teardrop),
`bore`/`glare` (fixed: `bore` → straight-ahead heavy droop, no sideways shift), `angry`/
`evil_laugh` (fixed: `evil_laugh` → eyes squeezed into a gleeful closed crescent, vs. `angry`'s
open direct stare), `happy`/`sad`/`sarcasm` (fixed: `sarcasm` → strongly asymmetric one-eyebrow-
cocked smirk), `content`/`bore` (fixed: `content` redesigned again as fully CLOSED soft crescent
smile — categorically different from `bore`'s half-open droop, not just "less droopy"), `crazy`
not reading as manic at all (fixed: mismatched eye sizes — one bulging, one small/dilated).

**Real bugs found and fixed along the way (not art, but would have shipped broken art):**
- Two separate keying failures produced salt-noise/speckle in `silly` and `content`: Gemini's
  green background for these specific generations keyed with ~15% of pixels landing in an
  ambiguous partial-alpha zone. Fix: binarize alpha at a threshold then run two passes of
  `ImageFilter.MedianFilter` before saving — the existing `key_green_adaptive` alone wasn't
  enough for every generation, only most.
- `crazy`'s mismatched-eye art had almost no transparent margin above the art in its own tight
  crop (bbox touched row 0 of the 65px box), so it consistently sat with the smaller eye's pupil
  hidden under the hairline regardless of body pose. Fix: re-letterbox with a fixed top margin
  matching the other emotions' average headroom, applied to all 6 file copies (L/M/R + their
  `_blink` copies) since the earlier per-file loop only caught 3 of them the first time.
- `angry`'s first "fixed" regeneration (open, V-browed) came back with Gemini's usual white
  sticker-card halo, and this particular halo's outer contour survived as a thin BLACK ring
  (not caught by `key_green_adaptive`'s white-halo strip, which only targets near-white/
  low-saturation pixels) — read by a blind critic as a "spiral", confusing it with `crazy`/
  `spoked`. Fixed by re-prompting with an explicit "no sticker border/halo/vignette" instruction
  rather than trying to strip it in post — the regenerated art came back clean.

**Round 6+**: `angry`/`glare` kept recurring as a soft pair across independent rounds even after
round 1's fix (both read as "furrowed, narrowed" family). Pushed further apart: `angry` → wide
OPEN bulging eyes with a tight V meeting near the nose bridge (rage, not suspicion); `glare` kept
narrowed but pushed the sideways pupil shift harder. `bore`/`glare` recurred too, well after
round 2's fix — diagnosed as both sharing the same "half-lidded brown-tinted eye" family;
final fix made them different in KIND rather than degree: `bore` stayed a warm-toned drooping
half-shut eye looking straight down, `glare` was rebuilt as fully OPEN round eyes (no colour
tint on the lid) with both pupils pushed hard into the outer corner — genuinely different eye
shape, brow shape, and colour treatment, confirmed side by side (`/tmp/bore_vs_glare_final.png`
equivalent evidence, see below).

**A pipeline hazard, not an art problem, that cost most of this pass's remaining time:** two
other concurrent sessions were live-editing character_4 during this pass (project board #41
body-pose task, landed as `b57f6b8`; a mouth-viseme task, landed as `b86f81e`) — both touch
shared `images/metadata/metadata.json` and `images/characters/character_4/{head,body,mouth,
background}/`. Running this pass's own `build_character_4.py` + `fix_character_4_eye_aspect.py`
(the tools this pass started with) silently REVERTED their already-committed head-crop and
per-emotion eye-box geometry back to an older convention each time, which is what produced a
string of confusing, seemingly-regressing renders (a "ring" artifact, one eye hidden off-frame,
a whole-grid pose shift) that had nothing to do with this pass's actual eye ART. Root-caused via
`git status`/`git log` (a second script, `fix_character_4_geometry.py`, existed uncommitted-by-
this-pass and was the actual current convention) and a running `character_qa.py character_1`
process from another session. Fixed the process, not just the symptom: `git checkout --` every
file outside `eyes/` back to HEAD before finishing, then wrote `tools/char4_finalize_eyes.py`,
which reads the CURRENT committed per-emotion box from `metadata.json` live (never hardcodes a
box) and only re-letterboxes this pass's regenerated sprites into it — respects "don't touch
box/positioning mechanics" for real, rather than by accident. Baseline `character_qa.py
character_4` problem count is 80 (all `background[*] body box outside canvas`, confirmed via
`git stash` to be identical on a pristine HEAD checkout, i.e. pre-existing and not from this
pass) — same false-positive pattern as the 32-problem baseline documented earlier in this file,
just a higher count under the current (different) background/body geometry.

**Final verdict:** because of the pipeline hazard above, the last 2–3 rounds of whole-face
blind-critic grids were unreliable evidence (they were rendering through a moving/broken
head-eye-box positioning target, not this pass's art). The decisive, trustworthy evidence is the
isolated per-emotion eye+eyebrow SPRITE files rendered directly on a plain background with no
head/body compositing at all (bypasses the shared positioning code entirely) — a fresh blind
critic on that isolated-sprite grid found only cosmetic base-rig reuse (e.g. `happy`/`sad` share
an eye shape, differentiated only by `sad`'s teardrop — an intentional, working design, the same
pattern character_1 itself uses), successfully read `sad`, `angry`, `sarcasm`, `worried`,
`crazy`, `evil_laugh`, `lust` confidently from the word list with no prompting, and flagged only
`bore`/`glare` as a genuine remaining near-duplicate (both a "droopy/half-lidded" family) — which
was then given its final, decisive fix in this same pass (see above): `bore` and `glare` are now
different in KIND (colour-tinted drooping stare vs. open round side-shifted eyes), not just
degree.

**Known remaining soft calls (real, but not actionable without more budget):** `shock`/`spoked`
share the general "startled" register (tiny-pupil-in-wide-eye vs. burst/motion-line accents) —
both individually legible as "something startled the character", genuinely hard to split further
into "shock" vs. "spooked" specifically from eyes alone even on character_1's own asset set,
per this file's earlier honest note that some family resemblance across character_4's 14
emotions is expected and acceptable, matching character_1's own precedent.

Evidence (this pass): `build/qa/character_4/sprite_shuffled_final{,2,3}.png` +
`sprite_shuffle_map_final{,2,3}.json` (the trustworthy isolated-sprite evidence and hidden
answer keys), `build/qa/character_4/emotion_grid_character_{1,4}_labelled.png` (full labelled
14-emotion reference grids), `tools/emotion_diff_grid.py`, `tools/char4_finalize_eyes.py`,
`tools/char4_fix_eyes_round{1,2,3,4}.py` (per-round regeneration prompts).

## Head-to-body attachment re-verification pass (2026-09-15, after the body-pose/viseme/emotion
axes landed concurrently)

Axis: re-verify head-to-body attachment (the gap/anchor bug fixed twice earlier this file,
rounds "Second round of real bugs" and the original build) still holds across ALL 39
`body_actions`, specifically because three OTHER concurrent sessions rewrote
`images/characters/character_4/body/*` and `images/metadata/metadata.json["character_4"]["body"]`
from scratch mid-pass (`b57f6b8` 19 new distinct poses, `b86f81e` visemes, `1d89a6f` emotions,
`1d601a0` a reconciliation commit) — a real risk that a fix already landed for this axis got
silently reverted or invalidated by a differently-shaped rebuild, exactly as this file's own
"Gotcha" section under the body-pose pass warned.

**Method:** `tools/char4_neck_seam_qa.py` (new) composes every character_4 `body_action` at full
1920x1080 resolution via `CharacterManager` (not a shortcut re-implementation) and crops a
generous neck/collar/upper-torso region (wide margin so a held prop stays legible in context,
not an ambiguous floating blob) for all 39 actions, plus 6 character_1 reference actions as the
"clean attachment" calibration bar. A fresh, context-free `general-purpose` critic reviewed the
unlabelled crops each round; findings were independently confirmed or refuted against the actual
full-resolution `CharacterManager` render (not the crop, and not the critic's prose alone) before
any fix — the same "verify against the real pixels" discipline this file's earlier passes used.

**Timing hazard hit directly:** the first render pass and first critic round happened to land
*during* another session's `build_character_4.py` + `fix_character_4_body_anchors.py` +
`fix_character_4_eye_aspect.py` run (visible mid-flight via `ps aux` and metadata.json mtimes
churning every few seconds) — every crop from that window was stale/self-inconsistent (e.g. one
render showed `achieve`/`winner` floating badly, a re-render 90s later after the other session's
own commit showed them fine, before this pass's own fixes were even applied). Fix for the
process, not just the symptom: watched `pgrep -f build_character_4` / `metadata.json` mtime until
quiet for several minutes before trusting ANY render as ground truth, then rebuilt every
comparison image from scratch. Cost about a third of this pass's time; recorded here so a future
pass budgets for it rather than being surprised again.

**6 real, confirmed floating-head defects found and fixed** (all introduced by the concurrent
`b57f6b8` body-pose rebuild's own `find_neck()` heuristic in `tools/build_character_4.py`
misfiring on specific poses — not a regression of this file's earlier two fix rounds, and not
touched via the now-deprecated `fix_character_4_body_anchors.py`/`fix_character_4_geometry.py`
chain per the body-pose pass's own "Gotcha" note):

- **achieve / winner** (share one body art file, the two-arms-raised "victory" pose):
  `find_neck()` scans top-down for the first row with a wide, centred opaque run and returns as
  soon as it finds one — with BOTH arms raised near head height, the two separate hands in the
  same row span nearly the full image width when measured end-to-end (`xs.max()-xs.min()`,
  which does not check for a CONTIGUOUS run), satisfying the "wide + centred" test by pure
  coincidence at the very top of the image. Result: head anchored at row 14 (into the raised
  hands) instead of row ~233 (the actual collar), a large, obvious gap once rendered at full res
  (the "hi"/"thinking" raised-single-hand bug this file already fixed once -- this is the same
  root cause, but two raised hands make the false-positive row occur much earlier/worse than one).
- **idea, idk, paper, yeah**: same class of bug -- a single raised hand/fist near head height
  (holding a lightbulb prop, a shrug, a raised fist, or a clipboard) produced a skin-or-prop-toned
  blob wide/centred enough to satisfy `find_neck()`'s row-scan before the scan ever reached the
  real neck row further down, again anchoring the head 100-300px too high with an empty exposed
  neck-stump left visible on the collar below it.

**Fix:** rather than generalize `find_neck()` further (5 different failure shapes across 6
actions -- two-hand span, raised fist, raised lightbulb-holding hand, a shrug, a clipboard-holding
raise -- suggests the general heuristic is structurally unreliable for any "something raised near
head height" pose, matching this file's own precedent of hardcoding stubborn cases rather than
chasing a fully general detector), each action's true neck stump was located directly by
HSV skin-mask inspection restricted to the collar-height region of that specific body PNG
(`cv2.inRange` skin range `[3,25,60]`-`[28,200,255]`, same range `find_neck_candidates` already
used elsewhere in this codebase), confirmed by cropping and eyeballing the actual pixels, then
written as an exact manually-measured `(position, size, neck)` triple straight into
`images/metadata/metadata.json["character_4"]["body"][action]` -- `size` was left untouched
(already correct, since `build_bodies()`'s `hw=int(bw*0.30)`/`hh=int(hw/1.2)` sizing math was
never the bug, only the `(hx,hy)` placement derived from the wrong `ncx,ncy`). No sprite files
were regenerated or touched -- this was purely a metadata/anchor fix, matching the file-scope
this pass was scoped to (`images/characters/character_4/body/`, `images/metadata/metadata.json`,
`tools/*.py`, this doc -- never eyes/mouths/backgrounds, those are other axes).

**Verification:** `character_qa.py character_4` -> 0 real problems (32 pre-existing
`background[*] body box outside canvas` false positives, identical class documented earlier in
this file and shared with character_1). Three further blind-critic rounds after the fix (one
generic, one explicitly mug-prop-aware after a false-positive round flagged `confuse`/`crazy`/
`running`/`sneaky`/`model`/`standing`/`technical` for a HELD MUG PROP near the chin being
mistaken for an exposed neck stub -- verified against the actual full-res renders and confirmed
those 7 are clean, no fix needed) all came back 39/39 PASS on the full action set, with the 6
fixed actions specifically re-checked each round as a sanity control alongside a previously-clean
sample.

**Lesson reinforced (this file's third time recording it):** the fast, high-confidence path is
always full-resolution `CharacterManager.get_character()` renders eyeballed directly -- a crop
tool's own re-implementation of the composition math is a second thing that can be wrong (this
pass's own `char4_neck_seam_qa.py` crop margins had to be widened once after being too tight to
give a mug prop legible context), and ANY render taken while another session's build script might
be running must be treated as untrustworthy until the process/mtime is confirmed quiet.

Evidence: `build/qa/character_4/neck_seam/{character_1,character_4}/*.png` (45 full-res crops,
6 reference + 39 candidate, the actual images every critic round and this summary are based on),
`build/qa/character_4/neck_seam_contact_sheet.png` (labelled human-review sheet). New tool:
`tools/char4_neck_seam_qa.py`.
