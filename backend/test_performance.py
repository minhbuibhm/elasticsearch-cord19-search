"""
------------------------------------------------
Tiêu chuẩn thực nghiệm:
1. Warm-up: 5 lần chạy đầu không tính giờ để cache hệ thống.
2. Iterations: 30 lần chạy cho mỗi query để lấy mẫu thống kê.
3. Metrics: Avg, Median, P95, P99.
------------------------------------------------
"""

import time
import statistics
import csv
from fastapi.testclient import TestClient
from main import app
from tabulate import tabulate
import numpy as np 

client = TestClient(app)

# Cấu hình thực nghiệm
N_WARMUP = 5
N_ITERATIONS = 20  # Số lần chạy lặp lại cho mỗi query
TOP_K = 10         # Số lượng kết quả lấy về

TEST_QUERIES = [
    # Nhóm Keyword (BM25 thường tốt)
    "remdesivir clinical trial",
    "SARS-CoV-2 spike protein structure",
    "hydroxychloroquine efficacy",
    # Nhóm Semantic (Vector thường tốt)
    "symptoms of respiratory failure",
    "impact of lockdown on mental health",
    "transmission via aerosols",
    # Nhóm Mixed (Hybrid thường tốt)
    "neurological complications in covid-19 patients",
    "effectiveness of face masks in preventing transmission",
    "long-term effects of covid-19 infection",
    "incubation period of omicron variant"
]

ENDPOINTS = {
    "BM25": "/api/v1/regular_search/",
    "SciBERT": "/api/v1/semantic_search/",
    "Hybrid": "/api/v1/hybrid_search/"
}

def measure_request(endpoint, query):
    start = time.perf_counter() # Dùng perf_counter chính xác hơn time.time
    try:
        resp = client.get(endpoint, params={"search_query": query, "limit": TOP_K})
        if resp.status_code != 200: return None
    except:
        return None
    end = time.perf_counter()
    return (end - start) * 1000 # ms

def run_latency_benchmark():
    print(f"🚀 BẮT ĐẦU BENCHMARK HIỆU NĂNG (Warmup={N_WARMUP}, Iterations={N_ITERATIONS})")
    
    # 1. Warm-up Phase
    print("🔥 Đang Warm-up hệ thống (Load model vào RAM, Cache Elasticsearch)...")
    for _ in range(N_WARMUP):
        for endpoint in ENDPOINTS.values():
            client.get(endpoint, params={"search_query": "covid", "limit": 5})
    
    final_results = {method: [] for method in ENDPOINTS}

    # 2. Testing Phase
    print("⏱️ Đang đo lường...")
    for q_idx, query in enumerate(TEST_QUERIES):
        print(f"   Query {q_idx+1}/{len(TEST_QUERIES)}: {query}")
        
        for method, endpoint in ENDPOINTS.items():
            query_latencies = []
            for _ in range(N_ITERATIONS):
                lat = measure_request(endpoint, query)
                if lat: query_latencies.append(lat)
            
            # Lưu trung bình của query này vào tổng kết
            if query_latencies:
                final_results[method].extend(query_latencies)

    # 3. Report
    headers = ["Method", "Samples", "Avg (ms)", "Median", "P95", "P99", "Min", "Max"]
    table_data = []
    
    csv_data = []

    for method, latencies in final_results.items():
        if not latencies: continue
        
        avg = statistics.mean(latencies)
        median = statistics.median(latencies)
        p95 = np.percentile(latencies, 95)
        p99 = np.percentile(latencies, 99)
        mn = min(latencies)
        mx = max(latencies)
        
        table_data.append([method, len(latencies), f"{avg:.2f}", f"{median:.2f}", f"{p95:.2f}", f"{p99:.2f}", f"{mn:.2f}", f"{mx:.2f}"])
        csv_data.append({"Method": method, "Avg": avg, "P95": p95})

    print("\n📊 KẾT QUẢ CUỐI CÙNG:")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Lưu file CSV để vẽ biểu đồ nếu cần
    keys = csv_data[0].keys()
    with open('benchmark_latency.csv', 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(csv_data)
    print("\n✅ Đã lưu kết quả chi tiết vào 'benchmark_latency.csv'")

if __name__ == "__main__":
    try:
        run_latency_benchmark()
    except Exception as e:
        print(f"Error: {e}")