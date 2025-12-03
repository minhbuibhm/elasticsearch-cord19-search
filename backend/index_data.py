"""
SCRIPT ANNOTATION & DOCUMENTATION
--------------------------------
Purpose: 
    This script is the "Data Engineering" pipeline. It takes raw JSON data (CORD-19 dataset),
    processes it into text chunks and vectors, and indexes it into Elasticsearch.

Structure:
    1. Configuration: Sets up index names and model constants.
    2. create_index(): Defines the "Schema" (Mapping) for Elasticsearch.
       - Creates a 'dense_vector' field for AI embeddings.
       - Creates 'text' fields for standard keyword search.
    3. generate_actions(): A generator that processes data stream-wise (efficient for large RAM).
       - Cleans text.
       - Converts text to Vector using SciBERT.
    4. index_data(): The main entry point that orchestrates the loading and bulk indexing.

Output:
    A single Elasticsearch index named 'cord19_hybrid_search' ready for Hybrid Querying.
"""

import json
import torch
from typing import List, Generator
from tqdm import tqdm
from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
# We use a single index for Hybrid Search.
# This allows us to run BM25 and kNN queries on the same documents simultaneously.
INDEX_NAME = "cord19_hybrid_search"

# SciBERT: A BERT model pre-trained on scientific text.
# It understands terms like "COVID-19", "nucleotide", etc. better than standard BERT.
EMBEDDING_MODEL = "allenai/scibert_scivocab_uncased"
VECTOR_DIMS = 768  # SciBERT outputs a vector with 768 dimensions.

# Local imports utility
try:
    from utils import get_es_client
except ImportError:
    # Fallback if utils.py is missing
    def get_es_client(max_retries=3, sleep_time=1):
        return Elasticsearch("http://localhost:9200", request_timeout=300)

# ---------------------------------------------------------
# 1. INDEX CREATION & MAPPING (THE SCHEMA)
# ---------------------------------------------------------
def create_index(es: Elasticsearch) -> None:
    """
    Deletes the old index and creates a new one with a specific mapping.
    
    Why 'mapping' is important:
    - It tells Elasticsearch to treat 'embedding' as a vector, not just a list of numbers.
    - It tells Elasticsearch to treat 'title' as text to be analyzed (stemmed, tokenized).
    """
    
    # 1. Start Fresh: Delete index if it exists to prevent mapping conflicts
    if es.indices.exists(index=INDEX_NAME):
        es.indices.delete(index=INDEX_NAME)
        print(f"Deleted existing index: {INDEX_NAME}")

    # 2. Define Schema
    mapping = {
        "mappings": {
            "properties": {
                # --- Metadata fields (Stored for Frontend Display) ---
                "cord_uid": {"type": "keyword"}, # Exact match ID
                "url": {"type": "keyword"},      # Clickable link
                "journal": {"type": "keyword"},  # Filterable category (Facet)
                
                # --- Text Search Fields (BM25) ---
                "title": {
                    "type": "text",
                    "analyzer": "english", # Handles stemming: "tests" -> "test"
                    # "keyword" sub-field allows exact sorting by title if needed
                    "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}
                },
                "abstract": {
                    "type": "text",
                    "analyzer": "english"
                },
                "authors": {
                    "type": "text", # Text allows searching "John" to find "John Smith"
                    "fields": {"keyword": {"type": "keyword", "ignore_above": 256}}
                },

                # --- Date Filter ---
                "publish_time": {
                    "type": "date", 
                    "format": "yyyy-MM-dd||yyyy" # Supports strict dates or just years
                },

                # --- Semantic Search Field (Vector) ---
                "embedding": {
                    "type": "dense_vector",
                    "dims": VECTOR_DIMS,      # 768 for SciBERT
                    "index": True,            # Enables HNSW (approximate nearest neighbor)
                    "similarity": "cosine"    # Cosine similarity is best for SBERT embeddings
                }
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        }
    }

    es.indices.create(index=INDEX_NAME, body=mapping)
    print(f"Created new index '{INDEX_NAME}' with Hybrid mapping.")

# ---------------------------------------------------------
# 2. DATA PROCESSING GENERATOR
# ---------------------------------------------------------
def generate_actions(documents: List[dict], model: SentenceTransformer) -> Generator:
    """
    Yields documents one by one to the bulk indexer.
    Using a generator is memory efficient for large datasets.
    """
    
    for doc in tqdm(documents, desc="Embedding & Indexing"):
        # 1. Data Cleaning & Extraction
        title = doc.get("title", "")
        abstract = doc.get("abstract", "")
        
        # Skip garbage data (empty documents)
        if not title and not abstract:
            continue

        # 2. Prepare Text for Vectorization
        # Combining Title + Abstract gives the AI the full context of the paper.
        text_to_embed = f"Title: {title}\nAbstract: {abstract}"

        # 3. Generate Embedding (The "Semantic" part)
        # We convert the text into a list of 768 floats.
        vector = model.encode(text_to_embed).tolist()

        # 4. Construct the Document for Elasticsearch
        # The keys here must match the 'properties' defined in create_index()
        es_doc = {
            "_index": INDEX_NAME,
            "_source": {
                "cord_uid": doc.get("cord_uid"),
                "title": title,
                "abstract": abstract,
                "publish_time": doc.get("publish_time"),
                "url": doc.get("url"),
                "journal": doc.get("journal"),
                "authors": doc.get("authors"),
                "embedding": vector  # This is the vector field
            }
        }
        yield es_doc

# ---------------------------------------------------------
# 3. MAIN EXECUTION FLOW
# ---------------------------------------------------------
def index_data(file_path: str):
    # Step 1: Connect to Database
    es = get_es_client(max_retries=3, sleep_time=2)
    
    # Step 2: Load AI Model
    # Checks for GPU (cuda/mps) to speed up embedding generation 10x-50x
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if torch.backends.mps.is_available(): device = torch.device("mps") # Mac M1/M2 support
    
    print(f"Loading Model: {EMBEDDING_MODEL} on {device}...")
    model = SentenceTransformer(EMBEDDING_MODEL).to(device)

    # Step 3: Load Raw Data
    print(f"Loading data from {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        documents = json.load(f)

    # Step 4: Reset Index
    create_index(es)

    # Step 5: Run Bulk Indexing
    # We use chunk_size=100 to avoid overloading memory with vectors
    print("Starting Bulk Indexing...")
    success, failed = helpers.bulk(
        es, 
        generate_actions(documents, model), 
        stats_only=True,
        chunk_size=100
    )
    
    print(f"Index Complete. Success: {success}, Failed: {failed}")
    print(f"Data is ready in index: '{INDEX_NAME}'")

if __name__ == "__main__":
    # Path to your dataset
    DATA_FILE = "../datasets/metadata_sample.json" 
    
    # Trigger the pipeline
    index_data(DATA_FILE)
    
    
# import json
# from pprint import pprint
# from typing import List

# from config import (
#     INDEX_NAME_DEFAULT,
#     INDEX_NAME_N_GRAM,
#     INDEX_NAME_EMBEDDING,
#     EMBEDDING_MODEL,
# )
# from elastic_transport import ObjectApiResponse
# from elasticsearch import Elasticsearch
# from tqdm import tqdm
# from utils import get_es_client

# import torch
# from sentence_transformers import SentenceTransformer


# def index_data(
#     documents: List[dict],
#     use_n_gram_tokenizer: bool,
#     use_embedding: bool,
#     model: SentenceTransformer | None = None,
# ) -> None:
#     es = get_es_client(max_retries=1, sleep_time=1)
#     _ = _create_index(
#         es=es, use_n_gram_tokenizer=use_n_gram_tokenizer, use_embedding=use_embedding
#     )
#     _ = _insert_documents(
#         es=es,
#         documents=documents,
#         use_n_gram_tokenizer=use_n_gram_tokenizer,
#         use_embedding=use_embedding,
#         model=model,
#     )

#     index_name = (
#         INDEX_NAME_N_GRAM
#         if use_n_gram_tokenizer
#         else INDEX_NAME_EMBEDDING if use_embedding else INDEX_NAME_DEFAULT
#     )
#     pprint(
#         f'Indexed {len(documents)} documents into Elasticsearch index "{index_name}"'
#     )


# def _create_index(
#     es: Elasticsearch, use_n_gram_tokenizer: bool, use_embedding: bool
# ) -> ObjectApiResponse:
#     tokenizer = "n_gram_tokenizer" if use_n_gram_tokenizer else "standard"
#     index_name = (
#         INDEX_NAME_N_GRAM
#         if use_n_gram_tokenizer
#         else INDEX_NAME_EMBEDDING if use_embedding else INDEX_NAME_DEFAULT
#     )

#     _ = es.indices.delete(index=index_name, ignore_unavailable=True)
#     if use_embedding:
#         return es.indices.create(
#             index=index_name,
#             mappings={
#                 "properties": {
#                     "embedding": {
#                         "type": "dense_vector",
#                     }
#                 }
#             },
#         )
#     return es.indices.create(
#         index=index_name,
#         body={
#             "settings": {
#                 "analysis": {
#                     "analyzer": {
#                         "default": {
#                             "type": "custom",
#                             "tokenizer": tokenizer,
#                         },
#                     },
#                     "tokenizer": {
#                         "n_gram_tokenizer": {
#                             "type": "edge_ngram",
#                             "min_gram": 1,
#                             "max_gram": 30,
#                             "token_chars": ["letter", "digit"],
#                         },
#                     },
#                 },
#             },
#         },
#     )


# def _insert_documents(
#     es: Elasticsearch,
#     documents: List[dict],
#     use_n_gram_tokenizer: bool,
#     use_embedding: bool,
#     model: SentenceTransformer | None = None,
# ) -> ObjectApiResponse:

#     operations = []
#     index_name = (
#         INDEX_NAME_N_GRAM
#         if use_n_gram_tokenizer
#         else INDEX_NAME_EMBEDDING if use_embedding else INDEX_NAME_DEFAULT
#     )
#     for document in tqdm(documents, total=len(documents), desc="Indexing documents"):
#         operations.append({"index": {"_index": index_name}})
#         if use_embedding and model is not None:
#             operations.append(
#                 {**document, "embedding": model.encode(f"Title:\n {document['title']}\n\n Abstract:\n document['abstract']")}
#             )
#         else:
#             operations.append(document)

#     return es.bulk(operations=operations)


# if __name__ == "__main__":

#     use_embedding = False
#     use_n_gram_tokenizer = False
#     # file_name = "dummy_data/apod.json"
#     file_name = "../datasets/metadata_sample.json"
#     model = None

#     with open(file_name) as f:
#         documents = json.load(f)

#     if use_embedding:
#         device = torch.device(
#             "cuda"
#             if torch.cuda.is_available()
#             else "mps" if torch.backends.mps.is_available() else "cpu"
#         )
#         model = SentenceTransformer(EMBEDDING_MODEL).to(device)
        
#     index_data(
#         documents=documents,
#         use_n_gram_tokenizer=use_n_gram_tokenizer,
#         use_embedding=use_embedding,
#         model=model
#     )

# =================