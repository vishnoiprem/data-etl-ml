import pysolr

solr = pysolr.Solr("http://localhost:8983/solr/products")

# ── Solr uses Lucene query syntax + filter queries (fq) ──
results = solr.search(
    q="category:Electronics",
    fq=[
        "price:[* TO 500]",       # range filter
        "in_stock:true"             # boolean filter
    ],
    sort="rating desc",
    rows=5,
    # ── Faceting: Solr's analytics equivalent ──
    **{
        "facet":       "on",
        "facet.field": "brand",
        "facet.range": "price",
        "f.price.facet.range.start": "0",
        "f.price.facet.range.end":   "500",
        "f.price.facet.range.gap":   "100",
        "stats":       "true",
        "stats.field": "price",
    }
)

print(f"Found: {results.hits} hits\n")
for doc in results:
    print(f"   {doc['rating']} | ${doc['price']} | {doc['brand']} — {doc['name']}")

print(f"\n Price Stats: {results.stats['stats_fields']['price']}")
print(f" Brand Facets: {results.facets['facet_fields']['brand']}")