import os
import time
from pprint import pprint
from dotenv import load_dotenv

from elasticsearch import Elasticsearch

load_dotenv()

def get_es_client(max_retries: int = 5, sleep_time: int = 2) -> Elasticsearch:
    elastic_api_key = os.getenv("ES_LOCAL_API_KEY")
    i = 0

    while i < max_retries:
        try:
            es = Elasticsearch(
                 "http://localhost:9200",
                 api_key=elastic_api_key
                )
            # pprint("Connected to Elasticsearch!")
            return es
        except Exception:
            pprint("Could not connect to Elasticsearch, retrying...")
            time.sleep(sleep_time)
            i += 1
    raise ConnectionError("Failed to connect to Elasticsearch after multiple attempts.")

if __name__ == "__main__":
    # Ensure Elastic Search is running
    # check connect to Elastic Search
    get_es_client()