"""
Raw Text API - Enhanced Version
--------------------------------
Endpoint to retrieve full text content from CORD-19 JSON files (PDF or PMC sources).

Input:
    - path: Relative path to JSON file (e.g., document_parses/pdf_json/<sha>.json)

Output:
    - JSON content with title, authors, sections (grouped paragraphs), tables, etc.
"""

import os
import json
from collections import OrderedDict
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional

router = APIRouter()

# Base path for CORD-19 dataset - configure via environment variable
CORD19_DATASET_PATH = os.environ.get(
    "CORD19_DATASET_PATH", 
    r"E:\minhbh\HCMUT\251-big-data\cord19_dataset"
)


def validate_path(path: str) -> bool:
    """
    Validate the path to prevent directory traversal attacks.
    Only allow paths that start with 'document_parses/'
    """
    if not path:
        return False
    
    # Normalize path (handle both / and \)
    normalized = path.replace("\\", "/")
    
    # Check for directory traversal
    if ".." in normalized:
        return False
    
    # Must start with document_parses/
    if not normalized.startswith("document_parses/"):
        return False
    
    # Must end with .json
    if not normalized.endswith(".json"):
        return False
    
    return True


def get_full_path(relative_path: str) -> str:
    """
    Convert relative path to full filesystem path.
    """
    # Normalize path separators for Windows
    normalized_path = relative_path.replace("/", os.sep)
    return os.path.join(CORD19_DATASET_PATH, normalized_path)


def detect_source_type(paper_id: str, path: str) -> str:
    """
    Detect if source is PMC or PDF based on paper_id or path.
    """
    if "pmc_json" in path.lower():
        return "pmc"
    if paper_id.upper().startswith("PMC"):
        return "pmc"
    return "pdf"


def extract_authors(metadata: Dict) -> List[Dict[str, str]]:
    """
    Extract authors from metadata.
    """
    authors = []
    raw_authors = metadata.get("authors", [])
    
    for author in raw_authors:
        if isinstance(author, dict):
            # Build full name
            first = author.get("first", "")
            middle = " ".join(author.get("middle", []))
            last = author.get("last", "")
            
            name_parts = [first, middle, last]
            full_name = " ".join(part for part in name_parts if part)
            
            if full_name:
                authors.append({
                    "name": full_name,
                    "email": author.get("email", "")
                })
    
    return authors


def group_paragraphs_by_section(body_text: List[Dict]) -> List[Dict[str, Any]]:
    """
    Group paragraphs by their section name.
    Returns ordered list of sections with their paragraphs.
    """
    if not body_text:
        return []
    
    # Use OrderedDict to maintain section order
    sections = OrderedDict()
    
    for para in body_text:
        section_name = para.get("section", "").strip() or "Content"
        text = para.get("text", "").strip()
        
        if not text:
            continue
        
        # Check if paragraph has citations
        has_citations = bool(para.get("cite_spans", []))
        
        if section_name not in sections:
            sections[section_name] = {
                "title": section_name,
                "paragraphs": []
            }
        
        sections[section_name]["paragraphs"].append({
            "text": text,
            "has_citations": has_citations
        })
    
    return list(sections.values())


def extract_tables(ref_entries: Dict) -> List[Dict[str, str]]:
    """
    Extract table information from ref_entries.
    """
    tables = []
    
    for ref_id, ref_data in ref_entries.items():
        if isinstance(ref_data, dict):
            ref_type = ref_data.get("type", "").lower()
            if ref_type == "table":
                tables.append({
                    "id": ref_id,
                    "caption": ref_data.get("text", "")
                })
    
    return tables


def extract_abstract(abstract_data: List[Dict]) -> List[Dict[str, str]]:
    """
    Extract abstract paragraphs.
    """
    if not abstract_data or not isinstance(abstract_data, list):
        return []
    
    return [
        {
            "text": para.get("text", "").strip(),
            "section": para.get("section", "")
        }
        for para in abstract_data
        if para.get("text", "").strip()
    ]


@router.get("/raw-text")
async def get_raw_text(
    path: str = Query(..., description="Relative path to JSON file")
):
    """
    Retrieve full text content from a CORD-19 JSON file.
    
    The path should be in format:
    - document_parses/pdf_json/<sha>.json
    - document_parses/pmc_json/<pmcid>.xml.json
    """
    # Validate path
    if not validate_path(path):
        raise HTTPException(
            status_code=400, 
            detail="Invalid path. Path must start with 'document_parses/' and end with '.json'"
        )
    
    # Get full path
    full_path = get_full_path(path)
    
    # Check if file exists
    if not os.path.exists(full_path):
        raise HTTPException(
            status_code=404,
            detail=f"Content file not found. Please ensure the dataset is available at the configured path."
        )
    
    # Read and parse content
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        # Extract metadata
        paper_id = content.get("paper_id", "")
        metadata = content.get("metadata", {})
        
        # Build response
        response = {
            "paper_id": paper_id,
            "source_type": detect_source_type(paper_id, path),
            "title": metadata.get("title", "Untitled"),
            "authors": extract_authors(metadata),
            "abstract": extract_abstract(content.get("abstract", [])),
            "sections": group_paragraphs_by_section(content.get("body_text", [])),
            "tables": extract_tables(content.get("ref_entries", {})),
            "references_count": len(content.get("bib_entries", {}))
        }
        
        return response
        
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="Failed to parse content file"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading content: {str(e)}"
        )
