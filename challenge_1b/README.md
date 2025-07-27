# Approach Explanation: A Generic Persona-Driven Document Intelligence System

Our system acts as an intelligent document analyst, built to be generic and adaptable to any collection of documents and any user context. It extracts and prioritizes the most relevant information based on a specific persona and their job-to-be-done, ensuring the output is always a tailored and actionable set of insights.

## Methodology

Our methodology is designed for flexibility and efficiency, adhering to strict performance and resource constraints.

### 1. Dynamic Keyword Generation
The process begins by dynamically analyzing the **persona** and **job-to-be-done** from the input JSON. The system extracts key nouns and verbs from these descriptions, filtering out common stop words. These extracted terms become the weighted keywords for the analysis. This ensures that the system's focus is always aligned with the user's specific goals, whether they are a "Financial Analyst" examining "revenue trends" or a "Medical Researcher" studying "protein interactions."

### 2. Document Parsing and Sectioning
The system is designed to handle any text-based PDF. It extracts the raw text from each document and employs a robust heuristic-based approach to identify sections. This method looks for common structural patterns like short, title-cased lines that are not part of a paragraph. This allows us to segment diverse document formats (e.g., financial reports, academic papers, travel guides) into meaningful sections without prior knowledge of their structure.

### 3. Contextual Relevance Scoring and Ranking
Each identified section is scored for its relevance to the user's task using the dynamically generated keywords. We assign a higher weight to keywords found in a section's title, as this is a strong indicator of its topic. Sections are then ranked by this score, and the top 5 are presented as the most important, providing the user with immediate access to the most critical information.

### 4. Extractive Subsection Analysis
To meet the system constraints (CPU-only, small footprint), we avoid large generative models for summarization. Instead, we have implemented an **extractive summarization** technique for the subsection analysis. For each top-ranking section, the system analyzes its content sentence by sentence, scoring each one against the dynamic keywords. The highest-scoring sentences are then extracted and combined to form a concise, relevant "refined_text." This provides the user with a quick summary of the most important points within a section without fabricating information.

## Conclusion
This generic approach ensures our system is a powerful and versatile tool. By dynamically adapting its analysis based on the user's context and using efficient, extractive techniques, it can deliver highly relevant, persona-driven insights from any collection of documents, all while adhering to strict performance and resource limitations.