import json
from pprint import pprint
from typing import List

from config import (
    INDEX_NAME_DEFAULT,
    INDEX_NAME_N_GRAM,
    INDEX_NAME_EMBEDDING,
    EMBEDDING_MODEL,
)
from elastic_transport import ObjectApiResponse
from elasticsearch import Elasticsearch
from tqdm import tqdm
from utils import get_es_client

import torch
from sentence_transformers import SentenceTransformer


def index_data(
    documents: List[dict],
    use_n_gram_tokenizer: bool,
    use_embedding: bool,
    model: SentenceTransformer | None = None,
) -> None:
    es = get_es_client(max_retries=1, sleep_time=1)
    _ = _create_index(
        es=es, use_n_gram_tokenizer=use_n_gram_tokenizer, use_embedding=use_embedding
    )
    _ = _insert_documents(
        es=es,
        documents=documents,
        use_n_gram_tokenizer=use_n_gram_tokenizer,
        use_embedding=use_embedding,
        model=model,
    )

    index_name = (
        INDEX_NAME_N_GRAM
        if use_n_gram_tokenizer
        else INDEX_NAME_EMBEDDING if use_embedding else INDEX_NAME_DEFAULT
    )
    pprint(
        f'Indexed {len(documents)} documents into Elasticsearch index "{index_name}"'
    )


def _create_index(
    es: Elasticsearch, use_n_gram_tokenizer: bool, use_embedding: bool
) -> ObjectApiResponse:
    tokenizer = "n_gram_tokenizer" if use_n_gram_tokenizer else "standard"
    index_name = (
        INDEX_NAME_N_GRAM
        if use_n_gram_tokenizer
        else INDEX_NAME_EMBEDDING if use_embedding else INDEX_NAME_DEFAULT
    )

    _ = es.indices.delete(index=index_name, ignore_unavailable=True)
    if use_embedding:
        return es.indices.create(
            index=index_name,
            mappings={
                "properties": {
                    "embedding": {
                        "type": "dense_vector",
                    }
                }
            },
        )
    return es.indices.create(
        index=index_name,
        body={
            "settings": {
                "analysis": {
                    "analyzer": {
                        "default": {
                            "type": "custom",
                            "tokenizer": tokenizer,
                        },
                    },
                    "tokenizer": {
                        "n_gram_tokenizer": {
                            "type": "edge_ngram",
                            "min_gram": 1,
                            "max_gram": 30,
                            "token_chars": ["letter", "digit"],
                        },
                    },
                },
            },
        },
    )


def _insert_documents(
    es: Elasticsearch,
    documents: List[dict],
    use_n_gram_tokenizer: bool,
    use_embedding: bool,
    model: SentenceTransformer | None = None,
) -> ObjectApiResponse:

    operations = []
    index_name = (
        INDEX_NAME_N_GRAM
        if use_n_gram_tokenizer
        else INDEX_NAME_EMBEDDING if use_embedding else INDEX_NAME_DEFAULT
    )
    for document in tqdm(documents, total=len(documents), desc="Indexing documents"):
        operations.append({"index": {"_index": index_name}})
        if use_embedding and model is not None:
            operations.append(
                {**document, "embedding": model.encode(f"Title:\n {document['title']}\n\n Abstract:\n document['abstract']")}
            )
        else:
            operations.append(document)

    return es.bulk(operations=operations)


if __name__ == "__main__":

    use_embedding = True
    use_n_gram_tokenizer = False
    # file_name = "dummy_data/apod.json"
    file_name = "../datasets/metadata_sample.json"
    model = None

    with open(file_name) as f:
        documents = json.load(f)

    if use_embedding:
        device = torch.device(
            "cuda"
            if torch.cuda.is_available()
            else "mps" if torch.backends.mps.is_available() else "cpu"
        )
        model = SentenceTransformer(EMBEDDING_MODEL).to(device)
        
    index_data(
        documents=documents,
        use_n_gram_tokenizer=use_n_gram_tokenizer,
        use_embedding=use_embedding,
        model=model
    )
