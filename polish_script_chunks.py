from pathlib import Path
import requests
import time

SRC = Path("outputs/original_script.txt")
OUT = Path("outputs/ai_polished_script.txt")

URL = "http://127.0.0.1:20128/v1/chat/completions"
MODEL = "oc/mimo-v2.5-free"

text = SRC.read_text(encoding="utf-8").strip()

# छोटे chunks ताकि router timeout न करे
chunk_size = 1800

chunks = [
    text[i:i + chunk_size]
    for i in range(0, len(text), chunk_size)
]

print("Original characters:", len(text))
print("Total chunks:", len(chunks))

results = []

for i, chunk in enumerate(chunks, 1):
    print(f"\n[{i}/{len(chunks)}] Sending to Mimo...")

    prompt = f"""
तुम एक professional Hindi movie-explanation script editor हो।

नीचे original Hindi transcript का एक हिस्सा है।

इसे natural, smooth और सुनने में engaging Hindi narration में सुधारो।

RULES:
- घटनाओं का क्रम बिल्कुल मत बदलो।
- कोई नई कहानी या information मत जोड़ो।
- Context के अनुसार गलत speech-to-text शब्द सुधारो।
- Character names consistent रखो।
- भाषा ऐसी हो जिसे Hindi AI voice आसानी से बोल सके।
- छोटे और natural sentences रखो।
- जरूरत के English movie terms रख सकते हो।
- Repetition हटाओ।
- केवल polished Hindi text दो।
- कोई heading या explanation मत दो।
- Hindi Unicode में output दो।
- `à¤...` जैसी encoding नहीं होनी चाहिए।

TEXT:
{chunk}
"""

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are an expert Hindi movie explanation script editor."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.5,
        "stream": False
    }

    success = False

    for attempt in range(3):
        try:
            r = requests.post(
                URL,
                json=payload,
                timeout=180
            )

            print("HTTP:", r.status_code)

            if r.status_code == 200:
                data = r.json()
                answer = data["choices"][0]["message"]["content"].strip()

                results.append(answer)
                success = True

                print("OK - output:", len(answer), "chars")
                break

            print(r.text[:1000])

        except Exception as e:
            print("Attempt", attempt + 1, "failed:", e)

        time.sleep(3)

    if not success:
        print(f"FAILED CHUNK {i}")
        raise SystemExit(1)

    # थोड़ा gap router को दें
    time.sleep(2)

final = "\n\n".join(results)

OUT.write_text(final, encoding="utf-8")

print("\n==============================")
print("DONE")
print("Saved:", OUT)
print("Characters:", len(final))
print("Mojibake:", "à¤" in final)
print("==============================")
