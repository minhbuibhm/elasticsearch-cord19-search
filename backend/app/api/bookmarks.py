from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Set
from datetime import datetime

from app.models import BookmarkRequest, BookmarkResponse, BookmarkedArticle, BookmarksListResponse
from app.auth.auth import verify_token, TokenData
from app.utils import get_es_client
from app.elasticsearch_helpers import (
    get_document_by_cord_uid,
    get_documents_by_cord_uids,
    check_document_exists
)
from app.config import INDEX_NAME_DEFAULT

router = APIRouter()

# In-memory bookmark storage: {user_id: {article_id: timestamp}}
# In production, this would be stored in a database
bookmarks_store: Dict[str, Dict[str, str]] = {}


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
    try:
        user_id = token_data.user_id
        es = get_es_client(max_retries=3, sleep_time=1)

        # Get user's bookmarks
        user_bookmarks = bookmarks_store.get(user_id, {})
        
        if not user_bookmarks:
            return BookmarksListResponse(
                bookmarks=[],
                total=0
            )
        
        # Fetch bookmarked documents from Elasticsearch
        bookmarked_ids = list(user_bookmarks.keys())
        papers = get_documents_by_cord_uids(es, bookmarked_ids, INDEX_NAME_DEFAULT)
        
        # Create a mapping for quick lookup
        papers_dict = {p.get('cord_uid'): p for p in papers}

        # Build bookmarked articles list
        bookmarked_articles = []
        for cord_uid, timestamp in user_bookmarks.items():
            paper = papers_dict.get(cord_uid)
            if not paper:
                # Skip if document no longer exists in Elasticsearch
                continue
            
            # Parse authors
            authors = paper.get('authors', [])
            if isinstance(authors, str):
                authors = authors.split('; ') if authors else []
            
            bookmarked_articles.append(BookmarkedArticle(
                id=cord_uid,
                title=paper.get('title', ''),
                authors=authors,
                journal=paper.get('journal'),
                publication_date=paper.get('publish_time'),
                abstract_snippet=truncate_abstract(paper.get('abstract', '')),
                bookmarked_at=timestamp
            ))

        # Sort by bookmark date (most recent first)
        bookmarked_articles.sort(key=lambda x: x.bookmarked_at, reverse=True)

        return BookmarksListResponse(
            bookmarks=bookmarked_articles,
            total=len(bookmarked_articles)
        )
    
    except ConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to Elasticsearch: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while retrieving bookmarks: {str(e)}"
        )


@router.post("", response_model=BookmarkResponse)
async def add_bookmark(
    request: BookmarkRequest,
    token_data: TokenData = Depends(verify_token)
):
    """
    Add an article to user's bookmarks
    """
    try:
        user_id = token_data.user_id
        article_id = request.article_id
        es = get_es_client(max_retries=3, sleep_time=1)

        # Verify article exists in Elasticsearch
        if not check_document_exists(es, article_id, INDEX_NAME_DEFAULT):
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
    
    except HTTPException:
        raise
    except ConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to Elasticsearch: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while adding bookmark: {str(e)}"
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
