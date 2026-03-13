from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import json
import time

INDEX = "products"

es = Elasticsearch(
    "http://localhost:9200",
    request_timeout=30
)

print("Client:", es)

try:
    print("Ping:", es.ping())
    print("Info:", es.info())
except Exception as e:
    print("Connection/info error:", repr(e))
    raise

mapping = {
    "settings": {
        "number_of_shards": 2,
        "number_of_replicas": 0,
        "refresh_interval": "-1"
    },
    "mappings": {
        "properties": {
            "name": {"type": "text", "analyzer": "standard"},
            "description": {"type": "text", "analyzer": "standard"},
            "category": {"type": "keyword"},
            "brand": {"type": "keyword"},
            "price": {"type": "float"},
            "rating": {"type": "float"},
            "in_stock": {"type": "boolean"},
            "reviews": {"type": "integer"}
        }
    }
}

try:
    if es.indices.exists(index=INDEX):
        es.indices.delete(index=INDEX)

    es.indices.create(index=INDEX, body=mapping)
except Exception as e:
    print("Index setup error:", repr(e))
    raise

with open("products.json", "r") as f:
    products = json.load(f)

def gen_actions(items):
    for p in items:
        yield {
            "_index": INDEX,
            "_id": p["id"],
            "_source": p
        }

start = time.time()
result = bulk(es, gen_actions(products), chunk_size=500)
elapsed = time.time() - start

es.indices.put_settings(index=INDEX, body={"refresh_interval": "1s"})
es.indices.refresh(index=INDEX)

print("Bulk result:", result)
print(f"Indexed in {elapsed:.2f}s")