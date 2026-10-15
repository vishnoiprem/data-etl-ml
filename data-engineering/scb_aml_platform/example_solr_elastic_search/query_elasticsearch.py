from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

# ── Compound bool query with filter, sort, and aggregations ──
response = es.search(
    index="products",
    body={
        "size": 5,
        "query": {
            "bool": {
                "must": [
                    {"match": {"category": "Electronics"}}
                ],
                "filter": [
                    {"range": {"price": {"lte": 500}}},
                    {"term":  {"in_stock": True}}
                ]
            }
        },
        "sort": [{"rating": "desc"}],

        # ── Aggregations: analytics in the same query ──
        "aggs": {
            "avg_price": {"avg": {"field": "price"}},
            "brand_breakdown": {
                "terms": {"field": "brand", "size": 10}
            },
            "price_ranges": {
                "range": {
                    "field": "price",
                    "ranges": [
                        {"to": 50},
                        {"from": 50, "to": 200},
                        {"from": 200, "to": 500}
                    ]
                }
            }
        }
    }
)

# ── Print results ──
print(f"Found: {response['hits']['total']['value']} hits\n")
for hit in response["hits"]["hits"]:
    s = hit["_source"]
    print(f"   {s['rating']} | ${s['price']} | {s['brand']} — {s['name']}")

print(f"\n Avg Price: ${response['aggregations']['avg_price']['value']:.2f}")
print(" Top Brands:")
for b in response["aggregations"]["brand_breakdown"]["buckets"]:
    print(f"   {b['key']}: {b['doc_count']} products")
