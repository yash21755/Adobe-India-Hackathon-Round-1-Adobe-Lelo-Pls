import json
import re
import datetime
import PyPDF2
import os
from collections import Counter
from string import punctuation

# Using a comprehensive fallback list of stopwords
STOP_WORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can', 'could', 'did', 'do', 'does', 'doing', 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', 'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'i', 'if', 'in', 'into', 'is', 'it', 'its', 'itself', 'just', 'me', 'more', 'most', 'my', 'myself', 'no', 'nor', 'not', 'now', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 's', 'same', 'she', 'should', 'so', 'some', 'such', 't', 'than', 'that', 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'these', 'they', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'we', 'were', 'what', 'when', 'where', 'which', 'while', 'who', 'whom', 'why', 'will', 'with', 'would', 'you', 'your', 'yours', 'yourself', 'yourselves', 'abstract', 'appendix', 'article', 'chapter', 'conclusion', 'copyright', 'data', 'details', 'document', 'due', 'example', 'figure', 'file', 'guide', 'image', 'information', 'introduction', 'issue', 'item', 'key', 'kind', 'level', 'method', 'model', 'note', 'number', 'page', 'paper', 'part', 'point', 'question', 'references', 'report', 'research', 'result', 'review', 'section', 'source', 'study', 'summary', 'table', 'term', 'text', 'topic', 'type', 'use', 'version', 'volume', 'analyze', 'create', 'define', 'describe', 'develop', 'evaluate', 'explain', 'find', 'identify', 'implement', 'plan', 'prepare', 'provide', 'summarize', 'understand'
}

def clean_text(text):
    """Removes punctuation and converts to lowercase for scoring."""
    return re.sub(rf"[{re.escape(punctuation)}]", "", text.lower())

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
    sections = []
    title_pattern = re.compile(r"^[A-Z][A-Za-z0-9\s,&'-]{3,90}$")
    current_title = "Introduction"
    current_content = ""
    current_page = 1

    for page_num, text in pages:
        lines = text.split('\n')
        for line in lines:
            stripped_line = line.strip()
            if title_pattern.match(stripped_line) and not stripped_line.endswith('.') and len(stripped_line.split()) < 15 and '  ' not in stripped_line:
                if current_content.strip():
                    sections.append({'title': current_title, 'content': current_content.strip(), 'page': current_page})
                current_title = stripped_line
                current_content = ""
                current_page = page_num
            else:
                current_content += line + "\n"
    if current_content.strip():
        sections.append({'title': current_title, 'content': current_content.strip(), 'page': current_page})
    return sections

def score_section(section, keywords):
    """Scores a section based on keyword density and title match."""
    content = clean_text(section['content'])
    title = clean_text(section['title'])
    words_in_content = content.split()
    if not words_in_content: return 0

    score = sum(content.count(k) * w + title.count(k) * w * 5 for k, w in keywords.items())
    score /= len(words_in_content)

    if title.strip().lower() in {"introduction", "conclusion", "references", "appendix", "overview"}:
        score *= 0.1
    return score

def find_best_subsection(section_title, content):
    """Finds the most meaningful paragraph and prepends the title for context."""
    subsections = re.split(r'\n\s*\n', content)
    best_sub = max(subsections, key=len) if subsections else ""
    return f"{section_title}\n\n{best_sub.strip()}"

def process_documents(input_filename):
    """Main processing function with two-pass analysis for contextual relevance."""
    with open(os.path.join("input", input_filename), 'r', encoding='utf-8') as f:
        data = json.load(f)

    persona = data['persona']['role']
    job = data['job_to_be_done']['task']

    # --- PASS 1: Find the Anchor/Core Theme ---
    print("\n[INFO] Pass 1: Finding the core theme...")
    primary_keywords = {word: 15 for word in clean_text(job).split() if word not in STOP_WORDS and len(word) > 3}
    print(f"[+] Primary Keywords: {list(primary_keywords.keys())}")
    
    all_docs_text = {}
    for doc in data['documents']:
        pages = extract_text_from_pdf(os.path.join("input", doc['filename']))
        all_docs_text[doc['filename']] = " ".join([page[1] for page in pages])

    doc_scores = {filename: sum(clean_text(text).count(kw) for kw in primary_keywords) for filename, text in all_docs_text.items()}
    anchor_doc_filename = max(doc_scores, key=doc_scores.get)
    anchor_doc_text = all_docs_text[anchor_doc_filename]
    print(f"[+] Anchor document found: {anchor_doc_filename}")

    # --- PASS 2: Re-score with Contextual Keywords ---
    print("\n[INFO] Pass 2: Analyzing all documents with contextual keywords...")
    # Extract new keywords (frequent proper nouns) from the anchor document
    contextual_keywords = {word.lower(): 10 for word, count in Counter(re.findall(r'\b[A-Z][a-z]{3,}\b', anchor_doc_text)).items() if count > 2 and word.lower() not in STOP_WORDS}
    print(f"[+] Contextual Keywords extracted: {list(contextual_keywords.keys())}")
    
    final_keywords = {**primary_keywords, **contextual_keywords}

    top_sections_from_all_docs = []
    for doc in data['documents']:
        filename = doc['filename']
        print(f"\n[+] Processing: {filename}")
        pages = extract_text_from_pdf(os.path.join("input", filename))
        if not pages: continue

        sections = extract_sections(pages)
        scored_sections = []
        for sec in sections:
            score = score_section(sec, final_keywords)
            if score > 0.1:
                sec.update({'score': score, 'document': filename})
                scored_sections.append(sec)
        
        sorted_sections = sorted(scored_sections, key=lambda x: x['score'], reverse=True)
        top_sections_from_all_docs.extend(sorted_sections[:2])
        print(f"[+] Selected top {len(sorted_sections[:2])} sections from {filename}")

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

    for i, sec in enumerate(globally_ranked_sections):
        results["extracted_sections"].append({
            "document": sec['document'],
            "section_title": sec['title'],
            "importance_rank": i + 1,
            "page_number": sec['page']
        })
        contextual_subsection = find_best_subsection(sec['title'], sec['content'])
        results["subsection_analysis"].append({
            "document": sec['document'],
            "refined_text": re.sub(r'\\', '', contextual_subsection),
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