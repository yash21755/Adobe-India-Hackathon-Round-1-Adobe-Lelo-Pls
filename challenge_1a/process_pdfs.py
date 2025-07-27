import pymupdf
import os
import json
import re
from collections import defaultdict

# These are expected by the hackathon environment's docker run command.
INPUT_DIR = "/app/input"
OUTPUT_DIR = "/app/output"

def analyze_document_structure_advanced(pdf_path):
    """
    Analyzes the PDF using a hybrid approach of pattern matching, font analysis,
    and heuristic filtering to extract a highly accurate structured outline.
    """
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:
        print(f"Error opening {pdf_path}: {e}")
        return {"title": os.path.basename(pdf_path), "outline": []}

    if doc.page_count == 0:
        doc.close()
        return {"title": os.path.basename(pdf_path), "outline": []}

    # --- Part 1: Header, Footer, and Style Analysis ---
    header_footer_candidates = defaultdict(list)
    for page in doc:
        header_y_threshold = page.rect.height * 0.15
        footer_y_threshold = page.rect.height * 0.85
        blocks = page.get_text("dict", flags=pymupdf.TEXT_INHIBIT_SPACES)["blocks"]
        for b in blocks:
            if b['type'] == 0 and 'lines' in b:
                block_y0 = b['bbox'][1]
                if block_y0 < header_y_threshold or block_y0 > footer_y_threshold:
                    block_text = " ".join([s['text'] for l in b['lines'] for s in l['spans']]).strip()
                    if len(block_text.split()) < 10:
                        header_footer_candidates[block_text].append(page.number)
    
    header_footer_set = {text for text, pages in header_footer_candidates.items() if len(set(pages)) >= 2}

    styles = {}
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if b['type'] == 0 and 'lines' in b:
                block_text = " ".join([s['text'] for l in b['lines'] for s in l['spans']]).strip()
                if block_text in header_footer_set: continue
                for l in b['lines']:
                    for s in l['spans']:
                        size = round(s['size'])
                        is_bold = "bold" in s['font'].lower()
                        style = (size, is_bold)
                        styles[style] = styles.get(style, 0) + 1

    body_style = max(styles, key=styles.get) if styles else (0, False)
    
    # --- Part 2: Pre-calculate Heading Levels ---
    prominent_styles = [s for s in styles if s[0] > body_style[0] or (s[0] == body_style[0] and s[1] and not body_style[1])]
    prominent_styles.sort(key=lambda x: (x[0], x[1]), reverse=True)
    style_to_level = {style: f"H{i+1}" for i, style in enumerate(prominent_styles[:5])}

    # --- Part 3: Title and Outline Extraction ---
    outline = []
    title = ""
    if doc.page_count > 0:
        # UPDATED: More robust title extraction logic
        first_page_blocks = doc[0].get_text("dict")["blocks"]
        title_candidates = []
        max_font_size = 0
        
        # Find max font size on the first page
        for b in first_page_blocks:
            if b['type'] == 0 and 'lines' in b and b['lines'][0]['spans']:
                size = b['lines'][0]['spans'][0]['size']
                if size > max_font_size:
                    max_font_size = size
        
        # Collect all blocks with a font size close to the max
        for b in first_page_blocks:
            if b['type'] == 0 and 'lines' in b and b['lines'][0]['spans']:
                span = b['lines'][0]['spans'][0]
                if abs(span['size'] - max_font_size) < 1:
                    title_candidates.append((b['bbox'][1], " ".join(s['text'] for l in b['lines'] for s in l['spans'])))

        # Sort by vertical position and join to form the title
        if title_candidates:
            title_candidates.sort()
            title = " ".join([text for y, text in title_candidates]).strip()


    heading_pattern = re.compile(r"^\s*([A-Z0-9]+(\.[0-9]+)*)\.?\s+([\s\S]+)|^(Chapter\s+\d+:.*|Appendix\s+[A-Z]:?.*|Summary|Introduction|Background|Conclusion|References|Mission\s+Statement:|Goals:|Timeline:)", re.IGNORECASE)
    # UPDATED: Stronger pattern to exclude list items
    list_item_pattern = re.compile(r"^\s*(\d+\.\s|[a-z]\)|\•|AFM\d+|[-–—])|:\s*$", re.IGNORECASE)
    noise_pattern = re.compile(r"copyright ©|version \d|\d{4}|page \d+ of \d+|international software testing|istqb|foundation level extension", re.IGNORECASE)
    toc_page_num_pattern = re.compile(r'[\. ]{3,}\s*\d+\s*$|\s+\d+\s*$')

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if b['type'] == 0 and 'lines' in b:
                is_toc_block = len(b['lines']) > 1 and page_num < 5
                text_units = b['lines'] if is_toc_block else [b]

                for unit in text_units:
                    spans = [s for l in unit.get('lines', []) for s in l.get('spans', [])]
                    if not spans: continue
                        
                    raw_text = "".join([s['text'] for s in spans]).strip()
                    text = toc_page_num_pattern.sub('', raw_text).strip()

                    if not text or text == title or text in header_footer_set or noise_pattern.search(text):
                        continue
                    
                    if list_item_pattern.match(text):
                        continue

                    first_span = spans[0]
                    is_bold = "bold" in first_span['font'].lower()

                    # UPDATED: Stricter filtering for paragraphs and sentences
                    is_paragraph = (len(unit.get('lines', [])) > 1 and not is_bold)
                    is_sentence = (text.endswith('.') and not is_bold and len(text.split()) > 5)
                    if is_paragraph or is_sentence:
                        continue
                    
                    if len(text.split()) > 15:
                        continue

                    match = heading_pattern.match(text)
                    if match:
                        number_part = match.group(1)
                        keyword_part = match.group(0)
                        
                        if number_part:
                            level = f"H{number_part.count('.') + 1}"
                        elif keyword_part.lower().startswith(("chapter", "appendix")):
                             level = "H2"
                        else:
                            level = "H1"
                            
                        outline.append({"level": level, "text": text, "page": page_num + 1})
                        continue

                    size = round(first_span['size'])
                    style = (size, is_bold)

                    if style in style_to_level:
                        level = style_to_level[style]
                        outline.append({"level": level, "text": text, "page": page_num + 1})

    if not title:
        title = os.path.basename(pdf_path) if not outline else outline[0]['text']

    doc.close()
    return {"title": title, "outline": outline}

def main():
    """
    Main function to process all PDFs in the input directory.
    """
    print("--- Starting Batch Processing (Advanced Heuristic) ---")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]
    
    for fname in pdf_files:
        input_path = os.path.join(INPUT_DIR, fname)
        print(f"Analyzing '{fname}'...")
        
        output = analyze_document_structure_advanced(input_path)
        
        json_fname = re.sub('(?i)\.pdf$', '.json', fname)
        out_path = os.path.join(OUTPUT_DIR, json_fname)
        
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=4)
        print(f"  -> Successfully created '{out_path}'")
        
    print("--- Batch Processing Complete ---")


if __name__ == "__main__":
    main()
