from transforms import try_parse_order_line

with open("./sample_data/orders.csv", encoding="utf-8") as handle:
    for line in handle:
        row = try_parse_order_line(line)
        if row is None:
            print("rejected:", line.strip())
            continue
        print(row["order_id"], row["region"])
