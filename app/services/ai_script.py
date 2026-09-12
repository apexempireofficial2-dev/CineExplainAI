from pathlib import Path
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

ROUTER_URL = "http://127.0.0.1:20128/v1/chat/completions"
MODEL = "oc/muse-spark-1.2-contributor-free"


def improve_movie_script(
    script_path,
    output_path,
    language="Hindi",
    style="Cinematic"
):
    script_path = Path(script_path)
    output_path = Path(output_path)

    # Website par upload ki hui ORIGINAL SCRIPT read karo
    original_script = script_path.read_text(
        encoding="utf-8"
    ).strip()

    if not original_script:
        raise RuntimeError("Original script empty hai.")

    api_key = os.getenv("NINE_ROUTER_API_KEY")

    if not api_key:
        raise RuntimeError(
            "NINE_ROUTER_API_KEY .env mein nahi mila."
        )

    prompt = f"""
Tum ek professional YouTube movie-explanation script writer ho.

Tumhe user ki ORIGINAL MOVIE EXPLANATION SCRIPT di ja rahi hai.
Tumhara kaam isi script ko samajhkar uska high-quality,
natural aur engaging Hindi movie explanation narration banana hai.

Language: {language}
Style: {style}

IMPORTANT RULES:

1. ORIGINAL SCRIPT KO SOURCE OF TRUTH MANAO.
2. Original story ke important events bilkul preserve karo.
3. Story ka chronological order preserve karo.
4. Characters ke naam aur important details preserve karo.
5. Apni taraf se naye story events invent mat karo.
6. Agar original script mein dialogue hai to uska meaning preserve
   karte hue natural narration mein convert karo.
7. Hindi natural aur human storyteller jaisi honi chahiye.
8. Robotic AI language avoid karo.
9. Repeated sentences remove karo.
10. Unnecessary filler remove karo.
11. Suspense aur emotional flow improve karo.
12. Movie explanation YouTube narration jaisa flow rakho.
13. Narration continuous paragraphs mein likho.
14. Scene numbers mat do.
15. Timestamps mat do.
16. Camera directions mat do.
17. [Music], [Sound], [Gunshot] jaise labels mat do.
18. Extra explanation, notes ya comments mat do.
19. Script ko unnecessarily short mat karo.
20. Original script ki important information miss mat karo.
21. Sirf improved narration script return karo.
22. Output Hindi Unicode mein hona chahiye.
23. English/Hinglish words sirf wahi use karo jahan natural lage.
24. Original script mein jo story hai usi ko better language,
    better flow aur better storytelling ke saath rewrite karo.

ORIGINAL SCRIPT:

{original_script}
"""

    response = requests.post(
        ROUTER_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert Hindi movie explanation "
                        "script writer. Preserve the original story "
                        "and improve only its narration quality."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.7,
            "stream": True,
        },
        timeout=600,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"9Router request failed: HTTP {response.status_code}\n"
            + response.text[-3000:]
        )

    chunks = []

    for line in response.text.splitlines():
        line = line.strip()

        if not line.startswith("data:"):
            continue

        payload = line[5:].strip()

        if payload == "[DONE]":
            continue

        try:
            data = json.loads(payload)

            content = (
                data["choices"][0]["delta"].get("content", "")
            )

            if content:
                chunks.append(content)

        except (
            json.JSONDecodeError,
            KeyError,
            IndexError,
            TypeError,
        ):
            continue

    improved_script = "".join(chunks).strip()

    if not improved_script:
        raise RuntimeError(
            "9Router ne empty script return ki.\n"
            + response.text[-3000:]
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path.write_text(
        improved_script,
        encoding="utf-8"
    )

    return output_path


# Backward compatibility
def generate_movie_script(
    transcript_path,
    output_path
):
    return improve_movie_script(
        transcript_path,
        output_path
    )

def cleanup_final_script(script_path, output_path):
    script_path = Path(script_path)
    output_path = Path(output_path)

    original_script = script_path.read_text(encoding="utf-8").strip()

    if not original_script:
        raise RuntimeError("Script empty hai.")

    api_key = os.getenv("NINE_ROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("NINE_ROUTER_API_KEY .env mein nahi mila.")

    prompt = f"""
Tum ek professional Hindi movie explanation editor ho.

Neeche AI-generated Hindi movie explanation script hai.
Iska kaam sirf FINAL narration cleanup karna hai.

RULES:
- Story aur events bilkul preserve karo.
- Characters ke naam preserve karo.
- Missing information mat invent karo.
- Chronological order mat badlo.
- Hindi grammar aur sentence structure correct karo.
- OCR/AI ki wajah se galat ya टूटा हुआ शब्द context ke according correct karo.
- Natural Indian Hindi/Hinglish narration banao.
- Repeated words/sentences hatao.
- Dialogue ko natural narration mein rakho.
- Suspense aur cinematic flow preserve karo.
- Script ko unnecessarily short mat karo.
- Timestamps mat do.
- Scene numbers mat do.
- Camera directions mat do.
- [Music], [Sound], [Gunshot] jaise labels mat do.
- Extra explanation/notes mat do.
- Sirf final narration script return karo.

IMPORTANT:
Agar koi sentence unclear hai, surrounding story ke context se uski grammar/wording correct karo,
lekin nayi story ya naya event invent mat karo.

SCRIPT:
{original_script}
"""

    response = requests.post(
        ROUTER_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert Hindi movie explanation editor."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "stream": True
        },
        timeout=600
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"9Router request failed: HTTP {response.status_code}\n"
            + response.text[-3000:]
        )

    chunks = []

    for line in response.text.splitlines():
        line = line.strip()

        if not line.startswith("data:"):
            continue

        payload = line[5:].strip()

        if payload == "[DONE]":
            continue

        try:
            data = json.loads(payload)
            content = data["choices"][0]["delta"].get("content", "")

            if content:
                chunks.append(content)

        except (
            json.JSONDecodeError,
            KeyError,
            IndexError,
            TypeError
        ):
            continue

    final_script = "".join(chunks).strip()

    if not final_script:
        raise RuntimeError("AI ne final script return nahi ki.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(final_script, encoding="utf-8")

    return output_path

