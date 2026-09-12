import os
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("NINE_ROUTER_API_KEY")

r = requests.post(
    "http://127.0.0.1:20128/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    },
    json={
        "model": "oc/muse-spark-1.2-contributor-free",
        "messages": [
            {
                "role": "user",
                "content": "Hindi mein ek chhoti movie explanation line likho."
            }
        ],
        "temperature": 0.7
    },
    timeout=120
)

print("HTTP:", r.status_code)
print(r.text)
