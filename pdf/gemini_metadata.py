import json
import pathlib
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# --- CONFIGURATION ---
API_KEY = os.getenv("GENAI_API_KEY")
METADATA_FILE = "metadata.json"
TOC_DIR = pathlib.Path("TOC")
OUTPUT_FILE = "processed_metadata.json"


# Initialize the client
client = genai.Client(api_key=API_KEY)

def process_toc_files():
    # 1. Load the brain (metadata.json)
    if not pathlib.Path(METADATA_FILE).exists():
        print(f"Error: {METADATA_FILE} not found.")
        return

    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        master_metadata = json.load(f)

    toc_mapping = master_metadata.get("toc_mapping", {})
    chapter_metadata = master_metadata.get("chapter_metadata", {})
    
    final_output = {}

    # 2. Iterate over all TOC files mentioned in the mapping
    for toc_filename, article_filenames in toc_mapping.items():
        toc_path = TOC_DIR / toc_filename
        
        if not toc_path.exists():
            print(f"Skipping {toc_filename}: File not found in {TOC_DIR}")
            continue

        print(f"Querying Gemini for {toc_filename}...")

        prompt = (
            "Vrni json array objektov s podatki `naslov`, `medij` (ime ali url naslov, kar je navedeno), "
            "`datum`, `avtor`, `oznaka` (array of strings, usually length one), `intro`."
            "Dolžina arraya naj bo enaka dolžini seznama na strani. Če se isti članek pojavi večkrat, naj se ponovi tudi v outputu (torej 1:1 z vsebino na strani). "
        )

        try:
            # 3. Query Gemini using the provided SDK pattern
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=[
                    types.Part.from_bytes(
                        data=toc_path.read_bytes(),
                        mime_type='application/pdf',
                    ),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    # This forces the model to return valid JSON only
                    response_mime_type='application/json',
                    thinking_config=types.ThinkingConfig(thinking_level="minimal"),
                    temperature=0.2,  # Lower temperature for more deterministic output
                )
            )

            # Parse the AI response
            extracted_items = json.loads(response.text)

            # 4. Combine results with filenames and URIs
            # We match them by index (1st item in PDF -> 1st filename in mapping)
            for i, article_file in enumerate(article_filenames):
                if i < len(extracted_items):
                    item_data = extracted_items[i]
                    
                    # Add the URI from chapter_metadata
                    uri_val = chapter_metadata.get(article_file, {}).get("uri", "")
                    item_data["url"] = uri_val

                    item_data["id"] = article_file  # Add the filename as an ID field

                    # remove "https://www." from medij if it exists
                    if "medij" in item_data and isinstance(item_data["medij"], str):
                        item_data["medij"] = item_data["medij"].replace("https://www.", "").replace("http://www.", "").replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
                    
                    # Store in final object using filename as key
                    final_output[article_file] = item_data
                else:
                    print(f"Warning: Gemini found fewer articles than expected in {toc_filename}")

        except Exception as e:
            print(f"Failed to process {toc_filename}: {e}")

    # 5. Save the combined JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=4)

    print(f"\nSuccess! Result saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    process_toc_files()