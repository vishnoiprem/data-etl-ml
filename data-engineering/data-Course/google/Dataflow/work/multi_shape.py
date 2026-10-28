import json
import apache_beam as beam
import apache_beam.typehints as th

RECORD_TYPE = th.Tuple[str, th.Dict[str, th.Any]]

def order_to_record(line: str) -> dict:
    parts = line.split(",")
    return {"id": parts[0], "region": parts[3], "value": float(parts[7])}

def event_to_record(line: str) -> dict:
    payload = json.loads(line)
    return {"id": payload["event_id"], "region": payload["region"], "value": float(payload["value"])}

with beam.Pipeline() as p:
    orders = (
        p
        | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")
        | "SkipHeader" >> beam.Filter(lambda line: not line.startswith("order_id"))
        | "ParseOrders" >> beam.Map(order_to_record)
        | "TagOrders" >> beam.Map(lambda record: ("order", record)).with_output_types(RECORD_TYPE)
    )
    events = (
        p
        | "ReadEvents" >> beam.io.ReadFromText("./sample_data/events.ndjson")
        | "ParseEvents" >> beam.Map(event_to_record)
        | "TagEvents" >> beam.Map(lambda record: ("event", record)).with_output_types(RECORD_TYPE)
    )
    merged = (orders, events) | "Flatten" >> beam.Flatten()
    (
        merged
        | "TotalBySource" >> beam.Map(lambda tagged: (tagged[0], tagged[1]["value"]))
        | "SumBySource" >> beam.CombinePerKey(sum)
        | "Format" >> beam.Map(lambda kv: f"{kv[0]},{kv[1]:.2f}")
        | "Write" >> beam.io.WriteToText("./out/totals_by_source", num_shards=1, shard_name_template="")
    )
