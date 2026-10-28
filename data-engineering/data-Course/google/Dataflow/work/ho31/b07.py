from apache_beam.pvalue import Row

row = Row(order_id="o1", region="EMEA", amount=100.0)
print(row.order_id)          # o1
print(row.as_dict())         # {'order_id': 'o1', ...}
