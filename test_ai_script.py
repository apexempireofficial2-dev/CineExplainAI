from app.services.ai_script import generate_movie_script

INPUT_FILE = "outputs/final_transcript.txt"
OUTPUT_FILE = "outputs/hindi_script.txt"

try:
    result = generate_movie_script(
        INPUT_FILE,
        OUTPUT_FILE
    )

    print("✅ Hindi movie script ready!")
    print(f"📄 Output: {OUTPUT_FILE}")
    print(result)

except Exception as e:
    print("❌ Error:")
    print(e)
