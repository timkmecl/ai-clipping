import datetime
import os
import json
from imap_tools import MailBox
from process_daily_clipping import pipeline # Import your processing function
from dotenv import load_dotenv

load_dotenv() 

# --- SETTINGS ---
EMAIL = os.getenv('GMAIL_USER')  # Set this in your .env file
PASSWORD = os.getenv('GMAIL_PASS')  # Set this in your .env file
TARGET_SUBJECT = 'Porocilo SREBRNA NIT'
FILENAME_PART = 'Dnevni kliping'

# Paths
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DATES_JSON_PATH = os.path.join(BASE_DIR, "dates.json")



def update_dates_json(new_id, formatted_date):
    """Updates the dates.json navigation file with prev/next links."""
    data = []
    if os.path.exists(DATES_JSON_PATH):
        with open(DATES_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        # If file doesn't exist, create it with an empty list
        with open(DATES_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    # Check if this ID already exists
    if any(item['id'] == new_id for item in data):
        return

    prev_id = data[-1]['id'] if data else None
    
    # Update the 'next' pointer of the previous last entry
    if data:
        data[-1]['next'] = new_id

    # Create new entry
    new_entry = {
        "id": new_id,
        "prev": prev_id,
        "next": None,
        "date": formatted_date
    }
    
    data.append(new_entry)

    with open(DATES_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def run_daily_task():
    today = datetime.date.today()
    # 260313
    today = datetime.date(2026, 3, 11)
    dir_name = today.strftime('%y%m%d')        # e.g., 250310
    display_date = today.strftime('%d. %m. %Y') # e.g., 10. 03. 2026
    
    target_dir = os.path.join(BASE_DIR, dir_name)
    report_path = os.path.join(target_dir, "report.pdf")

    # 1. Skip if already processed
    if os.path.exists(report_path):
        print(f"Directory {dir_name} already exists. Skipping.")
        return

    # 2. Search Gmail
    today_query = today.strftime('%Y/%m/%d')
    search_query = f'X-GM-RAW "subject:({TARGET_SUBJECT}) has:attachment filename:{FILENAME_PART} after:{today_query}"'

    print(f"Searching for email for {display_date}...")
    
    with MailBox('imap.gmail.com').login(EMAIL, PASSWORD) as mailbox:
        for msg in mailbox.fetch(search_query, limit=1, reverse=True):
            for att in msg.attachments:
                if FILENAME_PART.lower() in att.filename.lower():
                    
                    # 3. Create folder and save
                    os.makedirs(target_dir, exist_ok=True)
                    with open(report_path, 'wb') as f:
                        f.write(att.payload)
                    
                    print(f"Saved attachment to {report_path}")

                    # 4. Trigger your existing Pipeline
                    try:
                        pipeline(report_path, target_dir)
                        
                        # 5. Update navigation JSON only if pipeline succeeds
                        update_dates_json(dir_name, display_date)
                        print("System updated successfully.")
                    except Exception as e:
                        print(f"Pipeline failed: {e}")
                    
                    return

    print("No matching email found yet.")

if __name__ == "__main__":
    run_daily_task()