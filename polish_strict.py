from pathlib import Path
import requests
import time

INPUT = Path("uploads/0630401095a34da0ac0fbf4dfac4e398.txt")
OUTPUT = Path("outputs/ai_polished_script.txt")

URL = "http://127.0.0.1:20128/v1/chat/completions"

text = INPUT.read_text(encoding="utf-8", errors="replace").strip()

# छोटे chunks ताकि local AI timeout कम हो
chunks = []
current = ""

for para in text.split("\n"):
    para = para.strip()
    if not para:
        continue

    if len(current) + len(para) + 2 > 1000:
        if current:
            chunks.append(current)
        current = para
    else:
        current += ("\n" if current else "") + para

if current:
    chunks.append(current)

SYSTEM = """तुम एक professional Hindi movie dialogue editor हो।

तुम्हारा काम speech-to-text transcript को साफ, सही और natural Hindi dialogue में बदलना है।

IMPORTANT RULES:

1. Transcript में speech-to-text की वजह से गलत सुनाई देने वाले शब्दों को context के आधार पर सही करो।
2. Character names पूरे script में consistent रखो।
3. Eddie को एडी, Venom को वेनम, Annie को एनी, Dan को डैन, Drake को ड्रेक लिखो।
4. Symbiote जैसे movie proper nouns को गलत Hindi शब्द में मत बदलो।
5. English movie terms अगर dialogue में natural हैं तो उन्हें सही spelling में रखो।
6. Hindi dialogue ऐसा बनाओ जिसे Hindi AI voice आसानी से और natural तरीके से बोल सके।
7. टूटे हुए वाक्यों को natural dialogue में सुधारो।
8. punctuation सही लगाओ ताकि voice में सही pause आए।
9. Original dialogue का meaning मत बदलो।
10. नया dialogue या नई कहानी मत बनाओ।
11. अगर कोई शब्द unclear है लेकिन context से reasonably पता चलता है, तो सबसे logical correction करो।
12. अगर कोई शब्द बिल्कुल unclear है, तो कोई नया meaning invent मत करो।
13. Numbers/countdown को बिना कारण मत बदलो।
14. Action और dialogue को अलग-अलग समझो।
15. सिर्फ final corrected Hindi dialogue दो। कोई explanation, heading या टिप्पणी मत दो।
"""

def call_ai(chunk):
    prompt = SYSTEM + "\n\nइस transcript को सुधारो:\n\n" + chunk

    payload = {
        "model": "local-model",
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.15,
        "max_tokens": 1800
    }

    for attempt in range(3):
        try:
            r = requests.post(URL, json=payload, timeout=240)

            print("HTTP:", r.status_code)

            if r.status_code == 200:
                data = r.json()
                answer = data["choices"][0]["message"]["content"].strip()

                if answer:
                    return answer

            print("AI response failed. Attempt:", attempt + 1)

        except Exception as e:
            print("ERROR:", e)

        time.sleep(3)

    return chunk


print("===== CINEEXPLAINAI STRICT POLISH =====")
print("Original characters:", len(text))
print("Chunks:", len(chunks))
print()

results = []

for i, chunk in enumerate(chunks, 1):
    print(f"[{i}/{len(chunks)}] Processing...")

    result = call_ai(chunk)

    print("OK:", len(result), "chars")

    results.append(result)
    time.sleep(1)

final = "\n\n".join(results).strip()

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(final, encoding="utf-8")

print()
print("===== DONE =====")
print("Saved:", OUTPUT)
print("Characters:", len(final))
