from pathlib import Path
import re
import json
import subprocess
from gtts import gTTS

SCRIPT = Path("outputs/original_script.txt")
OUT_DIR = Path("outputs/narration_chunks")
OUT_JSON = Path("outputs/narration_timing.json")

OUT_DIR.mkdir(parents=True, exist_ok=True)

text = SCRIPT.read_text(encoding="utf-8")

# TurboScribe footer remove
text = re.sub(
    r"\(Transcribed by TurboScribe\..*?message\.\)",
    "",
    text,
    flags=re.I | re.S
).strip()

# Sentence split
parts = re.split(r'(?<=[।!?])\s+', text)
sentences = [x.strip() for x in parts if x.strip()]

print("Total sentences:", len(sentences))

timeline = []
current_time = 0.0

for i, sentence in enumerate(sentences, 1):

    mp3 = OUT_DIR / f"{i:04d}.mp3"

    print(f"[{i}/{len(sentences)}] TTS...")

    if not mp3.exists():
        tts = gTTS(text=sentence, lang="hi", slow=False)
        tts.save(str(mp3))

    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(mp3)
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {mp3}")

    duration = float(result.stdout.strip())

    timeline.append({
        "id": i,
        "text": sentence,
        "start": round(current_time, 3),
        "end": round(current_time + duration, 3),
        "duration": round(duration, 3),
        "audio": str(mp3)
    })

    current_time += duration

OUT_JSON.write_text(
    json.dumps(timeline, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print()
print("TIMING CREATED")
print("Total narration:", round(current_time, 3), "seconds")
print("JSON:", OUT_JSON)
