import json
import pathlib
import time
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# --- CONFIGURATION ---
API_KEY = os.getenv("GENAI_API_KEY")
INPUT_METADATA = "processed_metadata.json"
ARTICLES_DIR = pathlib.Path("articles")
OUTPUT_FILE = "articles.json"

print(f"Using GENAI_API_KEY: {'Set' if API_KEY else 'Not Set'}")

client = genai.Client(api_key=API_KEY)

# Define the schema to ensure consistent JSON structure
response_schema = {
    "type": "OBJECT",
    "properties": {
        "splosno": {
            "type": "OBJECT",
            "properties": {
                "povzetek": {"type": "STRING"},
                "highlights": {"type": "ARRAY", "items": {"type": "STRING"}}
            },
            "required": ["povzetek", "highlights"]
        },
        "nasprotniki": {
            "type": "OBJECT",
            "nullable": True,
            "properties": {
                "povzetek": {"type": "STRING"},
                "highlights": {"type": "ARRAY", "items": {"type": "STRING"}}
            },
            "required": ["povzetek", "highlights"]
        },
        "podporniki": {
            "type": "OBJECT",
            "nullable": True,
            "properties": {
                "povzetek": {"type": "STRING"},
                "highlights": {"type": "ARRAY", "items": {"type": "STRING"}}
            },
            "required": ["povzetek", "highlights"]
        }
    },
    "required": ["splosno", "nasprotniki", "podporniki"]
}
prompt = """Analiziraj priloženi članek in izlušči informacije v spodaj navedeni JSON strukturi. 

Navodila za vsebino:
1. "splosno": 
   - "povzetek": En sam jedrnat stavek, ki povzema bistvo članka.
   - "highlights": Seznam (array) natanko treh specifičnih ključnih točk (razen če jih ni toliko). Vsaka en stavek.
2. "nasprotniki": 
   - Osredotoči se izključno na kritične, strašljive ali zavajujoče trditve proti zakonu o pomoči pri prostovoljnem končanju življenja (ali pomoči pri končanju življenja ali evtanaziji na splošno), širjenje dvoma ali pozivanje h glasovanju proti.
   - "povzetek": En stavek o narativi, taktiki ali početju nasprotnikov v tem članku. Če so nasprontiki poimenovani, jih poimenuj tudi ti.
   - "highlights": Seznam konkretnih trditev. Trditve navedi čim bolj dobesedno (v narekovajih, če gre za citat). Če gre le za splošno početje, preferiraj tri trditve. Če je trditev več, naj bo seznam daljši, a največ 10.
   - POMEMBNO: Če članek ne vsebuje nobene kritike ali navedb nasprotnikov, naj bo celotno polje "nasprotniki" enako null.
3. "podporniki":
    - Osredotoči se izključno na pozitivne ali informativne trditve v podporo zakonu (ali pomoči pri končanju življenja ali evtanaziji na splošno), pozivanje h glasovanju za zakon ali pozitivno poročanje o njem.
    - "povzetek": En stavek o narativi, taktiki ali početju podpornikov v tem članku. Če so podporniki poimenovani, jih poimenuj tudi ti.
    - "highlights": Seznam konkretnih trditev. Trditve navedi čim bolj dobesedno (v narekovajih, če gre za citat). Če gre le za splošno početje, preferiraj tri trditve. Če je trditev več, naj bo seznam daljši, a ne predolg.
    - POMEMBNO: Če članek ne vsebuje nobene pozitivne ali informativne trditve v podporo zakonu, naj bo celotno polje "podporniki" enako null.

Vrni izključno JSON objekt.
"""

aggregators = [
    "najdi.si",
    "1zavse.si",
    "novice24.net",
    "novice24.si",
    "times.si",
    "telex.si",
    "klip.si",
    "megasvet.si",
    "si21.com",
    "portal24.si",
    "telegraf.si",
    "informer.si",
    "info0"
]

def analyze_articles():
    # 1. Load the metadata from previous step
    if not pathlib.Path(INPUT_METADATA).exists():
        print(f"Error: {INPUT_METADATA} not found. Run the first script first.")
        return

    with open(INPUT_METADATA, 'r', encoding='utf-8') as f:
        articles_data = json.load(f)

    final_results = {}

    # 2. Iterate over each article entry
    for filename, metadata in articles_data.items():
        pdf_path = ARTICLES_DIR / filename
        
        if not pdf_path.exists():
            print(f"Skipping {filename}: PDF not found in {ARTICLES_DIR}")
            continue

        # if url or medij contains known aggregator, skip analysis
        # normalize missing values and convert to lowercase in one go
        url = (metadata.get("url") or "").lower()
        medij = (metadata.get("medij") or "").lower()

        if any(agg in url for agg in aggregators) or any(agg in medij for agg in aggregators):
            print(f"Skipping {filename}: Detected as aggregator content based on URL or media name: {url} / {medij}")
            metadata["contents"] = None
            final_results[filename] = metadata
            continue

        print(f"Analyzing content of {filename}...")


        try:
            # 3. Call Gemini
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=[
                    types.Part.from_bytes(
                        data=pdf_path.read_bytes(),
                        mime_type='application/pdf',
                    ),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    system_instruction="Ti si strokovni analitik medijskih objav. Vedno vrni JSON po zahtevani shemi.",
                    response_mime_type="application/json",
                    thinking_config=types.ThinkingConfig(thinking_level="minimal"),
                    response_schema=response_schema,
                    temperature=0.2 # Lower temperature for more factual extraction
                )
            )

            # 4. Parse response and update metadata
            analysis_content = json.loads(response.text)
            
            # Create a copy of existing metadata and add the new 'content' field
            updated_entry = metadata.copy()
            updated_entry["contents"] = analysis_content
            
            final_results[filename] = updated_entry

            # Optional: Small delay to stay within rate limits for large batches
            # time.sleep(1) 

        except Exception as e:
            print(f"Failed to analyze {filename}: {e}")
            # Keep original metadata but mark content as failed/empty
            metadata["contents"] = None
            final_results[filename] = metadata

    # 5. Save the final enriched JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, ensure_ascii=False, indent=4)

    print(f"\nAnalysis complete! Final data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    analyze_articles()