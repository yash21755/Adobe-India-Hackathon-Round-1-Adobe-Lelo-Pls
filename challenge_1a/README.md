## Challenge 1A: Structured Outline Extraction from PDF Documents

This repository contains the solution for **Challenge 1A** of the Adobe India Hackathon. The challenge involves parsing a collection of PDF documents and automatically extracting a structured outline that includes the document title and hierarchical headings (H1, H2, H3), along with their respective page numbers.

The extracted outlines enable intelligent document understanding and support downstream tasks such as summarization, search, and semantic indexing.

## Problem Statement

Given a set of unstructured PDF documents, the system should identify and extract the following information:

- The document title
- Headings and subheadings, categorized into heading levels (H1, H2, H3)
- Page numbers associated with each heading

## Methodology

This solution is designed to be robust and domain-agnostic. It leverages visual and structural cues present in PDF layouts to accurately identify and organize content.

### 1. PDF Parsing

- The system uses the **PyMuPDF (fitz)** library to parse the visual layout of each PDF document.
- For each page, it extracts individual text blocks along with their associated metadata such as font size, font weight, coordinates, and alignment.

### 2. Title Detection

- The document title is inferred based on visual prominence.
- The system scans the first page and selects the text block with the largest font size (typically bold and centered) as the title.
- If multiple candidates exist, heuristics such as vertical position and length are used for disambiguation.

### 3. Heading Classification

- Headings are identified based on relative font size and style within the document.
- A clustering algorithm is used to group font sizes into three categories, which are then mapped to heading levels H1, H2, and H3.
- Each heading is tagged with its level and the page number on which it appears.

### 4. Structured Outline Generation

- The extracted headings and their levels are organized into a nested structure representing the document hierarchy.
- Each heading entry includes the text, level, and page number.
- The complete outline is saved in a clean and interpretable JSON format.

## File Structure

```text
project_root/
├── input/
│   └── [PDF files]
├── output/
│   └── [Extracted JSON files]
├── process_pdfs.py        # Main processing script
├── dockerfile             # Dockerfile to build the image
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## How to Run

The project is containerized using Docker to ensure reproducibility and ease of execution.

### Prerequisites

- [Docker](https://www.docker.com/get-started) must be installed and running on your system.

### Step 1: Build the Docker Image

Navigate to the project root directory and build the Docker image:

```bash
docker build -t outline-extractor .
```

### Step 2: Run the Container

Use the following command to run the container and generate outlines for all PDF files in the `input/` folder:

```bash
docker run --rm -v "%cd%\input:/app/input" -v "%cd%\output:/app/output" outline-extractor
```

### Output

- The system will generate one `.json` file per PDF in the `output/` directory.
- Each output JSON contains:
  - `title`: The inferred document title
  - `outline`: A list of headings with their `level` (H1, H2, H3), `text`, and `page`

### Sample Output

```json
{
    "title": "Parsippany -Troy Hills STEM Pathways",
    "outline": [
        {
            "level": "H1",
            "text": "PATHWAY OPTIONS",
            "page": 1
        },
        {
            "level": "H1",
            "text": "REGULAR PATHWAY",
            "page": 1
        },
        {
            "level": "H1",
            "text": "Goals:",
            "page": 1
        }
    ]
}
```

## Dependencies

The required Python libraries are listed in `requirements.txt` and are installed automatically during the Docker build:

- `PyMuPDF`
- `scikit-learn`
- `numpy`
- `matplotlib`

## Summary

This solution demonstrates an effective method to programmatically extract structured outlines from visually diverse PDF documents. It is generalizable, robust, and designed to work without prior knowledge of the document format. The output format is consistent and machine-readable, enabling further automation and integration into intelligent document processing pipelines.

---

© 2025 Adobe Hackathon Submission - Team Adobe Lelo Pls