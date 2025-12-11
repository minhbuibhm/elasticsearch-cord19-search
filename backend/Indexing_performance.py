import time
import json
import torch
from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer
from typing import List, Generator
from tqdm import tqdm
from index_data import create_index, generate_actions

# Giả sử các cấu hình đã được định nghĩa hoặc import từ config.py/index_data.py
INDEX_NAME = "cord19_hybrid_search"
EMBEDDING_MODEL = "allenai/scibert_scivocab_uncased"
INPUT_FILE = "../datasets/ready_for_indexing.json" 

try:
    from utils import get_es_client
except ImportError:
    # Fallback if utils.py is missing
    def get_es_client(max_retries=3, sleep_time=1):
        return Elasticsearch("http://localhost:9200", request_timeout=300)


def index_data(file_path: str):
    # 1. Kết nối ES và Load Model
    print("Khởi tạo kết nối và model...")
    es = get_es_client(max_retries=3, sleep_time=2)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if torch.backends.mps.is_available(): device = torch.device("mps")
    
    print(f"Loading Model: {EMBEDDING_MODEL} on {device}...")
    model = SentenceTransformer(EMBEDDING_MODEL).to(device)

    # 2. Load Data
    print(f"Loading data from {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    create_index(es)

    # 3. Bắt đầu đo thời gian
    print("--- BẮT ĐẦU ĐO THỜI GIAN INDEXING ---")
    start_time = time.time() # <--- Bắt đầu bấm giờ

    # ... (code chạy bulk indexing) ...
    success, failed = helpers.bulk(es, generate_actions(documents, model), chunk_size=100)
    success = len(documents)

    end_time = time.time()   # <--- Kết thúc bấm giờ
    
    duration = end_time - start_time
    print(f"⏱️ Tổng thời gian Indexing: {duration:.2f} giây")
    if duration > 0:
        print(f"⚡ Tốc độ trung bình: {len(documents) / duration:.2f} docs/giây")
    else:
        print("⚡ Tốc độ trung bình: Rất nhanh (vô cực docs/giây)")

if __name__ == "__main__":
    # Tạo dummy file nếu cần hoặc trỏ đúng đường dẫn
    index_data(INPUT_FILE)