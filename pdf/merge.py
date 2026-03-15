import json
import pathlib

# --- CONFIGURATION ---
ARTICLES_FILE = "articles.json"
THEMES_FILE = "themes.json"
SUMMARY_FILE = "summary.json"
OUTPUT_FILE = "analysis.json"

def merge_report_data():
    def load_json(filename):
        path = pathlib.Path(filename)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"Warning: {filename} not found. Using empty data.")
            return {}

    # 1. Load all components
    articles_data = load_json(ARTICLES_FILE)
    themes_data = load_json(THEMES_FILE)
    summary_data = load_json(SUMMARY_FILE)

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
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(combined_report, f, ensure_ascii=False, indent=4)

    print(f"Final report successfully merged into: {OUTPUT_FILE}")

if __name__ == "__main__":
    merge_report_data()