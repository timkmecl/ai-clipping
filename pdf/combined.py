import pypdf
import gc
import os
import json
import json
import pathlib
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv() 

# --- CONFIGURATION ---
API_KEY = os.getenv("GENAI_API_KEY")
GENERATIVE_MODEL = "gemini-3-flash-preview"

# ========================================================
# --- SECTION 1: PDF SPLITTING AND METADATA EXTRACTION ---
# ========================================================


def get_page_links(reader, page_idx):
    """Extracts target page indices from GoTo links on a specific page."""
    indices = []
    page = reader.pages[page_idx]
    if "/Annots" in page:
        for annot_ref in page["/Annots"]:
            try:
                annot = annot_ref.get_object()
                if annot.get("/Subtype") == "/Link" and "/A" in annot:
                    action = annot["/A"]
                    if action.get("/S") == "/GoTo":
                        dest = action.get("/D")
                        page_obj = dest[0] if isinstance(dest, list) else dest
                        page_num = reader.get_page_number(page_obj)
                        if page_num is not None:
                            indices.append(page_num)
            except Exception:
                continue
    return indices

def get_header_uri(page):
    """
    Checks for a URI annotation with a specific Rect:
    [40, 758, 570, 778]
    """
    target_rect = [40, 758, 570, 778]
    if "/Annots" in page:
        for annot_ref in page["/Annots"]:
            try:
                annot = annot_ref.get_object()
                rect = annot.get("/Rect")
                
                # Verify coordinates (allowing for small float rounding differences)
                if rect and all(abs(float(rect[i]) - target_rect[i]) < 1 for i in range(4)):
                    action = annot.get("/A")
                    if action and action.get("/S") == "/URI":
                        return action.get("/URI")
            except Exception:
                continue
    return None

def split_pdf_full_process(input_path, output_dir):
    toc_dir = pathlib.Path(output_dir) / "TOC"
    articles_dir = pathlib.Path(output_dir) / "articles"
    os.makedirs(articles_dir, exist_ok=True)
    os.makedirs(toc_dir, exist_ok=True)

    reader = pypdf.PdfReader(input_path)
    total_pages = len(reader.pages)
    
    toc_start_idx = None
    first_chapter_start_idx = None
    
    # Structure for final JSON
    output_data = {
        "toc_mapping": {},      # TOC_Page_N -> [list of pdf filenames]
        "chapter_metadata": {}  # Filename -> { uri: "..." }
    }
    
    all_chapter_starts = set()

    # 1. Detect TOC and find the start of the first chapter
    for i in range(total_pages):
        found_indices = get_page_links(reader, i)
        if found_indices:
            toc_start_idx = i
            first_chapter_start_idx = min(found_indices)
            break

    if toc_start_idx is None:
        print("Could not find any TOC links.")
        return

    # 2. Process TOC pages
    # From the first link found until the page before the first chapter begins
    for i in range(toc_start_idx, first_chapter_start_idx):
        # Save the TOC page
        toc_writer = pypdf.PdfWriter()
        toc_writer.add_page(reader.pages[i])
        toc_filename = f"TOC_Page_{i+1}.pdf"
        with open(toc_dir / toc_filename, "wb") as f:
            toc_writer.write(f)
        
        # Link mapping
        links = get_page_links(reader, i)
        valid_indices = sorted(list(set([idx for idx in links if idx >= first_chapter_start_idx])))
        
        if valid_indices:
            output_data["toc_mapping"][toc_filename] = [f"{idx + 1}.pdf" for idx in valid_indices]
            all_chapter_starts.update(valid_indices)
        
        del toc_writer

    # 3. Process Chapters
    sorted_starts = sorted(list(all_chapter_starts))
    
    for i in range(len(sorted_starts)):
        start = sorted_starts[i]
        end = sorted_starts[i+1] if (i+1) < len(sorted_starts) else total_pages
        
        if start >= end: continue

        filename = f"{start + 1}.pdf"
        filepath = articles_dir / filename
        
        # Metadata check: Look for URI on the FIRST page of the chapter
        chapter_uri = get_header_uri(reader.pages[start])
        output_data["chapter_metadata"][filename] = {"uri": chapter_uri}

        # Write the chapter file
        writer = pypdf.PdfWriter()
        writer.append(reader, pages=(start, end))
        with open(filepath, "wb") as f:
            writer.write(f)
        
        print(f"Saved {filename} (URI found: {'Yes' if chapter_uri else 'No'})")
        
        del writer
        gc.collect()

    # 4. Save JSON and Final Print
    metadata_file = pathlib.Path(output_dir) / "metadata.json"
    with open(metadata_file, "w") as jf:
        json.dump(output_data, jf, indent=4)

    print("\nProcessing complete.")
    print(f"Total chapters: {len(output_data['chapter_metadata'])}")
    print(f"Metadata saved to {metadata_file}")




# ========================================================
# --- SECTION 2: QUERYING GEMINI FOR ARTICLE METADATA ----
# ========================================================




# Initialize the client
client = genai.Client(api_key=API_KEY)


def process_toc_files(directory):
    base_path = pathlib.Path(directory)
    toc_dir = base_path / "TOC"
    metadata_file = base_path / "metadata.json"
    processed_metadata_file = base_path / "processed_metadata.json"

    # 1. Load the brain (metadata.json)
    if not metadata_file.exists():
        print(f"Error: {metadata_file} not found.")
        return

    with open(metadata_file, 'r', encoding='utf-8') as f:
        master_metadata = json.load(f)

    toc_mapping = master_metadata.get("toc_mapping", {})
    chapter_metadata = master_metadata.get("chapter_metadata", {})
    
    final_output = {}

    # 2. Iterate over all TOC files mentioned in the mapping
    for toc_filename, article_filenames in toc_mapping.items():
        toc_path = toc_dir / toc_filename
        
        if not toc_path.exists():
            print(f"Skipping {toc_filename}: File not found in {toc_dir}")
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
                model=GENERATIVE_MODEL,
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
    with open(processed_metadata_file, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=4)

    print(f"\nSuccess! Result saved to {processed_metadata_file}")




# =====================================================
# --- SECTION 3: ARTICLE ANALYSIS AND SUMMARIZATION ---
# =====================================================




articles_schema = {
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
articles_prompt = """Analiziraj priloženi članek in izlušči informacije v spodaj navedeni JSON strukturi. 

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
    - Osredotoči se izključno na pozitivne ali informativne trditve v podporo zakonu (ali pomoči pri končanju življenja ali evtanaziji na splošno), odgovarjanje nasprotnikom in pozivanje h glasovanju za zakon ali pozitivno poročanje o njem.
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

def analyze_articles(directory):
    base_path = pathlib.Path(directory)
    processed_metadata_file = base_path / "processed_metadata.json"
    articles_dir = base_path / "articles"
    articles_file = base_path / "articles.json"

    # 1. Load the metadata from previous step
    if not processed_metadata_file.exists():
        print(f"Error: {processed_metadata_file} not found. Run the first script first.")
        return

    with open(processed_metadata_file, 'r', encoding='utf-8') as f:
        articles_data = json.load(f)

    final_results = {}

    # 2. Iterate over each article entry
    for filename, metadata in articles_data.items():
        pdf_path = articles_dir / filename
        
        if not pdf_path.exists():
            print(f"Skipping {filename}: PDF not found in {articles_dir}")
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
                model=GENERATIVE_MODEL,
                contents=[
                    types.Part.from_bytes(
                        data=pdf_path.read_bytes(),
                        mime_type='application/pdf',
                    ),
                    articles_prompt
                ],
                config=types.GenerateContentConfig(
                    system_instruction="Ti si strokovni analitik medijskih objav. Vedno vrni JSON po zahtevani shemi.",
                    response_mime_type="application/json",
                    thinking_config=types.ThinkingConfig(thinking_level="minimal"),
                    response_schema=articles_schema,
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
    with open(articles_file, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, ensure_ascii=False, indent=4)

    print(f"\nAnalysis complete! Final data saved to {articles_file}")




# ============================================
# --- SECTION 4: DAILY SUMMARY GENERATION  ---
# ============================================




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


def generate_daily_summary(directory):
    base_path = pathlib.Path(directory)
    articles_file = base_path / "articles.json"
    summary_file = base_path / "summary.json"

    if not articles_file.exists():
        print(f"Error: {articles_file} not found.")
        return

    with open(articles_file, 'r', encoding='utf-8') as f:
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
        "V polju 'podporniki' povzemi glavne pozitivne ali informativne trditve v podporo zakonu in odgovore na kritike nasprotnikov - tu se osredotočaš le na zagovornike in podporo. "
        "Če podatkov za podpornike ni, napiši 'Danes ni bilo zaznati omemb podpornikov'."
    )

    print("Generating Daily Executive Summary...")

    try:
        # 3. Single API Call
        response = client.models.generate_content(
            model=GENERATIVE_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "Si izkušen politični analitik. Tvoj cilj je pripraviti kratek, "
                    "informativen in objektiven dnevni pregled medijskega dogajanja. "
                    "Uporabljaj profesionalen, uraden ton. Odgovori v slovenščini."
                ),
                # This forces the model to return valid JSON only
                response_mime_type="application/json",
                response_schema=summary_schema,
                temperature=0.5,
                thinking_config=types.ThinkingConfig(thinking_level="minimal"),
            )
        )

        # 4. Save to file
        result = json.loads(response.text)
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        
        print(f"Daily summary saved to {summary_file}")

    except Exception as e:
        print(f"Failed to generate daily summary: {e}")






# =======================================================
# --- SECTION 5: THEMATIC AGGREGATION AND CLUSTERING  ---
# =======================================================




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



themes_prompt_description = """
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

themes_prompt_splosno =  """Tukaj je seznam medijskih objav. Tvoja naloga je, da jih združiš v **specifične vsebinske teme**.
""" + themes_prompt_description

themes_prompt_nasprotniki = """Tukaj je seznam medijskih objav. Tvoja naloga je, da jih združiš v **specifične vsebinske teme**, vendar se osredotoči izključno na trditve in delovanje nasprotnikov.
""" + themes_prompt_description

themes_prompt_podporniki = """Tukaj je seznam medijskih objav. Tvoja naloga je, da jih združiš v **specifične vsebinske teme**, vendar se osredotoči izključno na trditve in delovanje podpornikov.
""" + themes_prompt_description


def run_aggregation_query(data_list, system_instruction):
    """Helper function to call Gemini with specific data and instructions."""
    prompt = f"Tukaj so podatki za analizo: {json.dumps(data_list, ensure_ascii=False)}"
    
    response = client.models.generate_content(
        model=GENERATIVE_MODEL,
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

def generate_thematic_aggregation(directory):
    base_path = pathlib.Path(directory)
    articles_file = base_path / "articles.json"
    themes_file = base_path / "themes.json"

    if not articles_file.exists():
        print(f"Error: {articles_file} not found.")
        return

    with open(articles_file, 'r', encoding='utf-8') as f:
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
        themes_prompt_splosno
    )

    print(f"Processing {len(nasprotniki_input)} articles for opponent narratives...")
    nasprotniki_themes = run_aggregation_query(
        nasprotniki_input,
        themes_prompt_nasprotniki
    )

    print(f"Processing {len(podporniki_input)} articles for supporter narratives...")
    podporniki_themes = run_aggregation_query(
        podporniki_input,
        themes_prompt_podporniki
    )

    # --- FINAL MERGE ---
    final_output = {
        "splosno": splosno_themes,
        "nasprotniki": nasprotniki_themes,
        "podporniki": podporniki_themes
    }

    with open(themes_file, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=4)

    print(f"Success! Aggregation saved to {themes_file}")





# ================================================
# --- SECTION 6: FINAL MERGE INTO MASTER FILE  ---
# ================================================



def merge_report_data(directory):
    base_path = pathlib.Path(directory)
    articles_file = base_path / "articles.json"
    themes_file = base_path / "themes.json"
    summary_file = base_path / "summary.json"
    output_file = base_path / "analysis.json"

    def load_json(path):
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"Warning: {path} not found. Using empty data.")
            return {}

    # 1. Load all components
    articles_data = load_json(articles_file)
    themes_data = load_json(themes_file)
    summary_data = load_json(summary_file)

    # 2. Combine into a single logical structure
    combined_report = {
        "summary": {
            "splosno": summary_data.get("splosno", ""),
            "nasprotniki": summary_data.get("nasprotniki", ""),
            "podporniki": summary_data.get("podporniki", "")
        },
        "themes": {
            "splosno": themes_data.get("splosno", []),
            "nasprotniki": themes_data.get("nasprotniki", []),
            "podporniki": themes_data.get("podporniki", [])
        },
        "articles": list(articles_data.values())
    }

    # 3. Save the master file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_report, f, ensure_ascii=False, indent=4)

    print(f"Final report successfully merged into: {output_file}")


def pipeline(report_file, directory):
    print("Starting PDF processing and analysis pipeline...\n")
    print("\n===============================")
    print("Step 1: Splitting PDF and extracting metadata...")
    split_pdf_full_process(report_file, directory)
    print("\n===============================")
    print("Step 2: Processing TOC files and extracting article metadata...")
    process_toc_files(directory)
    print("\n===============================")
    print("Step 3: Analyzing articles and extracting summaries...")
    analyze_articles(directory)
    print("\n===============================")
    print("Step 4: Generating daily executive summary...")
    generate_daily_summary(directory)
    print("\n===============================")
    print("Step 5: Performing thematic aggregation and clustering...")
    generate_thematic_aggregation(directory)
    print("\n===============================")
    print("Step 6: Merging all data into final report...")
    merge_report_data(directory)
    print("\nAll steps completed successfully!")


if __name__ == "__main__":
    directory = "261114/"
    report_file = "261114/report.pdf"
    pipeline(report_file, directory)