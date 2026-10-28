import sys
sys.path.insert(0, "./project")
import apache_beam as beam
from transforms import ParseOrderFn, RevenueByRegionFn

with beam.Pipeline() as p:
    lines = p | "ReadOrders" >> beam.io.ReadFromText("./sample_data/orders.csv")
    orders = lines | "ParseOrders" >> beam.ParDo(ParseOrderFn())
    keyed = orders | "KeyByRegion" >> beam.Map(lambda o: (o["region"], o))
    kept = keyed | "KeepComplete" >> beam.Filter(lambda pair: pair[1]["status"] == "complete")
    kept | "Rev" >> beam.CombinePerKey(RevenueByRegionFn()) | "P" >> beam.Map(print)
