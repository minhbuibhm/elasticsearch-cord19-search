from fastapi import APIRouter, HTTPException
from typing import List
import json
import os
from datetime import datetime

from app.models import SearchRequest, SearchResponse, ArticleSnippet

router = APIRouter()

# Load mock data
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "mock_cord19.json")

def load_papers():
    """Load papers from mock data file"""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_similarity(query: str, paper: dict) -> float:
    """
    Calculate similarity score between query and paper
    Simple keyword-based similarity for demo purposes
    In production, this would use semantic embeddings
    """
    query_lower = query.lower()
    query_words = set(query_lower.split())

    # Combine title and abstract for searching
    text = (paper['title'] + ' ' + paper['abstract']).lower()

    # Count matching words
    matching_words = sum(1 for word in query_words if word in text)

    # Calculate base similarity
    if len(query_words) == 0:
        return 0.5

    base_score = matching_words / len(query_words)

    # Boost score if query appears as phrase in title
    if query_lower in paper['title'].lower():
        base_score += 0.3

    # Boost score if query appears as phrase in abstract
    if query_lower in paper['abstract'].lower():
        base_score += 0.2

    # Normalize to 0-1 range
    return min(base_score, 1.0)

def filter_by_time(paper: dict, time_range: dict) -> bool:
    """Filter papers by publication date"""
    if time_range['type'] == 'any':
        return True

    pub_date = paper.get('publish_time')
    if not pub_date:
        return True

    paper_year = int(pub_date.split('-')[0])

    if time_range['type'] == 'since':
        if time_range['value']:
            since_year = int(time_range['value'])
            return paper_year >= since_year
        return True

    elif time_range['type'] == 'range':
        if time_range['start'] and time_range['end']:
            start_year = int(time_range['start'].split('-')[0])
            end_year = int(time_range['end'].split('-')[0])
            return start_year <= paper_year <= end_year
        return True

    return True

def truncate_abstract(abstract: str, max_length: int = 200) -> str:
    """Truncate abstract for snippet display"""
    if len(abstract) <= max_length:
        return abstract
    return abstract[:max_length].rsplit(' ', 1)[0] + '...'

@router.post("/search", response_model=SearchResponse)
async def search_papers(request: SearchRequest):
    """
    Search research papers with advanced filters
    """
    papers = load_papers()

    # Calculate similarity scores
    results = []
    for paper in papers:
        similarity = calculate_similarity(request.query, paper)

        # Apply minimum similarity threshold
        if similarity < 0.1:
            continue

        # Apply time filter
        if not filter_by_time(paper, request.advanced_filters.time_range.dict()):
            continue

        # For demo, we're assuming all papers are research related
        # In production, you'd filter by paper type/category

        results.append({
            'paper': paper,
            'similarity': similarity
        })

    # Sort results
    if request.advanced_filters.sort_by == 'relevance':
        results.sort(key=lambda x: x['similarity'], reverse=True)
    elif request.advanced_filters.sort_by == 'date':
        results.sort(key=lambda x: x['paper'].get('publish_time', ''), reverse=True)

    # Pagination
    page = request.pagination.get('page', 1)
    size = request.pagination.get('size', 10)
    total_results = len(results)
    total_pages = (total_results + size - 1) // size

    start_idx = (page - 1) * size
    end_idx = start_idx + size
    paginated_results = results[start_idx:end_idx]

    # Format response
    articles = []
    for item in paginated_results:
        paper = item['paper']
        articles.append(ArticleSnippet(
            id=paper['cord_uid'],
            similarity_score=round(item['similarity'], 2),
            title=paper['title'],
            authors=paper['authors'],
            journal=paper.get('journal'),
            publication_date=paper.get('publish_time'),
            abstract_snippet=truncate_abstract(paper['abstract'])
        ))

    return SearchResponse(
        pagination={
            'total_results': total_results,
            'page': page,
            'total_pages': total_pages,
            'size': size
        },
        results=articles
    )
