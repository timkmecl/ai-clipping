import pypdf
import gc
import os
import json

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

def split_pdf_full_process(input_path):
    os.makedirs("articles", exist_ok=True)
    os.makedirs("TOC", exist_ok=True)

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
        with open(os.path.join("TOC", toc_filename), "wb") as f:
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
        filepath = os.path.join("articles", filename)
        
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
    with open("metadata.json", "w") as jf:
        json.dump(output_data, jf, indent=4)

    print("\nProcessing complete.")
    print(f"Total chapters: {len(output_data['chapter_metadata'])}")
    print("Metadata saved to metadata.json")

if __name__ == "__main__":
    split_pdf_full_process("report.pdf")