from pathlib import Path
import os
import json
import base64
import requests
import time


# =========================
# CONFIG
# =========================

BASE_DIR = Path(__file__).resolve().parents[2]

FRAMES_DIR = BASE_DIR / "outputs" / "scene_frames_exact"
SCENE_MAP = BASE_DIR / "outputs" / "scene_map.json"
OUTPUT_FILE = BASE_DIR / "outputs" / "scene_visual_analysis.json"

ROUTER_URL = "http://127.0.0.1:20128/v1/chat/completions"
MODEL = "oc/mimo-v2.5-free"

API_KEY = os.getenv("NINE_ROUTER_API_KEY")


# =========================
# UTF-8 FIX
# =========================

def fix_utf8(text):
    """
    9Router kabhi-kabhi UTF-8 Hindi ko mojibake
    (à¤...) form mein return karta hai.
    """
    if not isinstance(text, str):
        return text

    for _ in range(3):
        try:
            fixed = text.encode("latin1").decode("utf-8")

            # Sirf tab replace karein jab conversion
            # actually useful ho.
            if fixed != text:
                text = fixed
            else:
                break

        except (UnicodeEncodeError, UnicodeDecodeError):
            break

    return text


# =========================
# IMAGE → BASE64
# =========================

def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


# =========================
# MIMO VISION
# =========================

def analyze_image(image_path):

    image_b64 = image_to_base64(image_path)

    prompt = """
इस movie scene image को ध्यान से देखो।

केवल वही जानकारी दो जो image में वास्तव में दिखाई दे रही है।
कहानी invent मत करना।
अनुमान या कल्पना को तथ्य की तरह मत लिखना।

इन 5 चीजों को बताओ:

1. Characters:
Image में कौन-कौन से characters/persons दिखाई दे रहे हैं।
अगर चेहरा या character पहचानना संभव नहीं है तो "unknown" लिखो।

2. Objects:
मुख्य दिखाई देने वाली objects/items बताओ।

3. Location:
Scene किस जगह का दिखाई देता है।
अगर exact location निश्चित नहीं है तो संभावित जगह को "possible" बताओ।

4. Visible action:
Image में इस समय कौन-सी action दिखाई दे रही है।

5. Important visual details:
ऐसी महत्वपूर्ण चीजें बताओ जो बाद में movie explanation script को सही scene से match करने में मदद कर सकती हैं।

जवाब केवल हिंदी में दो।
English केवल proper names या बहुत जरूरी common terms के लिए इस्तेमाल करो।

Format:

Characters:
- ...

Objects:
- ...

Location:
- ...

Visible Action:
- ...

Important Visual Details:
- ...
"""


    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.2,
        "stream": True
    }

    response = requests.post(
        ROUTER_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=180
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Mimo request failed: HTTP {response.status_code}\n"
            + response.text[:3000]
        )

    parts = []

    # =========================
    # SSE RESPONSE PARSER
    # =========================

    for line in response.text.splitlines():

        line = line.strip()

        if not line.startswith("data:"):
            continue

        raw = line[5:].strip()

        if not raw or raw == "[DONE]":
            continue

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue

        choices = data.get("choices") or []

        if not choices:
            continue

        choice = choices[0] or {}

        # Streaming response
        delta = choice.get("delta") or {}
        content = delta.get("content", "")

        # Non-streaming fallback
        if not content:
            message = choice.get("message") or {}
            content = message.get("content", "")

        if content:
            parts.append(content)

    answer = "".join(parts).strip()

    if not answer:
        raise RuntimeError(
            "Mimo ne content return kiya.\n"
            + response.text[:3000]
        )

    return fix_utf8(answer)


# =========================
# LOAD SCENE MAP
# =========================

def load_scene_map():

    if not SCENE_MAP.exists():
        raise RuntimeError(
            f"Scene map nahi mila: {SCENE_MAP}"
        )

    with open(SCENE_MAP, "r", encoding="utf-8") as f:
        data = json.load(f)

    scenes = data.get("scenes", [])

    if not scenes:
        raise RuntimeError("scene_map.json mein scenes nahi mile.")

    return scenes


# =========================
# MAIN
# =========================

def main():

    if not API_KEY:
        raise RuntimeError(
            "NINE_ROUTER_API_KEY environment variable set nahi hai."
        )

    if not FRAMES_DIR.exists():
        raise RuntimeError(
            f"Scene frames folder nahi mila: {FRAMES_DIR}"
        )

    scenes = load_scene_map()

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    results = []

    print("======================================")
    print("CineExplainAI - Mimo Vision")
    print("======================================")
    print("Model:", MODEL)
    print("Scenes:", len(scenes))
    print("Frames:", FRAMES_DIR)
    print()

    for index, scene in enumerate(scenes, start=1):

        scene_id = scene.get("id", index)

        frame_path = (
            FRAMES_DIR / f"scene_{scene_id:03d}.jpg"
        )

        print(
            f"[{index}/{len(scenes)}] "
            f"Analyzing scene {scene_id}..."
        )

        if not frame_path.exists():

            print(
                "  WARNING: frame nahi mila:",
                frame_path
            )

            results.append({
                "scene": scene_id,
                "start": scene.get("start"),
                "end": scene.get("end"),
                "duration": scene.get("duration"),
                "frame": str(frame_path),
                "status": "frame_missing",
                "visual_analysis": None
            })

            continue

        try:

            answer = analyze_image(frame_path)

            result = {
                "scene": scene_id,
                "start": scene.get("start"),
                "end": scene.get("end"),
                "duration": scene.get("duration"),
                "frame": str(frame_path),
                "status": "ok",
                "visual_analysis": answer
            }

            results.append(result)

            print("  OK")

            # 9Router par unnecessary rapid requests
            # avoid karne ke liye small pause.
            time.sleep(0.5)

        except Exception as e:

            print("  ERROR:", str(e))

            results.append({
                "scene": scene_id,
                "start": scene.get("start"),
                "end": scene.get("end"),
                "duration": scene.get("duration"),
                "frame": str(frame_path),
                "status": "error",
                "error": str(e),
                "visual_analysis": None
            })

    # =========================
    # SAVE
    # =========================

    output = {
        "model": MODEL,
        "total_scenes": len(scenes),
        "successful": sum(
            1 for x in results
            if x["status"] == "ok"
        ),
        "failed": sum(
            1 for x in results
            if x["status"] != "ok"
        ),
        "scenes": results
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=2
        )

    print()
    print("======================================")
    print("DONE")
    print("======================================")
    print("Output:")
    print(OUTPUT_FILE)
    print()
    print("Successful:",
          output["successful"])
    print("Failed:",
          output["failed"])


if __name__ == "__main__":
    main()
