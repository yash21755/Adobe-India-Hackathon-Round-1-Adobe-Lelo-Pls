# Challenge 1B: Persona-Driven Document Intelligence System

This project is a solution for the "Persona-Driven Document Intelligence" challenge. It acts as an intelligent document analyst that processes a collection of PDF documents and extracts the most relevant sections based on a specific user persona and their "job-to-be-done."

The system is designed to be **generic and context-aware**, capable of handling documents from any domain (e.g., travel, finance, research) and adapting its analysis to any user task.

## The Idea: A Two-Pass Anchor Mechanism

The core of this solution is an intelligent **two-pass anchor mechanism**, designed to mimic how a human expert would approach a research task. Instead of just searching for keywords, the system first establishes a core theme and then finds details that are contextually related to that theme.

### Pass 1: Finding the "Anchor"

The script begins by performing a high-level analysis of all provided documents. It uses the primary keywords from the user's `job_to_be_done` to identify the single most relevant document in the collection. This document becomes the **"anchor"**, establishing the central topic for the entire analysis.

### Pass 2: Finding Contextually Related Details

Once the anchor is established, the script analyzes it to extract new, **contextual keywords** by identifying frequently occurring proper nouns. These new keywords are then added to the search criteria.

The script then performs its main analysis of all documents, now looking for sections that relate to both the original task and the specific details found in the anchor document.

## Methodology

Our methodology is designed for flexibility and efficiency, adhering to strict performance and resource constraints.

### 1. Dynamic Keyword Generation
Dynamically extracts weighted keywords from persona and job-to-be-done.

### 2. Document Parsing and Sectioning
Heuristic-based parsing to extract structured sections from any PDF.

### 3. Relevance Scoring and Ranking
Ranks sections using weighted keyword matches to titles and body.

### 4. Extractive Subsection Analysis
Highlights most relevant sentences using extractive summarization.

## File Structure

```
/your_project_directory/
├── input/
│   ├── challenge1b_input.json
│   ├── document_A.pdf
│   └── document_B.pdf
├── output/
│   └── challenge1b_output.json
├── generic_planner.py
├── dockerfile
└── requirements.txt
```

## How to Run the System

### Prerequisites

- [Docker](https://www.docker.com/get-started) must be installed and running.


### Step 1: Build the Docker Image

```bash
docker build -t doc-analyzer .
```

### Step 2: Run the Container

```bash
docker run --name final-run doc-analyzer
```

### Step 3: Copy the Output File

```bash
docker cp final-run:/app/output/challenge1b_output.json ./output/
```

### Step 4: Clean Up

```bash
docker rm final-run
```

## Libraries and Dependencies

- `PyPDF2`: For PDF text extraction.
- `NLTK`: (optional) Used for stopword removal.

---

© 2025 Adobe Hackathon Submission - Team Adobe Lelo Pls