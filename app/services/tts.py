from pathlib import Path
from gtts import gTTS


def generate_tts(script_path, output_path):
    script_path = Path(script_path)
    output_path = Path(output_path)

    text = script_path.read_text(encoding="utf-8").strip()

    if not text:
        raise RuntimeError("Script empty hai.")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("TTS: Hindi audio generating...")

    tts = gTTS(
        text=text,
        lang="hi",
        slow=False
    )

    tts.save(str(output_path))

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("TTS audio generate nahi hua.")

    print("TTS DONE:", output_path)

    return output_path
