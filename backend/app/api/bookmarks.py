from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Set
import json
import os
from datetime import datetime

from app.models import BookmarkRequest, BookmarkResponse, BookmarkedArticle, BookmarksListResponse
from app.auth.auth import verify_token, TokenData

router = APIRouter()

# In-memory bookmark storage: {user_id: {article_id: timestamp}}
# In production, this would be stored in a database
bookmarks_store: Dict[str, Dict[str, str]] = {}

# Load mock data
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "mock_cord19.json")

def load_papers():
    """Load papers from mock data file"""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def truncate_abstract(abstract: str, max_length: int = 200) -> str:
    """Truncate abstract for snippet display"""
    if len(abstract) <= max_length:
        return abstract
    return abstract[:max_length].rsplit(' ', 1)[0] + '...'

@router.get("", response_model=BookmarksListResponse)
async def get_bookmarks(token_data: TokenData = Depends(verify_token)):
    """
    Get all bookmarked articles for the current user
    """
    user_id = token_data.user_id
    papers = load_papers()

    # Get user's bookmarks
    user_bookmarks = bookmarks_store.get(user_id, {})

    # Load bookmarked papers
    bookmarked_articles = []
    for paper in papers:
        if paper['cord_uid'] in user_bookmarks:
            bookmarked_articles.append(BookmarkedArticle(
                id=paper['cord_uid'],
                title=paper['title'],
                authors=paper['authors'],
                journal=paper.get('journal'),
                publication_date=paper.get('publish_time'),
                abstract_snippet=truncate_abstract(paper['abstract']),
                bookmarked_at=user_bookmarks[paper['cord_uid']]
            ))

    # Sort by bookmark date (most recent first)
    bookmarked_articles.sort(key=lambda x: x.bookmarked_at, reverse=True)

    return BookmarksListResponse(
        bookmarks=bookmarked_articles,
        total=len(bookmarked_articles)
    )

@router.post("", response_model=BookmarkResponse)
async def add_bookmark(
    request: BookmarkRequest,
    token_data: TokenData = Depends(verify_token)
):
    """
    Add an article to user's bookmarks
    """
    user_id = token_data.user_id
    article_id = request.article_id

    # Verify article exists
    papers = load_papers()
    article_exists = any(p['cord_uid'] == article_id for p in papers)

    if not article_exists:
        raise HTTPException(status_code=404, detail="Article not found")

    # Initialize user's bookmarks if needed
    if user_id not in bookmarks_store:
        bookmarks_store[user_id] = {}

    # Check if already bookmarked
    if article_id in bookmarks_store[user_id]:
        raise HTTPException(status_code=400, detail="Article already bookmarked")

    # Add bookmark with timestamp
    bookmarks_store[user_id][article_id] = datetime.utcnow().isoformat()

    return BookmarkResponse(
        message="Article bookmarked successfully",
        article_id=article_id
    )

@router.delete("/{article_id}", response_model=BookmarkResponse)
async def remove_bookmark(
    article_id: str,
    token_data: TokenData = Depends(verify_token)
):
    """
    Remove an article from user's bookmarks
    """
    user_id = token_data.user_id

    # Check if user has bookmarks
    if user_id not in bookmarks_store:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    # Check if article is bookmarked
    if article_id not in bookmarks_store[user_id]:
        raise HTTPException(status_code=404, detail="Bookmark not found")

    # Remove bookmark
    del bookmarks_store[user_id][article_id]

    return BookmarkResponse(
        message="Bookmark removed successfully",
        article_id=article_id
    )

@router.get("/check/{article_id}")
async def check_bookmark(
    article_id: str,
    token_data: TokenData = Depends(verify_token)
):
    """
    Check if an article is bookmarked by the current user
    """
    user_id = token_data.user_id

    is_bookmarked = (
        user_id in bookmarks_store and
        article_id in bookmarks_store[user_id]
    )

    return {
        "article_id": article_id,
        "is_bookmarked": is_bookmarked
    }
