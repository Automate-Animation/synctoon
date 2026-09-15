import argparse
import json
import os

from brain_requests.speach_aligner import TranscriptionService
from brain_requests.text_aligner import TextAnalyzer
from brain_requests.utils import update_values
from utils.add_phonemes import add_phonemes
from utils.constants import emotions, body_actions, screen_mode, characters
from utils.update_character_asset_name import update_assets
from utils.frame_info_generator import video_frames_info


def parse_args():
    parser = argparse.ArgumentParser(description="Analyze script+audio into frame instructions.")
    parser.add_argument("--script", required=True, help="Path to the story text file.")
    parser.add_argument(
        "--audio",
        help="Path to an existing audio file. If omitted, audio is synthesized via ElevenLabs.",
    )
    parser.add_argument("--out-dir", help="Output directory (default: ./build/<name>).")
    parser.add_argument("--fps", type=int, default=24, help="Frames per second (default 24).")
    return parser.parse_args()


def get_alignment(script_text, audio_path, out_dir):
    """Return a Gentle-shaped {"transcript","words"} dict.

    --audio given  -> align that file with Gentle (ElevenLabs can only align audio
                       it generated itself, so there's no ElevenLabs path here).
    --audio absent -> synthesize via ElevenLabs and use its own word timestamps.
    """
    if audio_path:
        script_path = os.path.join(out_dir, "script.txt")
        with open(script_path, "w") as f:
            f.write(script_text)
        files = [
            ("transcript", script_path, "text/plain"),
            ("audio", audio_path, "application/octet-stream"),
        ]
        service = TranscriptionService(files=files)
        return service.send_request()

    voice_path = os.path.join(out_dir, "voice.mp3")
    alignment_path = os.path.splitext(voice_path)[0] + ".alignment.json"

    # ponytail: reuse a prior ElevenLabs synth if this out-dir already has one (e.g. a
    # retry after a crash downstream) so we don't burn characters re-synthesizing the
    # same script. Delete the alignment JSON (or the whole out-dir) to force a fresh call.
    if os.path.exists(alignment_path) and os.path.exists(voice_path):
        print(f"Reusing existing synthesis: {voice_path}")
        with open(alignment_path) as f:
            return json.load(f)

    # No audio supplied: synthesize via ElevenLabs and use its own alignment.
    from brain_requests import tts

    return tts.synthesize(script_text, voice_path)


def main():
    args = parse_args()

    with open(args.script) as f:
        script_text = f.read()

    name = os.path.splitext(os.path.basename(args.script))[0]
    out_dir = args.out_dir or os.path.join("build", name)
    os.makedirs(out_dir, exist_ok=True)

    # Initialize the TextAnalyzer class (provider/model come from env — see llm.py)
    analyzer = TextAnalyzer()

    response_json = get_alignment(script_text, args.audio, out_dir)
    transcript = response_json["transcript"]

    # ponytail: head_direction has NO visual effect (head/{L,M,R} are identical
    # sprites for every character -- confirmed on character_1 and character_4;
    # eyes_direction is the only real gaze signal). A separate head_movement LLM
    # call used to pick head_direction independently of eyes_direction, so the
    # two disagreed on ~30% of frames in testing -- the head "turn" implied one
    # direction while the eyes looked another, reading as the character glancing
    # around at random. Dropped that call; eyes_direction is now the single
    # source of truth for both. Upgrade path: if head art ever gets real L/R
    # turned sprites, re-add an independent (but eyes-aware) head_direction pass.
    eyes_movement = analyzer.get_eyes_movement_instructions(transcript)
    character = analyzer.get_character(transcript, characters)
    emotions_result = analyzer.get_emotion(transcript, emotions)
    body_action = analyzer.get_body_action(transcript, body_actions)
    intensity = analyzer.get_intensity(transcript)
    zoom = analyzer.get_zoom(transcript)
    screen_mode_result = analyzer.get_screen_mode(transcript, screen_mode)

    update_values(response_json, eyes_movement, "eyes_direction", "M")
    for word in response_json["words"]:
        word["head_direction"] = word["eyes_direction"].split("_")[-1]
    update_values(response_json, character, "character", 1)
    update_values(response_json, emotions_result, "emotion", 1)
    update_values(response_json, body_action, "body_action", 3)
    update_values(response_json, intensity, "intensity", 1)
    update_values(response_json, zoom, "zoom", 0)
    update_values(response_json, screen_mode_result, "screen_mode", 1)

    # add Phonemes and Frames
    add_phonemes(response_json, FRAME_PER_SECOUND=args.fps)
    update_assets(response_json)
    video_frames_info(response_json)

    out_path = os.path.join(out_dir, "output_test.json")
    with open(out_path, "w") as json_file:
        json.dump(response_json, json_file, indent=4)

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
