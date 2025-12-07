from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
import torch
from sentence_transformers import SentenceTransformer

from app.models import SearchRequest, SearchResponse, ArticleSnippet
from app.config import INDEX_NAME_DEFAULT, INDEX_NAME_N_GRAM, INDEX_NAME_EMBEDDING, INDEX_NAME_HYBRID, EMBEDDING_MODEL
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


def build_year_filter(year: Optional[str]) -> Optional[Dict]:
    """Creates the Elasticsearch range filter for years."""
    if not year:
        return None
    return {
        "range": {
            "publish_time": {
                "gte": f"{year}-01-01",
                "lte": f"{year}-12-31",
                "format": "yyyy-MM-dd||yyyy",
            }
        }
    }


def reciprocal_rank_fusion(
    lexical_hits: List[Dict], semantic_hits: List[Dict], k: int = 60
) -> List[Dict]:
    """
    Implements Reciprocal Rank Fusion (RRF).
    Formula: Score = sum(1 / (k + rank_i))
    """
    doc_scores = {}

    # Process Lexical (Keyword) Results
    for rank, hit in enumerate(lexical_hits):
        doc_id = hit["_id"]
        if doc_id not in doc_scores:
            doc_scores[doc_id] = {"_source": hit["_source"], "_id": doc_id, "_score": 0}
        doc_scores[doc_id]["_score"] += 1 / (k + rank + 1)

    # Process Semantic (Vector) Results
    for rank, hit in enumerate(semantic_hits):
        doc_id = hit["_id"]
        if doc_id not in doc_scores:
            doc_scores[doc_id] = {"_source": hit["_source"], "_id": doc_id, "_score": 0}
        doc_scores[doc_id]["_score"] += 1 / (k + rank + 1)

    # Sort by final accumulated score
    sorted_docs = sorted(doc_scores.values(), key=lambda x: x["_score"], reverse=True)
    return sorted_docs


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
        elif request.search_method == "hybrid":
            # Hybrid search using Reciprocal Rank Fusion (RRF)
            # Combines keyword (BM25) and semantic (kNN) results

            # Build keyword query
            keyword_query = {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": request.query,
                                "fields": ["title", "abstract"],
                            }
                        }
                    ],
                    "filter": [build_year_filter(request.year)] if request.year else [],
                }
            }

            # Build kNN query
            query_vector = model.encode(request.query).tolist()
            knn_query = {
                "field": "embedding",
                "query_vector": query_vector,
                "k": 50,
                "num_candidates": 100,
            }
            year_filter = build_year_filter(request.year)
            if year_filter:
                knn_query["filter"] = year_filter

            # Execute both queries
            lexical_resp = es.search(
                index=INDEX_NAME_HYBRID,
                query=keyword_query,
                size=50,
                _source={"excludes": ["embedding"]},
            )

            semantic_resp = es.search(
                index=INDEX_NAME_HYBRID,
                knn=knn_query,
                size=50,
                _source={"excludes": ["embedding"]},
            )

            # Apply RRF to merge results
            fused_results = reciprocal_rank_fusion(
                lexical_resp["hits"]["hits"], semantic_resp["hits"]["hits"]
            )

            # Paginate fused results
            paginated_hits = fused_results[skip : skip + size]
            total_fused = len(fused_results)

            # Format hybrid results
            articles = []
            for hit in paginated_hits:
                source = hit["_source"]
                # RRF scores are small (0.01-0.03 range), normalize for display
                normalized_score = min(hit["_score"] * 30, 1.0)

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
                    'total_results': total_fused,
                    'page': page,
                    'total_pages': calculate_max_pages(total_fused, size),
                    'size': size
                },
                results=articles
            )
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
