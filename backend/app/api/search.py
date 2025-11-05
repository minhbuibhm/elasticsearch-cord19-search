from fastapi import APIRouter, HTTPException
from typing import List
import torch
from sentence_transformers import SentenceTransformer

from app.models import SearchRequest, SearchResponse, ArticleSnippet
from app.config import INDEX_NAME_DEFAULT, INDEX_NAME_N_GRAM, INDEX_NAME_EMBEDDING, EMBEDDING_MODEL
from app.utils import get_es_client

router = APIRouter()

# Initialize model for semantic search
device = torch.device('cuda' if torch.cuda.is_available()
                      else 'mps' if torch.backends.mps.is_available() else 'cpu')
model = SentenceTransformer(EMBEDDING_MODEL).to(device)


def truncate_abstract(abstract: str, max_length: int = 200) -> str:
    """Truncate abstract for snippet display"""
    if len(abstract) <= max_length:
        return abstract
    return abstract[:max_length].rsplit(' ', 1)[0] + '...'


def get_total_hits(response) -> int:
    """Extract total hits from Elasticsearch response"""
    return response["hits"]["total"]["value"]


def calculate_max_pages(total_hits: int, limit: int) -> int:
    """Calculate maximum number of pages"""
    return (total_hits + limit - 1) // limit


@router.post("/search", response_model=SearchResponse)
async def search_papers(request: SearchRequest):
    """
    Search research papers using Elasticsearch
    Supports both regular (keyword) and semantic (AI-powered) search
    """
    try:
        es = get_es_client(max_retries=3, sleep_time=1)

        # Convert pagination from page/size to skip/limit
        page = request.pagination.get('page', 1)
        size = request.pagination.get('size', 10)
        skip = (page - 1) * size

        # Determine search method
        if request.search_method == "semantic":
            # Semantic search using embeddings (Elasticsearch 8.x KNN API)
            embedded_query = model.encode(request.query)

            # Build KNN configuration
            knn_config = {
                "field": "embedding",
                "query_vector": embedded_query.tolist(),  # Convert numpy array to list
                "k": 1000,
                "num_candidates": 10000  # Number of candidates to consider
            }

            # Add year filter INSIDE knn config (Elasticsearch 8.x syntax)
            if request.year:
                knn_config["filter"] = [
                    {
                        "range": {
                            "publish_time": {
                                "gte": f"{request.year}-01-01",
                                "lte": f"{request.year}-12-31",
                                "format": "yyyy-MM-dd",
                            }
                        }
                    }
                ]

            # Build search parameters
            search_params = {
                "index": INDEX_NAME_EMBEDDING,
                "knn": knn_config,
                "size": size,
                "from_": skip,
                "filter_path": [
                    "hits.hits._source",
                    "hits.hits._score",
                    "hits.total",
                ],
            }

            response = es.search(**search_params)
        else:
            # Regular search (keyword-based)
            query = {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": request.query,
                                "fields": ["title", "abstract"]
                            }
                        }
                    ]
                }
            }

            # Add year filter if provided
            if request.year:
                query["bool"]["filter"] = [
                    {
                        "range": {
                            "publish_time": {
                                "gte": f"{request.year}-01-01",
                                "lte": f"{request.year}-12-31",
                                "format": "yyyy-MM-dd",
                            }
                        }
                    }
                ]

            # Select index based on tokenizer
            index_name = INDEX_NAME_DEFAULT if request.tokenizer == "Standard" else INDEX_NAME_N_GRAM

            response = es.search(
                index=index_name,
                body={
                    "query": query,
                    "from": skip,
                    "size": size,
                },
                filter_path=[
                    "hits.hits._source",
                    "hits.hits._score",
                    "hits.total",
                ],
            )

        # Process results
        total_hits = get_total_hits(response)
        total_pages = calculate_max_pages(total_hits, size)

        hits = response["hits"].get("hits", [])

        # Format results to match UI expectations
        articles = []
        for hit in hits:
            source = hit["_source"]
            score = hit.get("_score", 0)

            # Normalize score to 0-1 range for display
            # Elasticsearch scores can vary widely, so we normalize
            normalized_score = min(score / 100.0, 1.0) if request.search_method == "regular" else min(score / 10.0, 1.0)

            articles.append(ArticleSnippet(
                id=source.get('cord_uid', ''),
                similarity_score=round(normalized_score, 2),
                title=source.get('title', ''),
                authors=source.get('authors', '').split('; ') if isinstance(source.get('authors'), str) else source.get('authors', []),
                journal=source.get('journal'),
                publication_date=source.get('publish_time'),
                abstract_snippet=truncate_abstract(source.get('abstract', ''))
            ))

        return SearchResponse(
            pagination={
                'total_results': total_hits,
                'page': page,
                'total_pages': total_pages,
                'size': size
            },
            results=articles
        )

    except ConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to Elasticsearch: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during search: {str(e)}"
        )
