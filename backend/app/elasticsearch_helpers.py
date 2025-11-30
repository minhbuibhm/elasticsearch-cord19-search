"""
Elasticsearch helper utilities for querying CORD-19 dataset
"""
from typing import List, Dict, Optional
from elasticsearch import Elasticsearch
from app.config import INDEX_NAME_DEFAULT


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
