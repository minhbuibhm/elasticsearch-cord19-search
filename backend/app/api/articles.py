from fastapi import APIRouter, HTTPException
from typing import List

from app.models import ArticleDetail, RelatedArticle, RelatedArticlesResponse, Reference
from app.utils import get_es_client
from app.elasticsearch_helpers import (
    get_document_by_cord_uid,
    get_related_documents_v2
)
from app.config import INDEX_NAME_HYBRID

router = APIRouter()


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
    try:
        es = get_es_client(max_retries=3, sleep_time=1)

        # Get document from hybrid index (has references field)
        paper = get_document_by_cord_uid(es, article_id, INDEX_NAME_HYBRID)

        if not paper:
            raise HTTPException(status_code=404, detail="Article not found")

        # Parse authors - handle both string and list formats
        authors = paper.get('authors', [])
        if isinstance(authors, str):
            authors = authors.split('; ') if authors else []

        # Parse references
        raw_references = paper.get('references', [])
        references = []
        for ref in raw_references:
            references.append(Reference(
                ref_id=ref.get('ref_id'),
                title=ref.get('title'),
                year=ref.get('year'),
                venue=ref.get('venue'),
                authors=ref.get('authors'),
                volume=ref.get('volume'),
                pages=ref.get('pages'),
                doi=ref.get('doi')
            ))

        # Return detailed information
        return ArticleDetail(
            id=paper.get('cord_uid', ''),
            title=paper.get('title', ''),
            authors=authors,
            full_abstract=paper.get('abstract', ''),
            journal=paper.get('journal'),
            publication_date=paper.get('publish_time'),
            full_text_url=paper.get('url'),
            clinical_trials=[],  # Not available in current schema
            doi=paper.get('doi'),
            references=references
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
            detail=f"An error occurred while retrieving article: {str(e)}"
        )


@router.get("/{article_id}/related", response_model=RelatedArticlesResponse)
async def get_related_articles(article_id: str, limit: int = 5):
    """
    Get articles related to a specific article using More Like This query
    """
    try:
        es = get_es_client(max_retries=3, sleep_time=1)
        
        # First verify the source article exists
        source_paper = get_document_by_cord_uid(es, article_id, INDEX_NAME_HYBRID)
        if not source_paper:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Get related documents using kNN (preferred) with MLT fallback
        related_docs = get_related_documents_v2(
            es,
            article_id,
            max_results=limit,
            index=INDEX_NAME_HYBRID
        )
        
        # Format response
        related_articles = []
        for doc in related_docs:
            # Parse authors
            authors = doc.get('authors', [])
            if isinstance(authors, str):
                authors = authors.split('; ') if authors else []
            
            # Get similarity score (added by helper function)
            similarity = doc.get('_similarity_score', 0)
            # Normalize score to 0-1 range for display
            normalized_score = min(similarity / 10.0, 1.0)
            
            related_articles.append(RelatedArticle(
                id=doc.get('cord_uid', ''),
                similarity_score=round(normalized_score, 2),
                title=doc.get('title', ''),
                authors=authors,
                abstract_snippet=truncate_abstract(doc.get('abstract', ''))
            ))
        
        return RelatedArticlesResponse(
            article_id=article_id,
            related_papers=related_articles
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
            detail=f"An error occurred while finding related articles: {str(e)}"
        )
