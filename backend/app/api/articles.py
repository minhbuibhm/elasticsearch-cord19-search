from fastapi import APIRouter, HTTPException
from typing import List
import json
import os

from app.models import ArticleDetail, RelatedArticle, RelatedArticlesResponse

router = APIRouter()

# Load mock data
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "mock_cord19.json")

def load_papers():
    """Load papers from mock data file"""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_paper_similarity(paper1: dict, paper2: dict) -> float:
    """
    Calculate similarity between two papers based on keywords
    In production, this would use semantic embeddings
    """
    # Combine title and abstract
    text1 = (paper1['title'] + ' ' + paper1['abstract']).lower()
    text2 = (paper2['title'] + ' ' + paper2['abstract']).lower()

    # Simple word-based similarity
    words1 = set(text1.split())
    words2 = set(text2.split())

    # Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))

    if union == 0:
        return 0.0

    similarity = intersection / union

    # Boost if same authors
    authors1 = set(paper1['authors'])
    authors2 = set(paper2['authors'])
    if len(authors1.intersection(authors2)) > 0:
        similarity += 0.1

    return min(similarity, 1.0)

def truncate_abstract(abstract: str, max_length: int = 200) -> str:
    """Truncate abstract for snippet display"""
    if len(abstract) <= max_length:
        return abstract
    return abstract[:max_length].rsplit(' ', 1)[0] + '...'

@router.get("/{article_id}", response_model=ArticleDetail)
async def get_article_detail(article_id: str):
    """
    Get detailed information about a specific article
    """
    papers = load_papers()

    # Find the paper
    paper = None
    for p in papers:
        if p['cord_uid'] == article_id:
            paper = p
            break

    if not paper:
        raise HTTPException(status_code=404, detail="Article not found")

    # Return detailed information
    return ArticleDetail(
        id=paper['cord_uid'],
        title=paper['title'],
        authors=paper['authors'],
        full_abstract=paper['abstract'],
        journal=paper.get('journal'),
        publication_date=paper.get('publish_time'),
        full_text_url=paper.get('url'),
        clinical_trials=[],  # Mock data doesn't have this
        doi=paper.get('doi')
    )

@router.get("/{article_id}/related", response_model=RelatedArticlesResponse)
async def get_related_articles(article_id: str, limit: int = 5):
    """
    Get articles related to a specific article based on content similarity
    """
    papers = load_papers()

    # Find the source paper
    source_paper = None
    for p in papers:
        if p['cord_uid'] == article_id:
            source_paper = p
            break

    if not source_paper:
        raise HTTPException(status_code=404, detail="Article not found")

    # Calculate similarity with all other papers
    related = []
    for paper in papers:
        if paper['cord_uid'] == article_id:
            continue

        similarity = calculate_paper_similarity(source_paper, paper)
        related.append({
            'paper': paper,
            'similarity': similarity
        })

    # Sort by similarity and take top N
    related.sort(key=lambda x: x['similarity'], reverse=True)
    related = related[:limit]

    # Format response
    related_articles = []
    for item in related:
        paper = item['paper']
        related_articles.append(RelatedArticle(
            id=paper['cord_uid'],
            similarity_score=round(item['similarity'], 2),
            title=paper['title'],
            authors=paper['authors'],
            abstract_snippet=truncate_abstract(paper['abstract'])
        ))

    return RelatedArticlesResponse(
        article_id=article_id,
        related_papers=related_articles
    )
