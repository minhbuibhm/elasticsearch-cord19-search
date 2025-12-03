"""
BACKEND API - SEARCH ENGINE (FastAPI)
-------------------------------------
Purpose:
    Serves the 3 types of search (Lexical, Semantic, Hybrid) to the frontend.
    Connects to Elasticsearch and runs the AI model for query embedding.

Endpoints:
    1. /regular_search: Standard BM25 text search.
    2. /semantic_search: Vector-based kNN search.
    3. /hybrid_search: Combines #1 and #2 using Reciprocal Rank Fusion (RRF).
    4. /get_docs_per_year_count: Analytics for the timeline chart.
    5. /get_paper_details: Returns metadata + 10 related papers (Robust with MLT fallback). 
"""

import torch
import asyncio
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch, NotFoundError

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
INDEX_NAME = "cord19_hybrid_search"
EMBEDDING_MODEL = "allenai/scibert_scivocab_uncased"

# Local imports utility
try:
    from utils import get_es_client
except ImportError:

    def get_es_client(max_retries=3, sleep_time=1):
        return Elasticsearch("http://localhost:9200", request_timeout=30)


# ---------------------------------------------------------
# INITIALIZATION
# ---------------------------------------------------------
app = FastAPI(title="Paper-Finder API", version="1.0")

# Enable CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load AI Model (Global for performance)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
if torch.backends.mps.is_available():
    device = torch.device("mps")

print(f"Loading Model: {EMBEDDING_MODEL} on {device}...")
model = SentenceTransformer(EMBEDDING_MODEL).to(device)
print("Model Loaded Successfully.")


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------
def reciprocal_rank_fusion(
    lexical_hits: List[Dict], semantic_hits: List[Dict], k: int = 60
) -> List[Dict]:
    """
    Implements Reciprocal Rank Fusion (RRF).
    Formula: Score = sum(1 / (k + rank_i))
    """
    doc_scores = {}

    # 1. Process Lexical (Keyword) Results
    for rank, hit in enumerate(lexical_hits):
        doc_id = hit["_id"]
        if doc_id not in doc_scores:
            doc_scores[doc_id] = {"_source": hit["_source"], "_id": doc_id, "_score": 0}
        doc_scores[doc_id]["_score"] += 1 / (k + rank + 1)

    # 2. Process Semantic (Vector) Results
    for rank, hit in enumerate(semantic_hits):
        doc_id = hit["_id"]
        if doc_id not in doc_scores:
            doc_scores[doc_id] = {"_source": hit["_source"], "_id": doc_id, "_score": 0}
        doc_scores[doc_id]["_score"] += 1 / (k + rank + 1)

    # 3. Sort by final accumulated score
    sorted_docs = sorted(doc_scores.values(), key=lambda x: x["_score"], reverse=True)
    return sorted_docs


def build_year_filter(year: str | None) -> Dict | None:
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


# ---------------------------------------------------------
# API ENDPOINTS
# ---------------------------------------------------------


@app.get("/api/v1/regular_search/")
async def regular_search(
    search_query: str, skip: int = 0, limit: int = 10, year: str | None = None
) -> Dict:
    """
    Standard BM25 Search.
    """
    es = get_es_client()

    query = {
        "bool": {
            "must": [
                {
                    "multi_match": {
                        "query": search_query,
                        "fields": ["title^2", "abstract", "authors"],
                        "type": "best_fields",
                    }
                }
            ],
            "filter": build_year_filter(year) if year else [],
        }
    }

    response = es.search(
        index=INDEX_NAME,
        query=query,
        from_=skip,
        size=limit,
        _source={"excludes": ["embedding"]},
    )

    return {
        "hits": response["hits"]["hits"],
        "total": response["hits"]["total"]["value"],
        "max_pages": (response["hits"]["total"]["value"] + limit - 1) // limit,
    }


@app.get("/api/v1/semantic_search/")
async def semantic_search(
    search_query: str, skip: int = 0, limit: int = 10, year: str | None = None
) -> Dict:
    """
    Vector Search (kNN).
    """
    es = get_es_client()

    # 1. Convert Query to Vector
    query_vector = model.encode(search_query).tolist()

    # 2. Prepare kNN Query
    knn_query = {
        "field": "embedding",
        "query_vector": query_vector,
        "k": 100,
        "num_candidates": 200,
    }

    year_filter = build_year_filter(year)
    if year_filter:
        knn_query["filter"] = year_filter

    # 3. Execute
    response = es.search(
        index=INDEX_NAME,
        knn=knn_query,
        from_=skip,
        size=limit,
        _source={"excludes": ["embedding"]},
    )

    return {
        "hits": response["hits"]["hits"],
        "total": response["hits"]["total"]["value"],
        "max_pages": (response["hits"]["total"]["value"] + limit - 1) // limit,
    }


@app.get("/api/v1/hybrid_search/")
async def hybrid_search(
    search_query: str, skip: int = 0, limit: int = 10, year: str | None = None
) -> Dict:
    """
    Hybrid Search (RRF).
    """
    es = get_es_client()

    # --- 1. Setup Queries ---
    keyword_query = {
        "bool": {
            "must": [
                {
                    "multi_match": {
                        "query": search_query,
                        "fields": ["title", "abstract"],
                    }
                }
            ],
            "filter": build_year_filter(year) if year else [],
        }
    }

    query_vector = model.encode(search_query).tolist()

    knn_query = {
        "field": "embedding",
        "query_vector": query_vector,
        "k": 50,
        "num_candidates": 100,
    }
    year_filter = build_year_filter(year)
    if year_filter:
        knn_query["filter"] = year_filter

    # --- 2. Execute Both Queries ---
    lexical_resp = es.search(
        index=INDEX_NAME,
        query=keyword_query,
        size=50,
        _source={"excludes": ["embedding"]},
    )

    semantic_resp = es.search(
        index=INDEX_NAME, knn=knn_query, size=50, _source={"excludes": ["embedding"]}
    )

    # --- 3. RRF ---
    fused_results = reciprocal_rank_fusion(
        lexical_resp["hits"]["hits"], semantic_resp["hits"]["hits"]
    )

    paginated_hits = fused_results[skip : skip + limit]
    total_hits = len(fused_results)

    return {
        "hits": paginated_hits,
        "total": total_hits,
        "max_pages": (total_hits + limit - 1) // limit,
    }


@app.get("/api/v1/get_docs_per_year_count/")
async def get_docs_per_year_count(search_query: str) -> Dict:
    """
    Analytics: Timeline chart data.
    """
    es = get_es_client()

    query = {
        "bool": {
            "must": [
                {
                    "multi_match": {
                        "query": search_query,
                        "fields": ["title", "abstract"],
                    }
                }
            ]
        }
    }

    response = es.search(
        index=INDEX_NAME,
        query=query,
        size=0,
        aggs={
            "docs_per_year": {
                "date_histogram": {
                    "field": "publish_time",
                    "calendar_interval": "year",
                    "format": "yyyy",
                }
            }
        },
    )

    buckets = (
        response.get("aggregations", {}).get("docs_per_year", {}).get("buckets", [])
    )
    data = {bucket["key_as_string"]: bucket["doc_count"] for bucket in buckets}

    return {"docs_per_year": data}


@app.get("/api/v1/get_paper_details/")
async def get_paper_details(doc_id: str) -> Dict:
    """
    Returns full details for a single paper + 10 Related Papers.
    Uses 'kNN' if vector exists, otherwise falls back to 'More Like This' (MLT).
    """
    es = get_es_client()
    print(f"DEBUG: Fetching details for doc_id: {doc_id}")

    try:
        doc = es.get(index=INDEX_NAME, id=doc_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Paper not found")

    source = doc["_source"]
    embedding_vector = source.get("embedding")

    # Prepare details for frontend (exclude vector)
    paper_details = source.copy()
    if "embedding" in paper_details:
        del paper_details["embedding"]

    related_hits = []

    # STRATEGY 1: Semantic Search (Preferred)
    if embedding_vector:
        print("DEBUG: Vector found. Running kNN Search...")
        try:
            knn_query = {
                "field": "embedding",
                "query_vector": embedding_vector,
                "k": 11,
                "num_candidates": 50,
            }
            resp = es.search(
                index=INDEX_NAME, knn=knn_query, _source={"excludes": ["embedding"]}
            )
            # Remove self
            related_hits = [
                hit for hit in resp["hits"]["hits"] if hit["_id"] != doc_id
            ][:10]
        except Exception as e:
            print(f"DEBUG: kNN failed: {e}")

    # STRATEGY 2: Fallback to 'More Like This' (If vector is missing)
    if not related_hits:
        print("DEBUG: No vector or kNN results. Running 'More Like This' fallback...")
        try:
            mlt_query = {
                "more_like_this": {
                    "fields": ["title", "abstract"],
                    "like": [{"_index": INDEX_NAME, "_id": doc_id}],
                    "min_term_freq": 1,
                    "max_query_terms": 12,
                }
            }
            resp = es.search(
                index=INDEX_NAME,
                query=mlt_query,
                size=10,
                _source={"excludes": ["embedding"]},
            )
            related_hits = resp["hits"]["hits"]
        except Exception as e:
            print(f"DEBUG: MLT failed: {e}")

    print(f"DEBUG: Returning {len(related_hits)} related papers.")
    return {"paper_details": paper_details, "related_papers": related_hits}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


# === Old version ===
# import torch
# from config import INDEX_NAME_DEFAULT, INDEX_NAME_EMBEDDING, INDEX_NAME_N_GRAM, EMBEDDING_MODEL
# from elastic_transport import ObjectApiResponse
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import HTMLResponse
# from sentence_transformers import SentenceTransformer
# from utils import get_es_client

# app = FastAPI()
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# device = torch.device('cuda' if torch.cuda.is_available()
#                       else 'mps' if torch.backends.mps.is_available() else 'cpu')
# model = SentenceTransformer(EMBEDDING_MODEL).to(device)


# @app.get("/api/v1/regular_search/", response_model=None)
# async def regular_search(
#     search_query: str,
#     skip: int = 0,
#     limit: int = 10,
#     year: str | None = None,
#     tokenizer: str = "Standard",
# ) -> dict | HTMLResponse:
#     try:
#         es = get_es_client(max_retries=1, sleep_time=0)
#         query = {
#             "bool": {
#                 "must": [
#                     {
#                         "multi_match": {
#                             "query": search_query,
#                             "fields": ["title", "abstract"]#["title", "explanation"],
#                         }
#                     }
#                 ]
#             }
#         }

#         if year:
#             query["bool"]["filter"] = [
#                 {
#                     "range": {
#                         "publish_time": {
#                             "gte": f"{year}-01-01",
#                             "lte": f"{year}-12-31",
#                             "format": "yyyy-MM-dd",
#                         }
#                     }
#                 }
#             ]

#         index_name = (
#             INDEX_NAME_DEFAULT if tokenizer == "Standard" else INDEX_NAME_N_GRAM
#         )
#         response = es.search(
#             index=index_name,
#             body={
#                 "query": query,
#                 "from": skip,
#                 "size": limit,
#             },
#             filter_path=[
#                 "hits.hits._source",
#                 "hits.hits._score",
#                 "hits.total",
#             ],
#         )

#         total_hits = get_total_hits(response)
#         max_pages = calculate_max_pages(total_hits, limit)

#         return {
#             "hits": response["hits"].get("hits", []),
#             "max_pages": max_pages,
#         }
#     except Exception as e:
#         return handle_error(e)


# @app.get("/api/v1/semantic_search/", response_model=None)
# async def semantic_search(
#     search_query: str, skip: int = 0, limit: int = 10, year: str | None = None
# ) -> dict | HTMLResponse:
#     try:
#         es = get_es_client(max_retries=1, sleep_time=0)
#         embedded_query = model.encode(search_query)

#         query = {
#             "bool": {
#                 "must": [
#                     {
#                         "knn": {
#                             "field": "embedding",
#                             "query_vector": embedded_query,
#                             "k": 1e3,
#                         }
#                     }
#                 ]
#             }
#         }

#         if year:
#             query["bool"]["filter"] = [
#                 {
#                     "range": {
#                         "publish_time": {
#                             "gte": f"{year}-01-01",
#                             "lte": f"{year}-12-31",
#                             "format": "yyyy-MM-dd",
#                         }
#                     }
#                 }
#             ]

#         response = es.search(
#             index=INDEX_NAME_EMBEDDING,
#             body={
#                 "query": query,
#                 "from": skip,
#                 "size": limit,
#             },
#             filter_path=[
#                 "hits.hits._source",
#                 "hits.hits._score",
#                 "hits.total",
#             ],
#         )

#         total_hits = get_total_hits(response)
#         max_pages = calculate_max_pages(total_hits, limit)

#         return {
#             "hits": response["hits"].get("hits", []),
#             "max_pages": max_pages,
#         }
#     except Exception as e:
#         return handle_error(e)


# def get_total_hits(response: ObjectApiResponse) -> int:
#     return response["hits"]["total"]["value"]


# def calculate_max_pages(total_hits: int, limit: int) -> int:
#     return (total_hits + limit - 1) // limit


# @app.get("/api/v1/get_docs_per_year_count/", response_model=None)
# async def get_docs_per_year_count(
#     search_query: str, tokenizer: str = "Standard"
# ) -> dict | HTMLResponse:
#     try:
#         es = get_es_client(max_retries=1, sleep_time=0)
#         query = {
#             "bool": {
#                 "must": [
#                     {
#                         "multi_match": {
#                             "query": search_query,
#                             "fields": ["title", "abstract"] #["title", "explanation"],
#                         }
#                     }
#                 ]
#             }
#         }

#         index_name = (
#             INDEX_NAME_DEFAULT if tokenizer == "Standard" else INDEX_NAME_N_GRAM
#         )
#         response = es.search(
#             index=index_name,
#             body={
#                 "query": query,
#                 "aggs": {
#                     "docs_per_year": {
#                         "date_histogram": {
#                             "field": "publish_time",
#                             "calendar_interval": "year",  # Group by year
#                             "format": "yyyy",  # Format the year in the response
#                         }
#                     }
#                 },
#             },
#             filter_path=["aggregations.docs_per_year"],
#         )
#         return {"docs_per_year": extract_docs_per_year(response)}
#     except Exception as e:
#         return handle_error(e)


# def extract_docs_per_year(response: ObjectApiResponse) -> dict:
#     aggregations = response.get("aggregations", {})
#     docs_per_year = aggregations.get("docs_per_year", {})
#     buckets = docs_per_year.get("buckets", [])
#     return {bucket["key_as_string"]: bucket["doc_count"] for bucket in buckets}


# def handle_error(e: Exception) -> HTMLResponse:
#     error_message = f"An error occurred: {str(e)}"
#     return HTMLResponse(content=error_message, status_code=500)

# if __name__ == "__main__":
#     import asyncio
#     from pprint import pprint
#     search_query = "covid"
#     async def main():
#         # result = await regular_search(search_query)
#         result = await semantic_search(search_query)
#         pprint(result)

#     asyncio.run(main())
