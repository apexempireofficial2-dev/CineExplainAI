from pathlib import Path
import json
import subprocess
import shutil

BASE_DIR = Path(__file__).resolve().parent

TIMING_FILE = BASE_DIR / "outputs" / "narration_timing.json"
CHUNKS_DIR = BASE_DIR / "outputs" / "narration_chunks"

OUTPUT_DIR = BASE_DIR / "outputs"
AUDIO_LIST = OUTPUT_DIR / "narration_concat.txt"
FINAL_AUDIO = OUTPUT_DIR / "hindi_narration.wav"
SRT_FILE = OUTPUT_DIR / "hindi_subtitles.srt"


def load_timing():
    if not TIMING_FILE.exists():
        raise RuntimeError(
            f"Timing file nahi mili: {TIMING_FILE}"
        )

    with open(TIMING_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise RuntimeError(
            "narration_timing.json list format mein nahi hai."
        )

    return data


def srt_time(seconds):
    seconds = max(0.0, float(seconds))

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    milliseconds = int(
        round((seconds - int(seconds)) * 1000)
    )

    if milliseconds >= 1000:
        milliseconds = 0
        secs += 1

    if secs >= 60:
        secs = 0
        minutes += 1

    if minutes >= 60:
        minutes = 0
        hours += 1

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{secs:02d},"
        f"{milliseconds:03d}"
    )


def create_concat_file(timing):
    lines = []

    for index, item in enumerate(timing, start=1):

        audio_path = item.get("audio")

        if audio_path:
            path = BASE_DIR / audio_path
        else:
            path = CHUNKS_DIR / f"{index:04d}.mp3"

        if not path.exists():
            # Fallback to numbered chunk
            path = CHUNKS_DIR / f"{index:04d}.mp3"

        if not path.exists():
            raise RuntimeError(
                f"Audio chunk nahi mila: {path}"
            )

        # FFmpeg concat format
        escaped = str(path).replace("'", "'\\''")

        lines.append(
            f"file '{escaped}'"
        )

    AUDIO_LIST.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8"
    )


def create_srt(timing):
    blocks = []

    for index, item in enumerate(timing, start=1):

        text = str(
            item.get("text", "")
        ).strip()

        if not text:
            continue

        start = float(
            item.get("start", 0)
        )

        end = float(
            item.get(
                "end",
                start + float(
                    item.get("duration", 0)
                )
            )
        )

        if end <= start:
            end = start + 0.5

        block = (
            f"{index}\n"
            f"{srt_time(start)} --> {srt_time(end)}\n"
            f"{text}\n"
        )

        blocks.append(block)

    SRT_FILE.write_text(
        "\n".join(blocks),
        encoding="utf-8"
    )


def create_audio():
    ffmpeg = shutil.which("ffmpeg")

    if not ffmpeg:
        raise RuntimeError(
            "ffmpeg nahi mila."
        )

    if FINAL_AUDIO.exists():
        FINAL_AUDIO.unlink()

    command = [
        ffmpeg,
        "-y",

        "-f",
        "concat",

        "-safe",
        "0",

        "-i",
        str(AUDIO_LIST),

        "-vn",

        "-ac",
        "1",

        "-ar",
        "48000",

        "-c:a",
        "pcm_s16le",

        str(FINAL_AUDIO)
    ]

    print()
    print("Creating continuous Hindi narration...")
    print()

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    if result.returncode != 0:
        print(result.stdout[-5000:])

        raise RuntimeError(
            "FFmpeg audio concat failed."
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

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        return float(
            result.stdout.strip()
        )

    except Exception:
        return None


def main():

    print("=" * 60)
    print("CineExplainAI - Narration Timeline Builder")
    print("=" * 60)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    timing = load_timing()

    print(
        f"Narration chunks: {len(timing)}"
    )

    # --------------------------------------------------
    # Verify all chunks first
    # --------------------------------------------------

    print()
    print("Checking audio chunks...")

    for index, item in enumerate(
        timing,
        start=1
    ):

        audio_path = item.get("audio")

        if audio_path:
            path = BASE_DIR / audio_path
        else:
            path = CHUNKS_DIR / f"{index:04d}.mp3"

        if not path.exists():
            path = CHUNKS_DIR / f"{index:04d}.mp3"

        if not path.exists():
            raise RuntimeError(
                f"Missing chunk {index}: {path}"
            )

    print("All audio chunks OK.")

    # --------------------------------------------------
    # Create concat list
    # --------------------------------------------------

    create_concat_file(timing)

    print(
        f"Concat list: {AUDIO_LIST}"
    )

    # --------------------------------------------------
    # Create subtitles
    # --------------------------------------------------

    create_srt(timing)

    print(
        f"Subtitles: {SRT_FILE}"
    )

    # --------------------------------------------------
    # Create continuous audio
    # --------------------------------------------------

    create_audio()

    duration = get_duration(
        FINAL_AUDIO
    )

    print()
    print("=" * 60)
    print("DONE")
    print("=" * 60)

    print(
        f"Narration chunks : {len(timing)}"
    )

    print(
        f"Audio            : {FINAL_AUDIO}"
    )

    if duration is not None:
        print(
            f"Audio duration   : {duration:.3f} seconds"
        )

    print(
        f"Subtitles        : {SRT_FILE}"
    )

    print(
        f"Concat list      : {AUDIO_LIST}"
    )


if __name__ == "__main__":
    main()
