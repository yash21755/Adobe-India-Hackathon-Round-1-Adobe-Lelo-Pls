import json
import re
import datetime
import PyPDF2
import io

# A simple list of common English stop words.
STOP_WORDS = {
    'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he',
    'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were',
    'will', 'with', 'i', 'you', 'my', 'your', 'me'
}

def generate_keywords(persona, job_to_be_done):
    """
    Dynamically generates keywords from the persona and job description.
    """
    text = (persona + ' ' + job_to_be_done).lower()
    # Remove punctuation and split into words
    words = re.findall(r'\b\w+\b', text)
    # Filter out stop words and short words
    keywords = {
        word: 10 for word in words
        if word not in STOP_WORDS and len(word) > 3
    }
    return keywords

def extract_text_from_pdf(file_path):
    """
    Extracts text content from a given PDF file.
    """
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return ""

def extract_sections(document_content):
    """
    Extracts sections using a heuristic to find titles.
    """
    sections = {}
    # Use a placeholder for content before the first proper title
    current_title = "Introduction"
    current_content = ""
    page_number = 1 # Simplified page tracking for generic text

    lines = document_content.split('\n')
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        # Heuristic for a title: A short line (less than 10 words),
        # often in title case, and not ending with a period.
        if 0 < len(line_stripped) < 70 and line_stripped.istitle() and not line_stripped.endswith('.'):
             if current_content.strip():
                sections[current_title] = {'content': current_content.strip(), 'page': page_number}
             current_title = line_stripped
             current_content = ""
        else:
            current_content += line + '\n'

    # Add the last section
    if current_title not in sections and current_content.strip():
        sections[current_title] = {'content': current_content.strip(), 'page': page_number}
    return sections


def get_relevance_score(title, content, keywords):
    """
    Calculates a relevance score for a section based on keywords.
    """
    score = 0
    title_text = title.lower()
    content_text = content.lower()
    for keyword, weight in keywords.items():
        # Higher score for keywords in the title
        if re.search(r'\b' + re.escape(keyword) + r'\b', title_text):
            score += weight * 5
        # Score based on frequency in content
        score += weight * len(re.findall(r'\b' + re.escape(keyword) + r'\b', content_text))
    return score

def get_refined_subsection(content, keywords):
    """
    Performs extractive summarization to find the most relevant sentences.
    """
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', content)
    scored_sentences = []
    for sentence in sentences:
        if not sentence.strip():
            continue
        score = 0
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', sentence.lower()):
                score += 1
        if score > 0:
            scored_sentences.append({'sentence': sentence.strip(), 'score': score})

    # Sort sentences by score and return the top 2 as the "refined text"
    scored_sentences.sort(key=lambda x: x['score'], reverse=True)
    refined_text = " ".join([s['sentence'] for s in scored_sentences[:2]])
    return refined_text if refined_text else content.strip()[:300] # Fallback


def process_documents(input_file_path):
    """
    Main processing function.
    """
    with open(input_file_path, 'r') as f:
        input_data = json.load(f)

    persona = input_data['persona']['role']
    job_to_be_done = input_data['job_to_be_done']['task']
    keywords = generate_keywords(persona, job_to_be_done)

    all_sections = []
    for doc in input_data['documents']:
        filename = doc['filename']
        full_text = extract_text_from_pdf(filename)
        if not full_text:
            continue

        sections = extract_sections(full_text)
        for title, data in sections.items():
            score = get_relevance_score(title, data['content'], keywords)
            if score > 10:  # Relevance threshold
                all_sections.append({
                    "document": filename,
                    "section_title": title,
                    "importance_rank": score,
                    "page_number": data['page'],
                    "content": data['content']
                })

    # Sort sections by importance (higher score is better)
    sorted_sections = sorted(all_sections, key=lambda x: x['importance_rank'], reverse=True)

    # Prepare the output JSON
    output = {
        "metadata": {
            "input_documents": [doc['filename'] for doc in input_data['documents']],
            "persona": persona,
            "job_to_be_done": job_to_be_done,
            "processing_timestamp": datetime.datetime.now().isoformat()
        },
        "extracted_sections": [],
        "subsection_analysis": []
    }

    # Populate extracted_sections (Top 5)
    for i, section in enumerate(sorted_sections[:5]):
        output["extracted_sections"].append({
            "document": section['document'],
            "section_title": section['section_title'],
            "importance_rank": i + 1,
            "page_number": section['page_number']
        })

    # Populate subsection_analysis with extractive summaries (Top 5)
    for section in sorted_sections[:5]:
        refined_text = get_refined_subsection(section['content'], keywords)
        output["subsection_analysis"].append({
            "document": section['document'],
            "refined_text": refined_text,
            "page_number": section['page_number']
        })

    return output

if __name__ == '__main__':
    input_json_path = 'challenge1b_input.json'
    output_json_path = 'challenge1b_output.json'
    result = process_documents(input_json_path)
    with open(output_json_path, 'w') as f:
        json.dump(result, f, indent=4)
    print(f"Processing complete. Output written to {output_json_path}")