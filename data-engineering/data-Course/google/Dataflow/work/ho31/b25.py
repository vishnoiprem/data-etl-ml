import pyarrow.parquet as pq

table = pq.read_table("./out/hands_on/orders_parquet-00000-of-00001")
print(table.schema)
print(table.num_rows, "rows")
print(table.to_pydict()["region"][:5])
