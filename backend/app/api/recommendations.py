from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
from enum import Enum

from app.models import RecommendedArticle, RecommendationsResponse
from app.auth.auth import verify_token, TokenData
from app.api.bookmarks import bookmarks_store
from app.utils import get_es_client
from app.elasticsearch_helpers import get_documents_by_cord_uids, get_recent_documents
from app.config import INDEX_NAME_DEFAULT, INDEX_NAME_EMBEDDING

router = APIRouter()


class RecommendationMethod(str, Enum):
    """Recommendation method options"""
    MLT = "mlt"  # More Like This (default)
    VECTOR = "vector"  # Vector similarity using embeddings


def truncate_abstract(abstract: str, max_length: int = 150) -> str:
    """Truncate abstract for snippet display"""
    if len(abstract) <= max_length:
        return abstract
    return abstract[:max_length].rsplit(' ', 1)[0] + '...'


def generate_recommendation_reason(similarity: float) -> str:
    """Generate a human-readable reason for recommendation"""
    if similarity > 0.7:
        return "Highly related to your bookmarked papers"
    elif similarity > 0.5:
        return "Similar research area to your interests"
    elif similarity > 0.3:
        return "Related topics based on your reading history"
    else:
        return "Recommended based on your preferences"


def get_recommendations_mlt(
    es_client,
    bookmarked_docs: List[Dict],
    bookmarked_ids: set,
    limit: int
) -> List[Dict]:
    """
    Get recommendations using More Like This query
    
    Args:
        es_client: Elasticsearch client
        bookmarked_docs: List of bookmarked document dicts
        bookmarked_ids: Set of bookmarked cord_uids to exclude
        limit: Maximum number of recommendations
    
    Returns:
        List of recommended documents with scores
    """
    # Combine text from all bookmarked papers
    combined_text_parts = []
    for doc in bookmarked_docs:
        title = doc.get('title', '')
        abstract = doc.get('abstract', '')
        combined_text_parts.append(f"{title} {abstract}")
    
    combined_text = " ".join(combined_text_parts)
    
    # Run More Like This query
    try:
        response = es_client.search(
            index=INDEX_NAME_DEFAULT,
            body={
                "query": {
                    "more_like_this": {
                        "fields": ["title", "abstract"],
                        "like": combined_text,
                        "min_term_freq": 1,
                        "min_doc_freq": 1,
                        "max_query_terms": 30,
                        "minimum_should_match": "30%"
                    }
                },
                "size": limit + len(bookmarked_ids)  # Extra to account for filtering
            }
        )
        
        hits = response.get("hits", {}).get("hits", [])
        
        # Filter and collect results
        results = []
        for hit in hits:
            doc = hit["_source"]
            cord_uid = doc.get("cord_uid")
            
            # Skip bookmarked papers
            if cord_uid in bookmarked_ids:
                continue
            
            doc["_similarity_score"] = hit.get("_score", 0)
            results.append(doc)
            
            if len(results) >= limit:
                break
        
        return results
    except Exception as e:
        print(f"Error in MLT recommendations: {e}")
        return []


def get_recommendations_vector(
    es_client,
    bookmarked_cord_uids: List[str],
    bookmarked_ids: set,
    limit: int
) -> List[Dict]:
    """
    Get recommendations using vector similarity (KNN search on embeddings)
    
    Args:
        es_client: Elasticsearch client
        bookmarked_cord_uids: List of bookmarked cord_uids
        bookmarked_ids: Set of bookmarked cord_uids to exclude
        limit: Maximum number of recommendations
    
    Returns:
        List of recommended documents with scores
    """
    try:
        # Fetch embeddings for bookmarked papers
        response = es_client.search(
            index=INDEX_NAME_EMBEDDING,
            body={
                "query": {
                    "terms": {
                        "cord_uid": bookmarked_cord_uids
                    }
                },
                "_source": ["cord_uid", "embedding"],
                "size": len(bookmarked_cord_uids)
            }
        )
        
        hits = response.get("hits", {}).get("hits", [])
        if not hits:
            return []
        
        # Calculate average embedding vector
        embeddings = []
        for hit in hits:
            embedding = hit["_source"].get("embedding")
            if embedding:
                embeddings.append(embedding)
        
        if not embeddings:
            return []
        
        # Calculate average (simple centroid)
        avg_embedding = [
            sum(emb[i] for emb in embeddings) / len(embeddings)
            for i in range(len(embeddings[0]))
        ]
        
        # Run KNN search with average embedding
        knn_response = es_client.search(
            index=INDEX_NAME_EMBEDDING,
            body={
                "knn": {
                    "field": "embedding",
                    "query_vector": avg_embedding,
                    "k": limit + len(bookmarked_ids),
                    "num_candidates": (limit + len(bookmarked_ids)) * 10
                },
                "_source": {
                    "excludes": ["embedding"]  # Don't return the embedding vector
                }
            }
        )
        
        knn_hits = knn_response.get("hits", {}).get("hits", [])
        
        # Filter and collect results
        results = []
        for hit in knn_hits:
            doc = hit["_source"]
            cord_uid = doc.get("cord_uid")
            
            # Skip bookmarked papers
            if cord_uid in bookmarked_ids:
                continue
            
            doc["_similarity_score"] = hit.get("_score", 0)
            results.append(doc)
            
            if len(results) >= limit:
                break
        
        return results
    except Exception as e:
        print(f"Error in vector recommendations: {e}")
        return []


@router.get("/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(
    limit: int = 10,
    method: RecommendationMethod = RecommendationMethod.MLT,
    token_data: TokenData = Depends(verify_token)
):
    """
    Get personalized article recommendations based on user's bookmarks
    
    Args:
        limit: Maximum number of recommendations
        method: Recommendation method - 'mlt' (default) or 'vector'
        token_data: User authentication token
    
    Returns:
        Personalized recommendations with relevance scores
    """
    try:
        user_id = token_data.user_id
        es = get_es_client(max_retries=3, sleep_time=1)

        # Get user's bookmarks
        user_bookmarks = bookmarks_store.get(user_id, {})
        bookmarked_ids = set(user_bookmarks.keys())

        # If user has no bookmarks, return recent papers
        if not bookmarked_ids:
            recent_papers = get_recent_documents(es, max_results=limit, index=INDEX_NAME_DEFAULT)
            
            recommendations = []
            for i, paper in enumerate(recent_papers):
                # Parse authors
                authors = paper.get('authors', [])
                if isinstance(authors, str):
                    authors = authors.split('; ') if authors else []
                
                recommendations.append(RecommendedArticle(
                    id=paper.get('cord_uid', ''),
                    relevance_score=round(0.8 - (i * 0.05), 2),
                    title=paper.get('title', ''),
                    authors=authors,
                    abstract_snippet=truncate_abstract(paper.get('abstract', '')),
                    reason="Recent COVID-19 research"
                ))

            return RecommendationsResponse(
                recommendations=recommendations,
                total=len(recommendations),
                based_on_bookmarks=0
            )

        # Get bookmarked documents
        bookmarked_cord_uids = list(bookmarked_ids)
        bookmarked_docs = get_documents_by_cord_uids(es, bookmarked_cord_uids, INDEX_NAME_DEFAULT)

        # Get recommendations based on selected method
        if method == RecommendationMethod.VECTOR:
            recommended_docs = get_recommendations_vector(
                es, bookmarked_cord_uids, bookmarked_ids, limit
            )
        else:  # MLT is default
            recommended_docs = get_recommendations_mlt(
                es, bookmarked_docs, bookmarked_ids, limit
            )

        # Format recommendations
        recommendations = []
        for doc in recommended_docs:
            # Parse authors
            authors = doc.get('authors', [])
            if isinstance(authors, str):
                authors = authors.split('; ') if authors else []
            
            # Get and normalize similarity score
            score = doc.get('_similarity_score', 0)
            # Normalize to 0-1 range
            if method == RecommendationMethod.VECTOR:
                normalized_score = min(score / 10.0, 1.0)
            else:  # MLT
                normalized_score = min(score / 20.0, 1.0)
            
            recommendations.append(RecommendedArticle(
                id=doc.get('cord_uid', ''),
                relevance_score=round(normalized_score, 2),
                title=doc.get('title', ''),
                authors=authors,
                abstract_snippet=truncate_abstract(doc.get('abstract', '')),
                reason=generate_recommendation_reason(normalized_score)
            ))

        return RecommendationsResponse(
            recommendations=recommendations,
            total=len(recommendations),
            based_on_bookmarks=len(bookmarked_ids)
        )
    
    except ConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to Elasticsearch: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while generating recommendations: {str(e)}"
        )
