import json
import re
import datetime
import PyPDF2
import os
from collections import Counter
from string import punctuation

# Load stopwords with a fallback
try:
    import nltk
    nltk.download('stopwords', quiet=True)
    from nltk.corpus import stopwords
    STOP_WORDS = set(stopwords.words('english'))
except ImportError:
    print("[Warning] NLTK not found. Using a basic list of stopwords.")
    STOP_WORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he',
        'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were',
        'will', 'with', 'i', 'you', 'my', 'your', 'me', 'this', 'guide', 'document'
    }

def clean_text(text):
    """Removes punctuation and converts to lowercase for scoring."""
    return re.sub(rf"[{re.escape(punctuation)}]", "", text.lower())

def generate_keywords(persona, task):
    """Dynamically generates keywords from the persona and task."""
    print("[+] Generating keywords...")
    combined = f"{persona} {task}".lower()
    words = re.findall(r'\b\w{4,}\b', combined) # Find words with 4+ letters
    keywords = {word: 10 for word in words if word not in STOP_WORDS}
    print(f"[+] Keywords: {list(keywords.keys())}")
    return keywords

def extract_text_from_pdf(file_path):
    """Extracts text and page number from each page of a PDF."""
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]
    except Exception as e:
        print(f"[!] Error reading {file_path}: {e}")
        return []

def extract_sections(pages):
    """Extracts sections using a more robust title-finding heuristic."""
    print("[+] Detecting sections...")
    sections = []
    # A title is likely short, capitalized, and not a full sentence.
    title_pattern = re.compile(r"^[A-Z][A-Za-z0-9\s,&-]{3,80}$")

    current_title = "Introduction"
    current_content = ""
    current_page = 1

    for page_num, text in pages:
        lines = text.split('\n')
        for line in lines:
            stripped_line = line.strip()
            # Check if the line is a likely title
            if title_pattern.match(stripped_line) and not stripped_line.endswith('.') and len(stripped_line.split()) < 12:
                if current_content.strip():
                    sections.append({'title': current_title, 'content': current_content.strip(), 'page': current_page})
                current_title = stripped_line
                current_content = ""
                current_page = page_num
            else:
                current_content += line + "\n"

    if current_content.strip():
        sections.append({'title': current_title, 'content': current_content.strip(), 'page': current_page})

    print(f"[+] Sections found: {len(sections)}")
    return sections

def score_section(section, keywords):
    """Scores a section based on keyword density and title match."""
    content = clean_text(section['content'])
    title = clean_text(section['title'])
    words_in_content = content.split()
    
    if not words_in_content:
        return 0

    # Score based on keyword counts, with title keywords being more valuable
    score = sum(content.count(k) * w + title.count(k) * w * 5 for k, w in keywords.items())
    score /= len(words_in_content) # Normalize by content length to get density

    if title.strip().lower() in {"introduction", "conclusion", "references", "appendix"}:
        score *= 0.5 # Penalize generic sections
    return score

def find_best_subsection(section_title, content, keywords):
    """Finds the most relevant paragraph and prepends the section title for context."""
    subsections = re.split(r'\n\s*\n', content) # Split by blank lines
    best_sub = ""
    best_score = -1

    for sub in subsections:
        sub_cleaned = sub.strip()
        if not sub_cleaned or len(sub_cleaned) < 50: # Ignore short fragments
            continue

        words = re.findall(r'\b\w+\b', clean_text(sub_cleaned))
        if not words:
            continue

        # Score based on keyword density
        word_counts = Counter(words)
        score = sum(word_counts.get(k, 0) * w for k, w in keywords.items())
        score /= len(words)

        # Boost score for lists, as they are often summaries
        if '•' in sub_cleaned or '*' in sub_cleaned or re.match(r'^\d+\.', sub_cleaned):
            score *= 1.5

        if score > best_score:
            best_score = score
            best_sub = sub_cleaned

    # If no suitable subsection is found, use the beginning of the content
    if not best_sub:
        best_sub = content.strip()[:500]
        
    # Return the content with the section title for context
    return f"{section_title}\n\n{best_sub}"

def process_documents(input_filename):
    """Main processing function."""
    with open(os.path.join("input", input_filename), 'r', encoding='utf-8') as f:
        data = json.load(f)

    persona = data['persona']['role']
    job = data['job_to_be_done']['task']
    keywords = generate_keywords(persona, job)

    top_sections_from_all_docs = []

    for doc in data['documents']:
        filename = doc['filename']
        print(f"\n[+] Processing: {filename}")
        pages = extract_text_from_pdf(os.path.join("input", filename))
        if not pages:
            continue

        sections = extract_sections(pages)
        
        scored_sections_for_this_doc = []
        for sec in sections:
            score = score_section(sec, keywords)
            if score > 0.05: # Lower threshold to ensure we capture relevant sections
                sec.update({'score': score, 'document': filename})
                scored_sections_for_this_doc.append(sec)
        
        # Sort sections for this document and get the top 2
        sorted_sections = sorted(scored_sections_for_this_doc, key=lambda x: x['score'], reverse=True)
        top_sections_from_all_docs.extend(sorted_sections[:2])
        print(f"[+] Selected top {len(sorted_sections[:2])} sections from {filename}")

    # Globally rank all the selected top sections
    globally_ranked_sections = sorted(top_sections_from_all_docs, key=lambda x: x['score'], reverse=True)

    results = {
        "metadata": {
            "input_documents": [doc['filename'] for doc in data['documents']],
            "persona": persona,
            "job_to_be_done": job,
            "processing_timestamp": datetime.datetime.now().isoformat()
        },
        "extracted_sections": [],
        "subsection_analysis": []
    }

    # Populate the final output with the globally ranked sections
    for i, sec in enumerate(globally_ranked_sections):
        results["extracted_sections"].append({
            "document": sec['document'],
            "section_title": sec['title'],
            "importance_rank": i + 1,
            "page_number": sec['page']
        })

        # Generate the contextual refined_text
        contextual_subsection = find_best_subsection(sec['title'], sec['content'], keywords)
        results["subsection_analysis"].append({
            "document": sec['document'],
            "refined_text": re.sub(r'\\', '', contextual_subsection), # Clean stray backslashes
            "page_number": sec['page']
        })

    return results

if __name__ == "__main__":
    input_file = 'challenge1b_input.json'
    output_file = os.path.join("output", "challenge1b_output.json")

    print("[INFO] Starting processing...")
    result = process_documents(input_file)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4, ensure_ascii=False)

    print(f"\n[DONE] Output saved to {output_file}")