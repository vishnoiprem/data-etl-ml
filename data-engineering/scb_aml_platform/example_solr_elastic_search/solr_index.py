import pysolr
import json, time

solr = pysolr.Solr("http://localhost:8983/solr/products", always_commit=False)

with open("products.json") as f:
    products = json.load(f)

# ── Bulk index in batches ──
BATCH = 500
start = time.time()

for i in range(0, len(products), BATCH):
    batch = products[i : i + BATCH]
    solr.add(batch)

solr.commit()  # make all docs searchable
elapsed = time.time() - start

print(f" Solr: Indexed {len(products)} docs in {elapsed:.2f}s")

# Verify count
results = solr.search("*:*", rows=0)
print(f"   Total in Solr: {results.hits}")