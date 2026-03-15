import json
import pathlib
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# --- CONFIGURATION ---
API_KEY = os.getenv("GENAI_API_KEY")
INPUT_FILE = "articles.json"
OUTPUT_FILE = "summary.json"

client = genai.Client(api_key=API_KEY)

# Define the schema for the daily summary
summary_schema = {
    "type": "OBJECT",
    "properties": {
        "splosno": {"type": "STRING"},
        "nasprotniki": {"type": "STRING"},
        "podporniki": {"type": "STRING"}
    },
    "required": ["splosno", "nasprotniki", "podporniki"]
}


customer = "Predlagatelji in zagovorniki zakona o pomoči pri prostovoljnem končanju življenja"


def generate_daily_summary():
    if not pathlib.Path(INPUT_FILE).exists():
        print(f"Error: {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. Prepare data chunks for the prompt
    articles = []

    for meta in data.values():
        contents = meta.get("contents")
        if contents:
            articles.append(meta)
    
    print(f"Prepared {len(articles)} articles for summary generation.")
    
    # 2. Build the combined prompt
    input_context = articles
    prompt = (
        f"Tukaj so vsi povzetki današnjega poročanja: {json.dumps(input_context, ensure_ascii=False)}\n\n"
        "Pripravi jedrnat, a podroben dnevni povzetek (v dveh do štirih odstavkih - odstvake loči z \\n\\n) za vsako kategorijo posebej. Čeprav povzemaš, vseeno izpostavi relevantne osebe in posamezne medije, kjer je to smiselno. "
        f"Stranka je/so: {customer}, zato se osredotoči na informacije, ki so relevantne in pomembne za to skupino. "
        "V polju 'splosno' povzemi glavno smer medijskega poročanja. Naj bo self-contained, informativen in objektiven, tako s poročanjem za kot proti. "
        "V polju 'nasprotniki' povzemi glavne kritike in narative samo nasprotnikov - tu se osredotočaš le na nasprotnike in nasprotovanje. "
        "Če podatkov za nasprotnike ni, napiši 'Danes ni bilo zaznati omemb nasprotnikov'."
        "V polju 'podporniki' povzemi glavne pozitivne ali informativne trditve v podporo zakonu samo podpornikov - tu se osredotočaš le na podporo. "
        "Če podatkov za podpornike ni, napiši 'Danes ni bilo zaznati omemb podpornikov'."
    )

    print("Generating Daily Executive Summary...")

    try:
        # 3. Single API Call
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "Si izkušen politični analitik. Tvoj cilj je pripraviti kratek, "
                    "informativen in objektiven dnevni pregled medijskega dogajanja. "
                    "Uporabljaj profesionalen, uraden ton. Odgovori v slovenščini."
                ),
                response_mime_type="application/json",
                response_schema=summary_schema,
                temperature=0.5,
                thinking_config=types.ThinkingConfig(thinking_level="minimal"),
            )
        )

        # 4. Save to file
        result = json.loads(response.text)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        
        print(f"Daily summary saved to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Failed to generate daily summary: {e}")

if __name__ == "__main__":
    generate_daily_summary()