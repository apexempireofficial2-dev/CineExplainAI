import json
import time
from pathlib import Path

from app.services.scene_vision import analyze_image

FRAMES_DIR = Path("outputs/scene_frames_all")
OUTPUT = Path("outputs/scene_vision.json")

frames = sorted(FRAMES_DIR.glob("scene_*.jpg"))

print("Total frames:", len(frames))

results = []

for i, image_path in enumerate(frames, 1):
    print(f"\n[{i}/{len(frames)}] Analyzing {image_path.name}...")

    try:
        description = analyze_image(str(image_path))

        results.append({
            "scene": i,
            "image": image_path.name,
            "description": description
        })

        print("OK")

    except Exception as e:
        print("ERROR:", e)

        results.append({
            "scene": i,
            "image": image_path.name,
            "description": "",
            "error": str(e)
        })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    time.sleep(1)

print("\nDONE")
print("Saved:", OUTPUT)
