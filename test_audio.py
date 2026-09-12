from pathlib import Path
from app.services.audio import extract_audio

uploads = Path("uploads")

videos = [
    p for p in uploads.iterdir()
    if p.suffix.lower() in {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v"}
]

if not videos:
    print("❌ uploads folder mein video nahi mila.")
    raise SystemExit(1)

video = videos[0]

audio = Path("outputs") / f"{video.stem}.wav"

print("🎬 Video:", video)
print("🎵 Extracting audio...")

extract_audio(video, audio)

print("✅ Audio ready:")
print(audio)
