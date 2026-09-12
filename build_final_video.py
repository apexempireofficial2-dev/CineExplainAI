from pathlib import Path
import json
import subprocess
import shutil
import sys

BASE_DIR = Path(__file__).resolve().parent

VIDEO_FILE = BASE_DIR / "uploads" / "b1f2ec4f73a84149bd861ea62e3f8376.mp4"
PLAN_FILE = BASE_DIR / "outputs" / "scene_clip_plan.json"
NARRATION_FILE = BASE_DIR / "outputs" / "hindi_narration.wav"
SRT_FILE = BASE_DIR / "outputs" / "hindi_subtitles.srt"

OUTPUT_DIR = BASE_DIR / "outputs"
TEMP_DIR = OUTPUT_DIR / "final_clips"

VIDEO_ONLY = OUTPUT_DIR / "movie_visual_track.mp4"
FINAL_OUTPUT = OUTPUT_DIR / "Movie_Explained.mp4"


def run(command, description):
    print()
    print(description)
    print(" ".join(str(x) for x in command))

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    if result.returncode != 0:
        print(result.stdout[-6000:])
        raise RuntimeError(
            f"Command failed: {description}"
        )


def load_json(path):
    if not path.exists():
        raise RuntimeError(f"File nahi mili: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_files():
    required = [
        VIDEO_FILE,
        PLAN_FILE,
        NARRATION_FILE,
        SRT_FILE
    ]

    for path in required:
        if not path.exists():
            raise RuntimeError(
                f"Required file missing: {path}"
            )

    print("All required files found.")


def clean_temp():
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)

    TEMP_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


def create_clips(plans):
    ffmpeg = shutil.which("ffmpeg")

    if not ffmpeg:
        raise RuntimeError("ffmpeg nahi mila.")

    clip_paths = []

    total = len(plans)

    for index, plan in enumerate(plans, start=1):

        start = float(
            plan["clip_start"]
        )

        narration_duration = float(
            plan["narration_duration"]
        )

        if narration_duration <= 0:
            print(
                f"[{index}/{total}] "
                "Invalid narration duration, skip."
            )
            continue

        output = TEMP_DIR / (
            f"clip_{index:04d}.mp4"
        )

        # Exact narration duration.
        #
        # Movie audio intentionally remove kiya ja raha hai.
        # Sirf visual track final narration ke saath use hoga.

        command = [
            ffmpeg,
            "-y",

            "-ss",
            f"{start:.6f}",

            "-i",
            str(VIDEO_FILE),

            "-t",
            f"{narration_duration:.6f}",

            "-an",

            "-vf",
            "fps=30,format=yuv420p",

            "-c:v",
            "libx264",

            "-preset",
            "veryfast",

            "-crf",
            "23",

            "-movflags",
            "+faststart",

            str(output)
        ]

        try:
            run(
                command,
                f"[{index}/{total}] Creating video clip"
            )

            clip_paths.append(output)

        except Exception as e:
            print(
                f"Clip {index} failed: {e}"
            )

            raise

    if not clip_paths:
        raise RuntimeError(
            "Ek bhi video clip create nahi hui."
        )

    return clip_paths


def create_concat_list(clip_paths):
    concat_file = TEMP_DIR / "concat.txt"

    lines = []

    for path in clip_paths:
        escaped = str(path).replace(
            "'",
            "'\\''"
        )

        lines.append(
            f"file '{escaped}'"
        )

    concat_file.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8"
    )

    return concat_file


def concatenate_clips(concat_file):
    ffmpeg = shutil.which("ffmpeg")

    if VIDEO_ONLY.exists():
        VIDEO_ONLY.unlink()

    command = [
        ffmpeg,
        "-y",

        "-f",
        "concat",

        "-safe",
        "0",

        "-i",
        str(concat_file),

        "-an",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        "-r",
        "30",

        "-movflags",
        "+faststart",

        str(VIDEO_ONLY)
    ]

    run(
        command,
        "Concatenating all scene clips"
    )


def create_final_video():
    ffmpeg = shutil.which("ffmpeg")

    if FINAL_OUTPUT.exists():
        FINAL_OUTPUT.unlink()

    # Subtitles ko soft subtitle stream ke roop mein add kar rahe hain.
    # Saath mein Hindi narration audio.
    command = [
        ffmpeg,
        "-y",

        "-i",
        str(VIDEO_ONLY),

        "-i",
        str(NARRATION_FILE),

        "-i",
        str(SRT_FILE),

        "-map",
        "0:v:0",

        "-map",
        "1:a:0",

        "-map",
        "2:0",

        "-c:v",
        "copy",

        "-c:a",
        "aac",

        "-b:a",
        "192k",

        "-c:s",
        "mov_text",

        "-shortest",

        "-metadata:s:s:0",
        "language=hin",

        "-metadata:s:s:0",
        "title=Hindi Subtitles",

        "-metadata",
        "title=CineExplainAI Movie Explained",

        "-movflags",
        "+faststart",

        str(FINAL_OUTPUT)
    ]

    run(
        command,
        "Adding Hindi narration and subtitles"
    )


def get_duration(path):
    ffprobe = shutil.which("ffprobe")

    if not ffprobe:
        return None

    command = [
        ffprobe,
        "-v",
        "error",

        "-show_entries",
        "format=duration",

        "-of",
        "default=noprint_wrappers=1:nokey=1",

        str(path)
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        return float(
            result.stdout.strip()
        )
    except Exception:
        return None


def main():
    print("=" * 60)
    print("CineExplainAI - FINAL VIDEO BUILDER")
    print("=" * 60)

    check_files()

    semantic = load_json(
        PLAN_FILE
    )

    plans = semantic.get(
        "plans",
        []
    )

    if not plans:
        raise RuntimeError(
            "scene_clip_plan.json mein plans nahi mile."
        )

    print(
        f"Clip plans: {len(plans)}"
    )

    clean_temp()

    # --------------------------------------------------
    # 1. Create individual visual clips
    # --------------------------------------------------

    clip_paths = create_clips(
        plans
    )

    print()
    print(
        f"Created clips: {len(clip_paths)}"
    )

    # --------------------------------------------------
    # 2. Create concat list
    # --------------------------------------------------

    concat_file = create_concat_list(
        clip_paths
    )

    # --------------------------------------------------
    # 3. Concatenate visual track
    # --------------------------------------------------

    concatenate_clips(
        concat_file
    )

    visual_duration = get_duration(
        VIDEO_ONLY
    )

    if visual_duration is not None:
        print(
            f"Visual track duration: "
            f"{visual_duration:.3f} seconds"
        )

    # --------------------------------------------------
    # 4. Add narration + subtitles
    # --------------------------------------------------

    create_final_video()

    final_duration = get_duration(
        FINAL_OUTPUT
    )

    print()
    print("=" * 60)
    print("FINAL VIDEO READY")
    print("=" * 60)

    print(
        f"Output: {FINAL_OUTPUT}"
    )

    if final_duration is not None:
        print(
            f"Duration: "
            f"{final_duration:.3f} seconds"
        )

    print()
    print(
        "Original source video was not modified."
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped by user.")
        sys.exit(130)
    except Exception as e:
        print()
        print("=" * 60)
        print("ERROR")
        print("=" * 60)
        print(e)
        sys.exit(1)
