view: orders {
  label: "Orders"
  description: "One row per order line. Note the grain: a single order with three lines appears three times."
  # Grain: one row per order line
  sql: "select * from analytics.orders";

  dimension: order_id {
    label: "Order ID"
    type: string
    sql: "order_id"
    description: "The order identifier. NOT unique — one order has many lines. Use line_id to identify a row."
  }

  dimension: line_id {
    label: "Order Line ID"
    type: string
    sql: "line_id"
    description: "The unique order-line identifier. The grain."
  }

  dimension: customer_id {
    label: "Customer"
    type: string
    sql: "customer_id"
    description: "The customer who placed the order."
  }

  dimension: region {
    label: "Region"
    type: string
    sql: "region"
    description: "Sales region: EMEA, AMER, APAC or LATAM."
  }

  dimension: channel {
    label: "Channel"
    type: string
    sql: "channel"
    description: "Sales channel: web, app, store or partner."
  }

  dimension: status {
    label: "Status"
    type: string
    sql: "status"
    description: "Order status."
  }

  dimension: created_at {
    label: "Order Date"
    type: time
    sql: "created_at"
    timeframe: "raw, day, week, month, quarter, year"
    description: "When the order was placed."
  }

  dimension: product_category {
    label: "Product Category"
    type: string
    sql: "product_category"
    description: "The category of the product on the line."
  }

  measure: total_revenue {
    label: "Total Revenue"
    type: sum
    sql: "total_amount"
    description: "Sum of order line revenue."
  }

  measure: order_count {
    label: "Order Count"
    type: count
    sql: "order_id"
    description: "Number of order lines. To count orders rather than lines, use count_distinct on order_id."
  }

  measure: distinct_orders {
    label: "Distinct Orders"
    type: count
    sql: "order_id"
    description: "Number of unique orders."
  }

  measure: average_order_value {
    label: "Average Order Value"
    type: average
    sql: "total_amount"
    description: "Average revenue per order line."
  }

  measure: gross_margin {
    label: "Gross Margin"
    type: ratio
    sql: "margin_amount"
    filters: "total_amount"
    description: "Margin over revenue."
  }

  join: customers {
    relationship: many_to_one
    sql_on: "orders.customer_id = customers.customer_id"
    description: "Many order lines belong to one customer. Safe to traverse: it does not fan out."
  }

  join: products {
    relationship: many_to_one
    sql_on: "orders.product_id = products.product_id"
    description: "Many order lines reference one product. Safe to traverse."
  }
}

view: customers {
  label: "Customers"
  description: "One row per customer."
  # Grain: one row per customer
  sql: "select * from analytics.customers";

  dimension: customer_id {
    label: "Customer ID"
    type: string
    sql: "customer_id"
    description: "The unique customer identifier. The grain of this table."
  }

  dimension: customer_segment {
    label: "Segment"
    type: string
    sql: "segment"
    description: "The customer's marketing segment."
  }

  dimension: country {
    label: "Country"
    type: string
    sql: "country"
    description: "The customer's country. A conformed dimension — the same meaning in every fact table that joins it."
  }

  dimension: signup_date {
    label: "Signup Date"
    type: time
    sql: "signup_date"
    timeframe: "raw, day, month, year"
    description: "When the customer signed up. Note this is the current value only — the table is SCD Type 1, so a segment change overwrites rather than adding a row."
  }

  measure: customer_count {
    label: "Customers"
    type: count
    sql: "customer_id"
    description: "Number of customers."
  }

  measure: lifetime_value {
    label: "Lifetime Value"
    type: sum
    sql: "lifetime_value"
    description: "Total spend recorded on the customer record."
  }

  join: orders {
    relationship: one_to_many
    sql_on: "customers.customer_id = orders.customer_id"
    description: "One customer has many orders. Traversing this fan-outs the order lines — and therefore the revenue — unless the measure is a distinct count."
  }
}

view: products {
  label: "Products"
  description: "One row per product."
  # Grain: one row per product
  sql: "select * from analytics.products";

  dimension: product_id {
    label: "Product ID"
    type: string
    sql: "product_id"
    description: "The unique product identifier. The grain of this table."
  }

  dimension: product_category {
    label: "Category"
    type: string
    sql: "category"
    description: "The product's catalogue category."
  }

  dimension: supplier {
    label: "Supplier"
    type: string
    sql: "supplier"
    description: "The supplier who provides the product."
  }

  measure: product_count {
    label: "Products"
    type: count
    sql: "product_id"
    description: "Number of distinct products. Non-additive — the same product appears in many order lines."
  }

  measure: list_price {
    label: "List Price"
    type: average
    sql: "list_price"
    description: "Average list price across the product table. Non-additive — never sum it."
  }
}


explore: orders {
  label: "Orders"
  description: "The order-line explore the reports are built on."
  join: "customers, products"
}

explore: customers {
  label: "Customers"
  description: "A customer explore, for segmentation questions."
  join: "orders"
}
