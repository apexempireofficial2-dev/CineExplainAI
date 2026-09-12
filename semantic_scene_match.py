from pathlib import Path
import json
import os
import re
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

TIMING_FILE = BASE_DIR / "outputs" / "narration_timing.json"
VISION_FILE = BASE_DIR / "outputs" / "scene_visual_analysis.json"
OUTPUT_FILE = BASE_DIR / "outputs" / "scene_semantic_map.json"

ROUTER_URL = "http://127.0.0.1:20128/v1/chat/completions"
MODEL = "oc/mimo-v2.5-free"

MAX_RETRIES = 3
TIMEOUT = 180


def clean_text(text):
    if not text:
        return ""

    text = str(text)

    # Markdown हटाओ
    text = re.sub(r"\*\*", "", text)
    text = re.sub(r"```.*?```", "", text, flags=re.S)

    return text.strip()


def load_json(path):
    if not path.exists():
        raise RuntimeError(f"File nahi mili: {path}")

    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_narration():
    data = load_json(TIMING_FILE)

    if not isinstance(data, list):
        raise RuntimeError("narration_timing.json list format mein nahi hai.")

    result = []

    for item in data:
        if not isinstance(item, dict):
            continue

        text = clean_text(item.get("text", ""))

        if not text:
            continue

        result.append({
            "id": item.get("id"),
            "text": text,
            "start": float(item.get("start", 0)),
            "end": float(item.get("end", 0)),
            "duration": float(item.get("duration", 0)),
            "audio": item.get("audio", "")
        })

    if not result:
        raise RuntimeError("Narration chunks nahi mile.")

    return result


def load_visual_scenes():
    data = load_json(VISION_FILE)

    if not isinstance(data, dict):
        raise RuntimeError("scene_visual_analysis.json dictionary format mein nahi hai.")

    scenes = data.get("scenes", [])

    if not isinstance(scenes, list):
        raise RuntimeError("'scenes' list nahi mili.")

    result = []

    for scene in scenes:
        if not isinstance(scene, dict):
            continue

        if scene.get("status") != "ok":
            continue

        result.append({
            "scene": scene.get("scene"),
            "start": float(scene.get("start", 0)),
            "end": float(scene.get("end", 0)),
            "duration": float(scene.get("duration", 0)),
            "visual_analysis": clean_text(
                scene.get("visual_analysis", "")
            )
        })

    if not result:
        raise RuntimeError("Successful visual scenes nahi mile.")

    return result


def call_router(prompt, api_key):
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a precise movie scene matching assistant. "
                    "Never invent visual information. "
                    "Use only the supplied narration and scene descriptions."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1,
        "stream": True
    }

    last_error = ""

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(
                ROUTER_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=TIMEOUT
            )

            if response.status_code != 200:
                last_error = (
                    f"HTTP {response.status_code}: "
                    f"{response.text[-1000:]}"
                )
                print(f"  Attempt {attempt} failed: {last_error}")
                time.sleep(2 * attempt)
                continue

            chunks = []

            for line in response.text.splitlines():
                line = line.strip()

                if not line.startswith("data:"):
                    continue

                payload_line = line[5:].strip()

                if payload_line == "[DONE]":
                    continue

                try:
                    data = json.loads(payload_line)

                    content = (
                        data
                        .get("choices", [{}])[0]
                        .get("delta", {})
                        .get("content", "")
                    )

                    if content:
                        chunks.append(content)

                except (
                    json.JSONDecodeError,
                    KeyError,
                    IndexError,
                    TypeError
                ):
                    continue

            answer = "".join(chunks).strip()

            if answer:
                return answer

            last_error = "Router ne empty response diya."

        except Exception as e:
            last_error = str(e)
            print(f"  Attempt {attempt} exception: {e}")

        time.sleep(2 * attempt)

    raise RuntimeError(last_error)


def extract_json(text):
    text = text.strip()

    # ```json ... ``` हटाओ
    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.I
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    # पहले direct JSON try
    try:
        return json.loads(text)
    except Exception:
        pass

    # JSON object खोजो
    start = text.find("{")
    end = text.rfind("}")

    if start >= 0 and end > start:
        candidate = text[start:end + 1]

        try:
            return json.loads(candidate)
        except Exception:
            pass

    raise RuntimeError(
        "AI response mein valid JSON nahi mila:\n"
        + text[:3000]
    )


def match_one(narration, candidate_scenes, api_key):
    scene_text = []

    for scene in candidate_scenes:
        scene_text.append(
            f"""
SCENE {scene['scene']}
TIME: {scene['start']:.3f} - {scene['end']:.3f}

VISUAL:
{scene['visual_analysis']}
""".strip()
        )

    scenes_block = "\n\n".join(scene_text)

    prompt = f"""
Tum movie narration ko actual video scenes se match kar rahe ho.

NARRATION:
{narration['text']}

NARRATION AUDIO TIME:
{narration['start']:.3f} - {narration['end']:.3f}

Neeche candidate video scenes diye gaye hain:

{scenes_block}

TASK:

Narration ke meaning, characters, objects, location aur visible action
ke basis par sabse suitable scene choose karo.

IMPORTANT RULES:

1. Sirf supplied visual descriptions ka use karo.
2. Visual description mein jo nahi hai usko invent mat karo.
3. Narration mein kisi character ka naam hai lekin scene description
   mein character confirm nahi hai, to us character ko visual fact mat mano.
4. Scene ko sirf narration ke time ke basis par choose mat karo.
5. Semantic/visual similarity ko priority do.
6. Agar exact match nahi hai to sabse plausible scene choose karo.
7. Same scene ko multiple narration chunks ke liye choose karna allowed hai.
8. Scene ko narration ke duration ke equal hona zaroori nahi hai.
9. Scene number supplied list mein se hi choose karo.
10. Sirf JSON return karo. Koi explanation nahi.

JSON FORMAT:

{{
  "scene": 1,
  "confidence": 0.85,
  "reason": "short reason"
}}

confidence 0 se 1 ke beech number hona chahiye.
"""

    answer = call_router(prompt, api_key)
    result = extract_json(answer)

    scene_id = result.get("scene")
    confidence = result.get("confidence", 0)
    reason = result.get("reason", "")

    try:
        scene_id = int(scene_id)
    except Exception:
        raise RuntimeError(
            f"Invalid scene number: {scene_id}"
        )

    try:
        confidence = float(confidence)
    except Exception:
        confidence = 0.0

    valid_ids = {
        int(s["scene"])
        for s in candidate_scenes
        if s["scene"] is not None
    }

    if scene_id not in valid_ids:
        raise RuntimeError(
            f"AI ne invalid scene choose kiya: {scene_id}"
        )

    return {
        "scene": scene_id,
        "confidence": max(0.0, min(1.0, confidence)),
        "reason": clean_text(reason)
    }


def build_candidates(narration, scenes):
    """
    Narration ke approximate audio time ke aas-paas ke scenes ko
    candidate banata hai.

    Isse har request mein 59 scenes bhejne ki zarurat nahi padegi.
    """

    narration_mid = (
        narration["start"] + narration["end"]
    ) / 2.0

    candidates = []

    for scene in scenes:
        scene_mid = (
            scene["start"] + scene["end"]
        ) / 2.0

        distance = abs(scene_mid - narration_mid)

        # Time-near scenes ko candidate rakho.
        if distance <= 45:
            candidates.append((distance, scene))

    # Agar nearby scenes bahut kam hain,
    # to nearest scenes add karo.
    if len(candidates) < 8:
        all_scenes = []

        for scene in scenes:
            scene_mid = (
                scene["start"] + scene["end"]
            ) / 2.0

            distance = abs(scene_mid - narration_mid)
            all_scenes.append((distance, scene))

        all_scenes.sort(key=lambda x: x[0])

        existing = {
            int(s["scene"])
            for _, s in candidates
        }

        for distance, scene in all_scenes:
            sid = int(scene["scene"])

            if sid not in existing:
                candidates.append((distance, scene))
                existing.add(sid)

            if len(candidates) >= 12:
                break

    candidates.sort(key=lambda x: x[0])

    # Maximum 12 candidates
    return [
        scene
        for _, scene in candidates[:12]
    ]


def main():
    print("=" * 60)
    print("CineExplainAI - Semantic Scene Matcher")
    print("=" * 60)

    api_key = os.getenv("NINE_ROUTER_API_KEY")

    if not api_key:
        raise RuntimeError(
            "NINE_ROUTER_API_KEY environment variable nahi mila."
        )

    narration = load_narration()
    scenes = load_visual_scenes()

    print(f"Narration chunks: {len(narration)}")
    print(f"Visual scenes: {len(scenes)}")
    print(f"AI model: {MODEL}")
    print()

    results = []

    for index, item in enumerate(narration, start=1):

        print(
            f"[{index}/{len(narration)}] "
            f"Narration {item['id']} "
            f"({item['start']:.1f}-{item['end']:.1f}s)"
        )

        print("  ", item["text"][:180])

        candidates = build_candidates(
            item,
            scenes
        )

        print(
            "  Candidate scenes:",
            ", ".join(
                str(s["scene"])
                for s in candidates
            )
        )

        try:
            match = match_one(
                item,
                candidates,
                api_key
            )

            selected_scene = next(
                s for s in scenes
                if int(s["scene"]) == int(match["scene"])
            )

            result = {
                "narration_id": item["id"],
                "narration_text": item["text"],
                "narration_start": item["start"],
                "narration_end": item["end"],
                "narration_duration": item["duration"],

                "scene": selected_scene["scene"],
                "scene_start": selected_scene["start"],
                "scene_end": selected_scene["end"],
                "scene_duration": selected_scene["duration"],

                "confidence": match["confidence"],
                "reason": match["reason"],

                "audio": item["audio"]
            }

            results.append(result)

            print(
                f"  MATCH -> Scene {match['scene']} "
                f"(confidence {match['confidence']:.2f})"
            )

        except Exception as e:
            print("  MATCH FAILED:", e)

            # Fail-safe: nearest candidate
            fallback = candidates[0]

            results.append({
                "narration_id": item["id"],
                "narration_text": item["text"],
                "narration_start": item["start"],
                "narration_end": item["end"],
                "narration_duration": item["duration"],

                "scene": fallback["scene"],
                "scene_start": fallback["start"],
                "scene_end": fallback["end"],
                "scene_duration": fallback["duration"],

                "confidence": 0.0,
                "reason": "AI matching failed; nearest-scene fallback used.",

                "audio": item["audio"]
            })

        # Router par unnecessary rapid requests avoid karo
        time.sleep(0.5)

    output = {
        "model": MODEL,
        "narration_chunks": len(narration),
        "video_scenes": len(scenes),
        "matched": len(results),
        "results": results
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_FILE.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print()
    print("=" * 60)
    print("DONE")
    print("=" * 60)
    print("Output:")
    print(OUTPUT_FILE)
    print("Matched:", len(results))
    print("Failed:", sum(
        1
        for r in results
        if r["confidence"] == 0
    ))


if __name__ == "__main__":
    main()
