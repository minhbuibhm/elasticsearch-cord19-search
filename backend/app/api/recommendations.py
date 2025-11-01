from fastapi import APIRouter, Depends
from typing import Dict, List
import json
import os

from app.models import RecommendedArticle, RecommendationsResponse
from app.auth.auth import verify_token, TokenData
from app.api.bookmarks import bookmarks_store

router = APIRouter()

# Load mock data
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "mock_cord19.json")

def load_papers():
    """Load papers from mock data file"""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_paper_similarity(paper1: dict, paper2: dict) -> float:
    """
    Calculate similarity between two papers
    """
    text1 = (paper1['title'] + ' ' + paper1['abstract']).lower()
    text2 = (paper2['title'] + ' ' + paper2['abstract']).lower()

    words1 = set(text1.split())
    words2 = set(text2.split())

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

def truncate_abstract(abstract: str, max_length: int = 150) -> str:
    """Truncate abstract for snippet display"""
    if len(abstract) <= max_length:
        return abstract
    return abstract[:max_length].rsplit(' ', 1)[0] + '...'

def generate_recommendation_reason(similarity: float, common_topics: List[str]) -> str:
    """Generate a human-readable reason for recommendation"""
    if similarity > 0.15:
        return "Highly related to your bookmarked papers"
    elif similarity > 0.10:
        return "Similar research area to your interests"
    elif common_topics:
        return f"Related topics: {', '.join(common_topics[:2])}"
    else:
        return "Recommended based on your reading history"

@router.get("/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(
    limit: int = 10,
    token_data: TokenData = Depends(verify_token)
):
    """
    Get personalized article recommendations based on user's bookmarks

    Algorithm:
    1. Get all user's bookmarked articles
    2. For each non-bookmarked article, calculate average similarity to bookmarked articles
    3. Rank by similarity and return top N
    """
    user_id = token_data.user_id
    papers = load_papers()

    # Get user's bookmarks
    user_bookmarks = bookmarks_store.get(user_id, {})
    bookmarked_ids = set(user_bookmarks.keys())

    # If user has no bookmarks, return popular papers (mock logic)
    if not bookmarked_ids:
        recommendations = []
        for i, paper in enumerate(papers[:limit]):
            recommendations.append(RecommendedArticle(
                id=paper['cord_uid'],
                relevance_score=round(0.8 - (i * 0.05), 2),
                title=paper['title'],
                authors=paper['authors'],
                abstract_snippet=truncate_abstract(paper['abstract']),
                reason="Popular research in COVID-19"
            ))

        return RecommendationsResponse(
            recommendations=recommendations,
            total=len(recommendations),
            based_on_bookmarks=0
        )

    # Get bookmarked papers
    bookmarked_papers = [p for p in papers if p['cord_uid'] in bookmarked_ids]

    # Calculate recommendations
    recommendation_scores = []
    for paper in papers:
        # Skip already bookmarked papers
        if paper['cord_uid'] in bookmarked_ids:
            continue

        # Calculate average similarity to all bookmarked papers
        similarities = []
        for bookmarked_paper in bookmarked_papers:
            sim = calculate_paper_similarity(paper, bookmarked_paper)
            similarities.append(sim)

        avg_similarity = sum(similarities) / len(similarities) if similarities else 0

        # Only recommend if similarity is above threshold
        if avg_similarity > 0.05:
            recommendation_scores.append({
                'paper': paper,
                'score': avg_similarity
            })

    # Sort by relevance score
    recommendation_scores.sort(key=lambda x: x['score'], reverse=True)
    recommendation_scores = recommendation_scores[:limit]

    # Format recommendations
    recommendations = []
    for item in recommendation_scores:
        paper = item['paper']
        score = item['score']

        recommendations.append(RecommendedArticle(
            id=paper['cord_uid'],
            relevance_score=round(score, 2),
            title=paper['title'],
            authors=paper['authors'],
            abstract_snippet=truncate_abstract(paper['abstract']),
            reason=generate_recommendation_reason(score, [])
        ))

    return RecommendationsResponse(
        recommendations=recommendations,
        total=len(recommendations),
        based_on_bookmarks=len(bookmarked_ids)
    )
