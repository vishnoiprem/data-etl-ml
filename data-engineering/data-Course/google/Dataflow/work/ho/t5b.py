import shutil
import apache_beam as beam

INPUT = "./sample_data/orders.csv"
CSV_OUTPUT = "./out/hands_on/fanout_csv"
AUDIT_OUTPUT = "./out/hands_on/fanout_audit"

def main():
    for path in (CSV_OUTPUT, AUDIT_OUTPUT):
        shutil.rmtree(path, ignore_errors=True)
    with beam.Pipeline() as pipeline:
        lines = pipeline | "ReadOrders" >> beam.io.ReadFromText(INPUT)
        orders = lines | "ParseOrders" >> beam.Map(lambda line: line.split(","))
        (orders
         | "FormatSummary" >> beam.Map(lambda row: f"{row[3]},{row[6]},{row[7]}")
         | "WriteCsv" >> beam.io.WriteToText(CSV_OUTPUT, num_shards=1, shard_name_template=""))
        (orders
         | "FormatAudit" >> beam.Map(lambda row: ",".join(row))
         | "WriteAudit" >> beam.io.WriteToText(AUDIT_OUTPUT, num_shards=1, shard_name_template=""))
        (orders
         | "CountRows" >> beam.combiners.Count.Globally()
         | "LogCount" >> beam.Map(lambda count: print(f"rows seen: {count}")))
main()
