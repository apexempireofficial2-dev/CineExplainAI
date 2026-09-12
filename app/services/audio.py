from pathlib import Path
import subprocess


def extract_audio(video_path, audio_path):
    video_path = Path(video_path)
    audio_path = Path(audio_path)

    audio_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        str(audio_path)
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            "FFmpeg audio extraction failed:\n"
            + result.stderr[-3000:]
        )

    return audio_path
