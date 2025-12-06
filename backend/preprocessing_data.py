"""
STEP 1: DATA PREPARATION
------------------------
Purpose: 
    Reads the raw metadata and the referenced PDF_JSON files.
    Extracts the bibliography with FULL details and formatted authors.
    Saves a single, clean JSON file containing EVERYTHING (Metadata + References).
    
    Output: 'ready_for_indexing.json'
"""

import json
import os
from tqdm import tqdm

# CONFIGURATION
INPUT_METADATA = "../datasets/metadata_sample.json"
DATASET_ROOT = "../datasets/CORD-19-research-challenge/"
OUTPUT_FILE = "../datasets/ready_for_indexing.json"

def format_author_name(author_dict: dict) -> str:
    """
    Converts structured author dict to string: 'Last, First Middle'
    Example: {'first': 'C', 'last': 'Reusken', 'middle': ['B']} -> 'Reusken, C B'
    """
    if not isinstance(author_dict, dict):
        return ""

    first = author_dict.get("first", "")
    # Middle is often a list ["B", "E"], join them with spaces
    middle_list = author_dict.get("middle", [])
    middle = " ".join(middle_list) if isinstance(middle_list, list) else ""
    last = author_dict.get("last", "")
    suffix = author_dict.get("suffix", "")

    # Logic: "Last, First Middle Suffix"
    # We build the "First Middle Suffix" part first
    given_names_parts = [p for p in [first, middle, suffix] if p]
    given_names_str = " ".join(given_names_parts)

    if last and given_names_str:
        return f"{last}, {given_names_str}"
    elif last:
        return last
    elif given_names_str:
        return given_names_str
    return ""

def format_authors_list(authors_list: list) -> str:
    """Joins multiple authors with semicolons: 'Auth1; Auth2; Auth3'"""
    if not isinstance(authors_list, list):
        return ""
    
    formatted_names = [format_author_name(a) for a in authors_list]
    # Filter out empty strings
    formatted_names = [n for n in formatted_names if n]
    
    return "; ".join(formatted_names)

def extract_references_from_json(relative_path: str) -> list:
    """Opens the detailed PDF JSON and extracts comprehensive citation info."""
    full_path = os.path.join(DATASET_ROOT, relative_path)
    print(f"Full path: {full_path}")
    
    if not os.path.exists(full_path):
        print(f"[WARM] {full_path} not exits !!")
        return []

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        bib_entries = data.get("bib_entries", {})
        refs = []
        
        # Parse references
        for ref_id, details in bib_entries.items():
            # 1. Format Authors
            raw_authors = details.get("authors", [])
            formatted_authors = format_authors_list(raw_authors)

            # 2. Extract DOI safely
            other_ids = details.get("other_ids", {})
            doi = ""
            if "DOI" in other_ids and isinstance(other_ids["DOI"], list) and len(other_ids["DOI"]) > 0:
                doi = other_ids["DOI"][0]

            # 3. Build Reference Object
            refs.append({
                "ref_id": ref_id,
                "title": details.get("title", ""),
                "year": details.get("year", None),
                "venue": details.get("venue", ""),
                "volume": details.get("volume", ""),
                "issn": details.get("issn", ""),
                "pages": details.get("pages", ""),
                "authors": formatted_authors,  # Merged string
                "doi": doi
            })
            
        return refs
    except Exception:
        # Silently fail for individual corrupt files to keep pipeline running
        return []

def run_pipeline():
    print(f"Reading raw metadata from {INPUT_METADATA}...")
    try:
        with open(INPUT_METADATA, 'r', encoding='utf-8') as f:
            raw_docs = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Could not find {INPUT_METADATA}")
        return

    processed_docs = []

    for doc in tqdm(raw_docs, desc="Processing References"):
        # 1. Basic Metadata
        clean_doc = {
            "cord_uid": doc.get("cord_uid"),
            "title": doc.get("title", ""),
            "abstract": doc.get("abstract", ""),
            "publish_time": doc.get("publish_time"),
            "url": doc.get("url"),
            "journal": doc.get("journal"),
            "authors": doc.get("authors"), # This is already a string in metadata
            "references": [] 
        }

        # 2. Extract References from external file
        pdf_json_rel_path = doc.get("pdf_json_files", "")
        if pdf_json_rel_path:
            # Handle multiple paths "path1; path2"
            first_file = pdf_json_rel_path.split(';')[0].strip()
            print(f"processing doc: {first_file}")
            if first_file:
                clean_doc["references"] = extract_references_from_json(first_file)
        
        processed_docs.append(clean_doc)

    print(f"Saving {len(processed_docs)} documents to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(processed_docs, f, indent=2)
        print(f"Save {OUTPUT_FILE} ...")
    print("Done! You can now run index_data.py using the ready_for_indexing.json to indexing data to Elasticsearch!!")

if __name__ == "__main__":
    run_pipeline()
    # full_path = "../datasets/CORD-19-research-challenge/document_parses/pdf_json/90eb9ce0e94e206ecc316829f32ea29560026748.json"
    # print(os.path.exists(full_path))