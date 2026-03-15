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
OUTPUT_FILE = "themes.json"

client = genai.Client(api_key=API_KEY)

# Define the schema for a single theme list
theme_array_schema = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "naslov": {"type": "STRING"},
            "povzetek": {"type": "STRING"},
            "highlights": {"type": "ARRAY", "items": {"type": "STRING"}},
            "ids": {"type": "ARRAY", "items": {"type": "STRING"}},
            "mediji": {"type": "ARRAY", "items": {"type": "STRING"}}
        },
        "required": ["naslov", "povzetek", "highlights", "ids", "mediji"]
    }
}


customer = "Predlagatelji in zagovorniki zakona o pomoči pri prostovoljnem končanju življenja"

prompt_description = """
Ciljna publika je/so: {customer}, zato se osredotoči na teme, ki so relevantne in pomembne za to skupino, vendar hkrati ohrani širok pogled na vsebino, da zajameš različne vidike in teme, ki se pojavljajo v medijih.

Navodila za kategorizacijo:
1. **Bodi specifičen:** Ne ustvarjaj splošnih tem (npr. "Politika" ali "Zakon"). Tema mora odražati konkreten dogodek, specifičen argument ali določen vidik razprave.
2. **Velikost skupin:** Vsaka tema naj združuje le nekaj člankov (običajno 2 do 5, lahko pa seveda tudi več ali izjemoma en sam, če je edinstven in pomemben, vendar se tega zadnjega izogibaj). Če ugotoviš, da ima tema preveč raznolikih člankov, jo raje razbij na bolj specifične pod-teme.
3. **Korelacija:** Polje 'ids' mora vsebovati ključe (imena datotek) člankov, polje 'mediji' pa imena medijev teh istih člankov v popolnoma enakem vrstnem redu (mediji[i] pripada ids[i]).
4. **Kakovost vsebine:** 
   - 'povzetek': Ena poved, ki pove, kaj povezuje te specifične članke. Gre za povzetek celotne teme.
   - 'highlights': 3-5 alinej bistvenih skupnih točk, izjemoma lahko več. Vsaka en stavek.

Vrni izključno JSON array objektov.
"""

prompt_splosno =  """Tukaj je seznam medijskih objav. Tvoja naloga je, da jih združiš v **specifične vsebinske teme**.
""" + prompt_description

prompt_nasprotniki = """Tukaj je seznam medijskih objav. Tvoja naloga je, da jih združiš v **specifične vsebinske teme**, vendar se osredotoči izključno na trditve in delovanje nasprotnikov.
""" + prompt_description

prompt_podporniki = """Tukaj je seznam medijskih objav. Tvoja naloga je, da jih združiš v **specifične vsebinske teme**, vendar se osredotoči izključno na trditve in delovanje podpornikov.
""" + prompt_description


def run_aggregation_query(data_list, system_instruction):
    """Helper function to call Gemini with specific data and instructions."""
    prompt = f"Tukaj so podatki za analizo: {json.dumps(data_list, ensure_ascii=False)}"
    
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=theme_array_schema,
            thinking_config=types.ThinkingConfig(thinking_level="minimal"),
            temperature=0.4
        )
    )
    return json.loads(response.text)

def main():
    if not pathlib.Path(INPUT_FILE).exists():
        print(f"Error: {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        master_data = json.load(f)

    # --- DATA PREPARATION ---
    
    # 1. Prepare data for "splosno" (All articles with 'contents')
    splosno_input = []
    # 2. Prepare data for "nasprotniki" (Only those where nasprotniki is not null)
    nasprotniki_input = []
    # 3. Prepare data for "podporniki" (Only those where podporniki is not null)
    podporniki_input = []

    for file_id, meta in master_data.items():
        if "contents" not in meta or meta["contents"] is None:
            continue
            
        # Common metadata
        base_meta = {
            "id": file_id,
            "naslov": meta.get("naslov"),
            "medij": meta.get("medij"),
            "datum": meta.get("datum"),
            "uri": meta.get("url")
        }

        # For General Pass: Base meta + 'splosno'
        splosno_entry = base_meta.copy()
        splosno_entry["contents_splosno"] = meta["contents"]["splosno"]
        splosno_input.append(splosno_entry)

        # For Opponents Pass: Base meta + 'splosno' + 'nasprotniki'
        if meta["contents"].get("nasprotniki") is not None:
            opp_entry = base_meta.copy()
            opp_entry["contents_splosno"] = meta["contents"]["splosno"]
            opp_entry["contents_nasprotniki"] = meta["contents"]["nasprotniki"]
            nasprotniki_input.append(opp_entry)
        
        # For Supporters Pass: Base meta + 'splosno' + 'podporniki'
        if meta["contents"].get("podporniki") is not None:
            supp_entry = base_meta.copy()
            supp_entry["contents_splosno"] = meta["contents"]["splosno"]
            supp_entry["contents_podporniki"] = meta["contents"]["podporniki"]
            podporniki_input.append(supp_entry)

    # --- EXECUTION ---

    print(f"Processing {len(splosno_input)} articles for general themes...")
    splosno_themes = run_aggregation_query(
        splosno_input,
        prompt_splosno
    )

    print(f"Processing {len(nasprotniki_input)} articles for opponent narratives...")
    nasprotniki_themes = run_aggregation_query(
        nasprotniki_input,
        prompt_nasprotniki
    )

    print(f"Processing {len(podporniki_input)} articles for supporter narratives...")
    podporniki_themes = run_aggregation_query(
        podporniki_input,
        prompt_podporniki
    )

    # --- FINAL MERGE ---
    final_output = {
        "splosno": splosno_themes,
        "nasprotniki": nasprotniki_themes,
        "podporniki": podporniki_themes
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=4)

    print(f"Success! Aggregation saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()