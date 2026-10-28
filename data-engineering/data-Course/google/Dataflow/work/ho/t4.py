import json, shutil
import apache_beam as beam

ORDERS = "./sample_data/orders.csv"
REFERENCE = "./sample_data/product_reference.ndjson"
OUTPUT = "./out/hands_on/enriched"

def parse_reference_line(line):
    text = line.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}

def enrich(order, categories):
    order["category"] = categories.get(order.get("product_id"), "unknown")
    return order

def main():
    shutil.rmtree(OUTPUT, ignore_errors=True)
    with beam.Pipeline() as pipeline:
        lines = pipeline | "ReadOrders" >> beam.io.ReadFromText(ORDERS)
        orders = lines | "ParseOrders" >> beam.Map(lambda line: line)
        reference = (
            pipeline
            | "ReadReference" >> beam.io.ReadFromText(REFERENCE)
            | "ParseReference" >> beam.Map(parse_reference_line)
            | "KeyByProductId" >> beam.Map(lambda row: (row.get("product_id"), row.get("category", "unknown")))
            | "ToDict" >> beam.pvalue.AsDict()
        )
        enriched = orders | "EnrichWithCategory" >> beam.Map(enrich, categories=reference)
        (enriched
         | "Format" >> beam.Map(lambda order: f"{order.get('product_id')},{order.get('category')}")
         | "Write" >> beam.io.WriteToText(OUTPUT, num_shards=1, shard_name_template=""))
    with open(OUTPUT, encoding="utf-8") as handle:
        ls = handle.read().splitlines()
    print(f"enriched {len(ls)} orders")
    for line in ls[:5]:
        print(" ", line)
main()
