from google import genai

client = genai.Client()

audio = client.files.upload(
    file="outputs/parakeet_chunks/dialogue_test.wav"
)

interaction = client.interactions.create(
    model="gemini-3.5-transcribe",
    input=[
        {
            "type": "audio",
            "uri": audio.uri,
            "mime_type": audio.mime_type,
        }
    ],
    generation_config={
        "transcription_config": {
            "language_codes": ["en-US"],
            "mode": "verbatim"
        }
    },
)

text = interaction.output_text or ""
print(text)

with open("outputs/gemini_test.txt", "w", encoding="utf-8") as f:
    f.write(text)
