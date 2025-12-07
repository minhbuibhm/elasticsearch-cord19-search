"""
Elasticsearch helper utilities for querying CORD-19 dataset
"""
from typing import List, Dict, Optional, Tuple
from elasticsearch import Elasticsearch
from app.config import INDEX_NAME_DEFAULT, INDEX_NAME_HYBRID


def get_document_by_cord_uid(
    es_client: Elasticsearch, 
    cord_uid: str, 
    index: str = INDEX_NAME_DEFAULT
) -> Optional[Dict]:
    """
    Retrieve a single document by its cord_uid
    
    Args:
        es_client: Elasticsearch client instance
        cord_uid: The cord_uid of the document to retrieve
        index: Elasticsearch index name (default: cord19)
    
    Returns:
        Document dict if found, None otherwise
    """
    try:
        # Search for document with matching cord_uid
        response = es_client.search(
            index=index,
            body={
                "query": {
                    "term": {
                        "cord_uid": cord_uid
                    }
                },
                "size": 1
            }
        )
        
        hits = response.get("hits", {}).get("hits", [])
        if hits:
            return hits[0]["_source"]
        return None
    except Exception as e:
        print(f"Error retrieving document {cord_uid}: {e}")
        return None


def get_documents_by_cord_uids(
    es_client: Elasticsearch, 
    cord_uids: List[str], 
    index: str = INDEX_NAME_DEFAULT
) -> List[Dict]:
    """
    Retrieve multiple documents by their cord_uids
    
    Args:
        es_client: Elasticsearch client instance
        cord_uids: List of cord_uid values
        index: Elasticsearch index name (default: cord19)
    
    Returns:
        List of document dicts
    """
    if not cord_uids:
        return []
    
    try:
        # Use terms query for efficient batch retrieval
        response = es_client.search(
            index=index,
            body={
                "query": {
                    "terms": {
                        "cord_uid": cord_uids
                    }
                },
                "size": len(cord_uids)
            }
        )
        
        hits = response.get("hits", {}).get("hits", [])
        return [hit["_source"] for hit in hits]
    except Exception as e:
        print(f"Error retrieving documents: {e}")
        return []


def get_related_documents(
    es_client: Elasticsearch,
    cord_uid: str,
    max_results: int = 5,
    index: str = INDEX_NAME_DEFAULT,
    min_term_freq: int = 1,
    min_doc_freq: int = 1
) -> List[Dict]:
    """
    Find related documents using Elasticsearch More Like This (MLT) query
    
    Args:
        es_client: Elasticsearch client instance
        cord_uid: The cord_uid of the source document
        max_results: Maximum number of related documents to return
        index: Elasticsearch index name (default: cord19)
        min_term_freq: Minimum term frequency for MLT
        min_doc_freq: Minimum document frequency for MLT
    
    Returns:
        List of related document dicts with similarity scores
    """
    try:
        # First, get the source document to extract text
        source_doc = get_document_by_cord_uid(es_client, cord_uid, index)
        if not source_doc:
            return []
        
        # Extract text for MLT query
        title = source_doc.get("title", "")
        abstract = source_doc.get("abstract", "")
        like_text = f"{title} {abstract}"
        
        # Run More Like This query
        response = es_client.search(
            index=index,
            body={
                "query": {
                    "more_like_this": {
                        "fields": ["title", "abstract"],
                        "like": like_text,
                        "min_term_freq": min_term_freq,
                        "min_doc_freq": min_doc_freq,
                        "max_query_terms": 25
                    }
                },
                "size": max_results + 1  # +1 to account for source doc potentially appearing
            }
        )
        
        hits = response.get("hits", {}).get("hits", [])
        
        # Filter out the source document and add scores
        results = []
        for hit in hits:
            doc = hit["_source"]
            # Skip the source document itself
            if doc.get("cord_uid") == cord_uid:
                continue
            
            # Add similarity score
            doc["_similarity_score"] = hit.get("_score", 0)
            results.append(doc)
            
            if len(results) >= max_results:
                break
        
        return results
    except Exception as e:
        print(f"Error finding related documents for {cord_uid}: {e}")
        return []


def check_document_exists(
    es_client: Elasticsearch,
    cord_uid: str,
    index: str = INDEX_NAME_DEFAULT
) -> bool:
    """
    Check if a document exists in Elasticsearch
    
    Args:
        es_client: Elasticsearch client instance
        cord_uid: The cord_uid to check
        index: Elasticsearch index name (default: cord19)
    
    Returns:
        True if document exists, False otherwise
    """
    try:
        response = es_client.count(
            index=index,
            body={
                "query": {
                    "term": {
                        "cord_uid": cord_uid
                    }
                }
            }
        )
        return response.get("count", 0) > 0
    except Exception as e:
        print(f"Error checking document existence for {cord_uid}: {e}")
        return False


def get_recent_documents(
    es_client: Elasticsearch,
    max_results: int = 10,
    index: str = INDEX_NAME_DEFAULT
) -> List[Dict]:
    """
    Get recent documents sorted by publication date
    
    Args:
        es_client: Elasticsearch client instance
        max_results: Maximum number of documents to return
        index: Elasticsearch index name (default: cord19)
    
    Returns:
        List of recent document dicts
    """
    try:
        response = es_client.search(
            index=index,
            body={
                "query": {
                    "match_all": {}
                },
                "sort": [
                    {"publish_time": {"order": "desc"}}
                ],
                "size": max_results
            }
        )
        
        hits = response.get("hits", {}).get("hits", [])
        return [hit["_source"] for hit in hits]
    except Exception as e:
        print(f"Error retrieving recent documents: {e}")
        return []


def get_document_with_es_id(
    es_client: Elasticsearch,
    cord_uid: str,
    index: str = INDEX_NAME_HYBRID
) -> Optional[Tuple[str, Dict]]:
    """
    Retrieve a document with its ES _id by cord_uid

    Args:
        es_client: Elasticsearch client instance
        cord_uid: The cord_uid of the document to retrieve
        index: Elasticsearch index name (default: hybrid index)

    Returns:
        Tuple of (es_id, source_dict) if found, None otherwise
    """
    try:
        response = es_client.search(
            index=index,
            body={
                "query": {
                    "term": {"cord_uid": cord_uid}
                },
                "size": 1
            }
        )

        hits = response.get("hits", {}).get("hits", [])
        if hits:
            return (hits[0]["_id"], hits[0]["_source"])
        return None
    except Exception as e:
        print(f"Error retrieving document with ES id {cord_uid}: {e}")
        return None


def get_es_ids_by_cord_uids(
    es_client: Elasticsearch,
    cord_uids: List[str],
    index: str = INDEX_NAME_HYBRID
) -> Dict[str, str]:
    """
    Batch retrieve ES _ids for multiple cord_uids

    Args:
        es_client: Elasticsearch client instance
        cord_uids: List of cord_uid values
        index: Elasticsearch index name (default: hybrid index)

    Returns:
        Dict mapping cord_uid -> es_id
    """
    if not cord_uids:
        return {}

    try:
        response = es_client.search(
            index=index,
            body={
                "query": {
                    "terms": {"cord_uid": cord_uids}
                },
                "size": len(cord_uids),
                "_source": ["cord_uid"]
            }
        )

        hits = response.get("hits", {}).get("hits", [])
        return {hit["_source"]["cord_uid"]: hit["_id"] for hit in hits}
    except Exception as e:
        print(f"Error retrieving ES ids: {e}")
        return {}


def get_related_documents_v2(
    es_client: Elasticsearch,
    cord_uid: str,
    max_results: int = 5,
    index: str = INDEX_NAME_HYBRID
) -> List[Dict]:
    """
    Find related documents using kNN (preferred) with MLT fallback.
    Uses document reference for better accuracy.

    Args:
        es_client: Elasticsearch client instance
        cord_uid: The cord_uid of the source document
        max_results: Maximum number of related documents to return
        index: Elasticsearch index name (default: hybrid index)

    Returns:
        List of related document dicts with similarity scores
    """
    try:
        # Step 1: Get ES _id and embedding from the source document
        result = get_document_with_es_id(es_client, cord_uid, index)
        if not result:
            return []

        es_id, source_doc = result
        embedding_vector = source_doc.get("embedding")

        related_hits = []

        # Strategy 1: kNN search (preferred) if embedding exists
        if embedding_vector:
            try:
                knn_query = {
                    "field": "embedding",
                    "query_vector": embedding_vector,
                    "k": max_results + 1,  # +1 to exclude self
                    "num_candidates": 50,
                }
                resp = es_client.search(
                    index=index,
                    knn=knn_query,
                    _source={"excludes": ["embedding"]},
                )
                # Remove self from results
                related_hits = [
                    hit for hit in resp["hits"]["hits"] if hit["_id"] != es_id
                ][:max_results]
            except Exception as e:
                print(f"kNN search failed: {e}")

        # Strategy 2: MLT fallback with document reference
        if not related_hits:
            try:
                mlt_query = {
                    "more_like_this": {
                        "fields": ["title", "abstract"],
                        "like": [{"_index": index, "_id": es_id}],
                        "min_term_freq": 1,
                        "max_query_terms": 12,
                    }
                }
                resp = es_client.search(
                    index=index,
                    query=mlt_query,
                    size=max_results,
                    _source={"excludes": ["embedding"]},
                )
                related_hits = resp["hits"]["hits"]
            except Exception as e:
                print(f"MLT search failed: {e}")

        # Format results
        results = []
        for hit in related_hits:
            doc = hit["_source"].copy()
            doc["_similarity_score"] = hit.get("_score", 0)
            results.append(doc)

        return results
    except Exception as e:
        print(f"Error finding related documents for {cord_uid}: {e}")
        return []
