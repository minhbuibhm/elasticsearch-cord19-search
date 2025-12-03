from elasticsearch import Elasticsearch
from pprint import pprint
from utils import get_es_client

# Connect
es = get_es_client()
INDEX = "cord19_hybrid_search"
DOC_ID = "wnIi5ZoB2-yUxg_e24Xz" # The ID causing issues

print(f"--- INSPECTING DOCUMENT: {DOC_ID} ---")

if not es.indices.exists(index=INDEX):
    print(f"❌ Index '{INDEX}' does not exist!")
    exit()

try:
    # 1. Get the Source
    doc = es.get(index=INDEX, id=DOC_ID)
    source = doc['_source']
    
    print(f"✅ Document Found in '{INDEX}'")
    print(f"Keys in _source: {list(source.keys())}")
    
    if "embedding" in source:
        vec = source['embedding']
        print(f"✅ Embedding Field Exists!")
        print(f"   Type: {type(vec)}")
        print(f"   Length: {len(vec) if isinstance(vec, list) else 'N/A'}")
        print(f"   Sample: {vec[:5]}...")
    else:
        print(f"❌ Embedding Field is MISSING from _source.")
        print("   This is why kNN lookup fails.")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n--- MAPPING CHECK ---")
mapping = es.indices.get_mapping(index=INDEX)
props = mapping[INDEX]['mappings']['properties']
if "embedding" in props:
    print("✅ Mapping for 'embedding' exists:")
    pprint(props['embedding'])
else:
    print("❌ 'embedding' is NOT in the mapping properties.")