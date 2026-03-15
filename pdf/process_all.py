import json
import pathlib
import time
import os
import gc
import pypdf
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- INITIALIZATION ---
load_dotenv()
API_KEY = os.getenv("GENAI_API_KEY")

if not API_KEY:
    print("Error: GENAI_API_KEY not found in environment variables.")
    exit(1)

client = genai.Client(api_key=API_KEY)

# --- CONFIGURATION ---
INPUT_PDF = "aaa.pdf"
TOC_DIR = pathlib.Path("TOC")
ARTICLES_DIR = pathlib.Path("articles")

# Intermediate and final files
METADATA_FILE = "metadata.json"
PROCESSED_METADATA_FILE = "processed_metadata.json"
ARTICLES_JSON = "articles.json"
THEMES_FILE = "themes.json"
SUMMARY_FILE = "summary.json"
FINAL_OUTPUT = "analysis.json"

CUSTOMER = "Predlagatelji in zagovorniki zakona o pomoči pri prostovoljnem končanju življenja"

AGGREGATORS = [
    "najdi.si", "1zavse.si", "novice24.net", "novice24.si", "times.si",
    "telex.si", "klip.si", "megasvet.si", "si21.com", "portal24.si",
    "telegraf.si", "informer.si", "info0"
]

# --- PDF SPLITTING UTILS ---

def get_page_links(reader, page_idx):
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
    target_rect = [40, 758, 570, 778]
    if "/Annots" in page:
        for annot_ref in page["/Annots"]:
            try:
                annot = annot_ref.get_object()
                rect = annot.get("/Rect")
                if rect and all(abs(float(rect[i]) - target_rect[i]) < 1 for i in range(4)):
                    action = annot.get("/A")
                    if action and action.get("/S") == "/URI":
                        return action.get("/URI")
            except Exception:
                continue
    return None

def split_pdf(input_path):
    print(f"--- 1. Splitting {input_path} ---")
    os.makedirs(ARTICLES_DIR, exist_ok=True)
    os.makedirs(TOC_DIR, exist_ok=True)

    reader = pypdf.PdfReader(input_path)
    total_pages = len(reader.pages)
    
    toc_start_idx = None
    first_chapter_start_idx = None
    
    output_data = {"toc_mapping": {}, "chapter_metadata": {}}
    all_chapter_starts = set()

    for i in range(total_pages):
        found_indices = get_page_links(reader, i)
        if found_indices:
            toc_start_idx = i
            first_chapter_start_idx = min(found_indices)
            break

    if toc_start_idx is None:
        print("Could not find any TOC links.")
        return None

    for i in range(toc_start_idx, first_chapter_start_idx):
        toc_writer = pypdf.PdfWriter()
        toc_writer.add_page(reader.pages[i])
        toc_filename = f"TOC_Page_{i+1}.pdf"
        with open(TOC_DIR / toc_filename, "wb") as f:
            toc_writer.write(f)
        
        links = get_page_links(reader, i)
        valid_indices = sorted(list(set([idx for idx in links if idx >= first_chapter_start_idx])))
        
        if valid_indices:
            output_data["toc_mapping"][toc_filename] = [f"{idx + 1}.pdf" for idx in valid_indices]
            all_chapter_starts.update(valid_indices)
        
        del toc_writer

    sorted_starts = sorted(list(all_chapter_starts))
    for i in range(len(sorted_starts)):
        start = sorted_starts[i]
        end = sorted_starts[i+1] if (i+1) < len(sorted_starts) else total_pages
        if start >= end: continue

        filename = f"{start + 1}.pdf"
        chapter_uri = get_header_uri(reader.pages[start])
        output_data["chapter_metadata"][filename] = {"uri": chapter_uri}

        writer = pypdf.PdfWriter()
        writer.append(reader, pages=(start, end))
        with open(ARTICLES_DIR / filename, "wb") as f:
            writer.write(f)
        
        del writer
        gc.collect()

    with open(METADATA_FILE, "w", encoding='utf-8') as jf:
        json.dump(output_data, jf, indent=4)
    
    return output_data

# --- GEMINI PROCESSING ---

def process_metadata(master_metadata):
    print("--- 2. Extracting Metadata via Gemini ---")
    toc_mapping = master_metadata.get("toc_mapping", {})
    chapter_metadata = master_metadata.get("chapter_metadata", {})
    final_output = {}

    for toc_filename, article_filenames in toc_mapping.items():
        toc_path = TOC_DIR / toc_filename
        print(f"Querying Gemini for {toc_filename}...")

        prompt = (
            "Vrni json array objektov s podatki naslov, medij (ime ali url naslov, kar je navedeno), "
            "datum, avtor, oznaka (array of strings, usually length one), intro."
        )

        try:
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=[types.Part.from_bytes(data=toc_path.read_bytes(), mime_type='application/pdf'), prompt],
                config=types.GenerateContentConfig(response_mime_type='application/json', temperature=0.2)
            )
            extracted_items = json.loads(response.text)

            for i, article_file in enumerate(article_filenames):
                if i < len(extracted_items):
                    item_data = extracted_items[i]
                    uri_val = chapter_metadata.get(article_file, {}).get("uri", "")
                    item_data["url"] = uri_val
                    item_data["id"] = article_file
                    
                    if "medij" in item_data and isinstance(item_data["medij"], str):
                        item_data["medij"] = item_data["medij"].replace("https://www.", "").replace("http://www.", "").replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
                    
                    final_output[article_file] = item_data
        except Exception as e:
            print(f"Failed to process {toc_filename}: {e}")

    with open(PROCESSED_METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=4)
    return final_output

def analyze_articles(articles_data):
    print("--- 3. Analyzing Articles via Gemini ---")
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
            }
        },
        "required": ["splosno", "nasprotniki"]
    }
    
    prompt = f"Analiziraj priloženi članek in izlušči informacije v spodaj navedeni JSON strukturi. Navodila za vsebino: 1. 'splosno': En stavek povzetek + 3 točke highlights. 2. 'nasprotniki': Osredotoči se na kritike zakona o pomoči pri prostovoljnem končanju življenja. Če ni kritik, naj bo nasprotniki null. Vrni izključno JSON. Ciljna publika: {CUSTOMER}"

    final_results = {}
    for filename, metadata in articles_data.items():
        pdf_path = ARTICLES_DIR / filename
        if not pdf_path.exists(): continue

        url = (metadata.get("url") or "").lower()
        medij = (metadata.get("medij") or "").lower()

        if any(agg in url for agg in AGGREGATORS) or any(agg in medij for agg in AGGREGATORS):
            print(f"Skipping {filename}: Aggregator content.")
            metadata["contents"] = None
            final_results[filename] = metadata
            continue

        print(f"Analyzing {filename}...")
        try:
            response = client.models.generate_content(
                model="gemini-3-flash-preview",
                contents=[types.Part.from_bytes(data=pdf_path.read_bytes(), mime_type='application/pdf'), prompt],
                config=types.GenerateContentConfig(
                    system_instruction="Ti si strokovni analitik medijskih objav. Vedno vrni JSON po zahtevani shemi.",
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=0.2
                )
            )
            updated_entry = metadata.copy()
            updated_entry["contents"] = json.loads(response.text)
            final_results[filename] = updated_entry
        except Exception as e:
            print(f"Failed to analyze {filename}: {e}")
            metadata["contents"] = None
            final_results[filename] = metadata

    with open(ARTICLES_JSON, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, ensure_ascii=False, indent=4)
    return final_results

def run_themes_aggregation(master_data):
    print("--- 4. Generating Themes via Gemini ---")
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

    prompt_desc = f"Ciljna publika: {CUSTOMER}. Navodila: Bodi specifičen, ne splošen. Skupine 2-5 člankov. 'ids' in 'mediji' morajo biti usklajeni. 'povzetek' 1 poved, 'highlights' 3-5 točk."

    splosno_input = []
    nasprotniki_input = []

    for file_id, meta in master_data.items():
        if "contents" not in meta or meta["contents"] is None: continue
        base_meta = {"id": file_id, "naslov": meta.get("naslov"), "medij": meta.get("medij"), "datum": meta.get("datum"), "uri": meta.get("url")}
        
        s_entry = base_meta.copy()
        s_entry["contents_splosno"] = meta["contents"]["splosno"]
        splosno_input.append(s_entry)

        if meta["contents"].get("nasprotniki"):
            o_entry = base_meta.copy()
            o_entry["contents_splosno"] = meta["contents"]["splosno"]
            o_entry["contents_nasprotniki"] = meta["contents"]["nasprotniki"]
            nasprotniki_input.append(o_entry)

    def query_gemini_themes(data, instruction):
        if not data: return []
        resp = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=f"Tukaj so podatki: {json.dumps(data, ensure_ascii=False)}",
            config=types.GenerateContentConfig(
                system_instruction=f"Si analitik tem. {instruction}",
                response_mime_type="application/json",
                response_schema=theme_array_schema,
                temperature=0.4
            )
        )
        return json.loads(resp.text)

    s_themes = query_gemini_themes(splosno_input, f"Združi v vsebinske teme. {prompt_desc}")
    n_themes = query_gemini_themes(nasprotniki_input, f"Združi v teme nasprotnikov. {prompt_desc}")

    themes_results = {"splosno": s_themes, "nasprotniki": n_themes}
    with open(THEMES_FILE, 'w', encoding='utf-8') as f:
        json.dump(themes_results, f, ensure_ascii=False, indent=4)
    return themes_results

def generate_summary(articles_data):
    print("--- 5. Generating Daily Summary ---")
    summary_schema = {
        "type": "OBJECT",
        "properties": {
            "splosno": {"type": "STRING"},
            "nasprotniki": {"type": "STRING"}
        },
        "required": ["splosno", "nasprotniki"]
    }

    relevant_articles = [m for m in articles_data.values() if m.get("contents")]
    prompt = f"Povzetki: {json.dumps(relevant_articles, ensure_ascii=False)}\n\nPripravi kratek dnevni povzetek (v enem do treh odstavkih). Stranka: {CUSTOMER}. 'splosno' = glavno poročanje, 'nasprotniki' = kritike."

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="Si izkušen politični analitik. Odgovori v slovenščini.",
                response_mime_type="application/json",
                response_schema=summary_schema,
                temperature=0.5,
            )
        )
        summary_result = json.loads(response.text)
        with open(SUMMARY_FILE, 'w', encoding='utf-8') as f:
            json.dump(summary_result, f, ensure_ascii=False, indent=4)
        return summary_result
    except Exception as e:
        print(f"Summary failed: {e}")
        return {}

def finalize_report(articles, themes, summary):
    print("--- 6. Finalizing Analysis ---")
    combined = {
        "summary": summary,
        "themes": themes,
        "articles": list(articles.values())
    }
    with open(FINAL_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False, indent=4)
    print(f"COMPLETE: {FINAL_OUTPUT}")

# --- MAIN EXECUTION ---
def main():
    if not os.path.exists(INPUT_PDF):
        print(f"Error: {INPUT_PDF} not found.")
        return

    # 1. Split PDF
    raw_meta = split_pdf(INPUT_PDF)
    if not raw_meta: return

    # 2. Extract Metadata (TOC -> Titles, Media, etc.)
    proc_meta = process_metadata(raw_meta)

    # 3. Analyze each article (PDF -> Summary, Highlights, Opponents)
    articles_enriched = analyze_articles(proc_meta)

    # 4. Aggregate into Themes
    themes = run_themes_aggregation(articles_enriched)

    # 5. Generate Executive Summary
    summary = generate_summary(articles_enriched)

    # 6. Merge all into final JSON
    finalize_report(articles_enriched, themes, summary)

if __name__ == "__main__":
    main()
