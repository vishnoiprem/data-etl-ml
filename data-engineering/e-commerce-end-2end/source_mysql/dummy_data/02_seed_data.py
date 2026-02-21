"""
E-Commerce Dummy Data Generator
Generates realistic Shopee/Lazada-style data for MySQL
"""
import random
import string
import json
from datetime import datetime, timedelta
from decimal import Decimal
import mysql.connector
from faker import Faker

fake = Faker(['th_TH', 'en_US'])
random.seed(42)

# ── DB Config ────────────────────────────────────────────────
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "ecommerce123",
    "database": "ecommerce_db",
    "charset": "utf8mb4",
}

# ── Constants ────────────────────────────────────────────────
CATEGORIES = [
    (1, None, "Electronics", "electronics", 1),
    (2, 1, "Smartphones", "smartphones", 2),
    (3, 1, "Laptops", "laptops", 2),
    (4, 1, "Audio", "audio", 2),
    (5, None, "Fashion", "fashion", 1),
    (6, 5, "Men's Clothing", "mens-clothing", 2),
    (7, 5, "Women's Clothing", "womens-clothing", 2),
    (8, 5, "Shoes", "shoes", 2),
    (9, None, "Home & Living", "home-living", 1),
    (10, 9, "Furniture", "furniture", 2),
    (11, 9, "Kitchen", "kitchen", 2),
    (12, None, "Beauty & Health", "beauty-health", 1),
    (13, 12, "Skincare", "skincare", 2),
    (14, 12, "Supplements", "supplements", 2),
    (15, None, "Sports & Outdoors", "sports-outdoors", 1),
]

BRANDS = [
    "Samsung", "Apple", "Xiaomi", "OPPO", "Huawei",
    "Nike", "Adidas", "Uniqlo", "H&M", "Zara",
    "IKEA", "Philips", "Bosch", "Sony", "LG",
    "L'Oreal", "Nivea", "Maybelline", "The Body Shop", "Cetaphil",
]

CARRIERS = ["Kerry Express", "Flash Express", "J&T Express", "SCG Yamato", "DHL"]
PAYMENT_METHODS = ["credit_card", "debit_card", "bank_transfer", "wallet", "cod"]
CITIES_TH = ["Bangkok", "Chiang Mai", "Phuket", "Pattaya", "Khon Kaen", "Nakhon Ratchasima", "Hat Yai"]
DEVICE_TYPES = ["mobile", "desktop", "tablet"]
PLATFORMS = ["ios", "android", "web"]


def rand_date(start_days_ago=365, end_days_ago=0):
    start = datetime.now() - timedelta(days=start_days_ago)
    end = datetime.now() - timedelta(days=end_days_ago)
    return start + (end - start) * random.random()


def rand_order_no():
    return "ORD" + datetime.now().strftime("%Y%m%d") + "".join(random.choices(string.digits, k=8))


def seed_all():
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("Connected to MySQL. Starting seed...")

    # ── Categories ───────────────────────────────────────────
    print("Seeding categories...")
    for cat in CATEGORIES:
        cur.execute("""
            INSERT IGNORE INTO categories (category_id, parent_id, name, slug, level)
            VALUES (%s, %s, %s, %s, %s)
        """, cat)
    conn.commit()

    # ── Brands ───────────────────────────────────────────────
    print("Seeding brands...")
    for brand in BRANDS:
        slug = brand.lower().replace(" ", "-").replace("'", "")
        cur.execute("INSERT IGNORE INTO brands (name, slug) VALUES (%s, %s)", (brand, slug))
    conn.commit()

    # ── Users ────────────────────────────────────────────────
    print("Seeding 500 users...")
    user_ids = []
    for i in range(500):
        username = fake.user_name() + str(random.randint(100, 9999))
        email = f"user{i+1}@ecom-demo.com"
        phone = f"+66{random.randint(800000000, 899999999)}"
        utype = random.choices(["buyer", "seller", "both"], weights=[70, 15, 15])[0]
        created = rand_date(730, 0)
        cur.execute("""
            INSERT INTO users (username, email, phone, password_hash, full_name, gender,
                               user_type, status, is_verified, country_code, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            username, email, phone,
            "$2b$12$fakehashforseedingonly" + str(i),
            fake.name(), random.choice(["M", "F"]),
            utype, "active",
            random.choice([0, 1]),
            "TH", created
        ))
        user_ids.append(cur.lastrowid)
    conn.commit()

    # ── Addresses ────────────────────────────────────────────
    print("Seeding addresses...")
    for uid in user_ids:
        for _ in range(random.randint(1, 3)):
            city = random.choice(CITIES_TH)
            cur.execute("""
                INSERT INTO user_addresses
                    (user_id, label, recipient_name, phone, address_line1, city, postal_code, country_code, is_default)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                uid, random.choice(["Home", "Office", "Other"]),
                fake.name(), f"+66{random.randint(800000000,899999999)}",
                fake.street_address(), city,
                str(random.randint(10000, 99999)), "TH",
                1 if _ == 0 else 0
            ))
    conn.commit()

    # ── Sellers ──────────────────────────────────────────────
    print("Seeding 50 sellers...")
    seller_ids = []
    seller_user_ids = [uid for i, uid in enumerate(user_ids) if i < 80][:50]
    for uid in seller_user_ids:
        shop = fake.company() + " Shop"
        slug = shop.lower().replace(" ", "-").replace(",", "").replace(".", "")[:50] + str(uid)
        cur.execute("""
            INSERT INTO sellers
                (user_id, shop_name, shop_slug, seller_type, status, rating, total_reviews,
                 total_sales, response_rate, joined_date, warehouse_city, commission_rate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            uid, shop, slug,
            random.choice(["individual", "enterprise"]),
            "active",
            round(random.uniform(3.5, 5.0), 2),
            random.randint(10, 5000),
            random.randint(100, 100000),
            round(random.uniform(80, 100), 2),
            rand_date(1000, 30).date(),
            random.choice(CITIES_TH),
            round(random.uniform(2, 8), 2)
        ))
        seller_ids.append(cur.lastrowid)
    conn.commit()

    # ── Warehouses ───────────────────────────────────────────
    print("Seeding warehouses...")
    warehouse_ids = []
    wh_data = [
        ("BKK-01", "Bangkok Central", "Bangkok", 13.7563, 100.5018),
        ("BKK-02", "Bangkok North", "Bangkok", 13.8621, 100.4477),
        ("CNX-01", "Chiang Mai Hub", "Chiang Mai", 18.7883, 98.9853),
        ("HKT-01", "Phuket Hub", "Phuket", 7.9519, 98.3381),
        ("KKN-01", "Khon Kaen Hub", "Khon Kaen", 16.4419, 102.8360),
    ]
    for code, name, city, lat, lng in wh_data:
        cur.execute("""
            INSERT INTO warehouses (name, code, type, city, country_code, latitude, longitude, capacity_sqm, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, code, "fulfillment", city, "TH", lat, lng, random.uniform(5000, 50000), 1))
        warehouse_ids.append(cur.lastrowid)
    conn.commit()

    # ── Products & SKUs ──────────────────────────────────────
    print("Seeding 200 products with SKUs...")
    sku_ids = []
    product_ids = []
    leaf_cats = [2, 3, 4, 6, 7, 8, 10, 11, 13, 14, 15]
    brand_ids = list(range(1, len(BRANDS) + 1))

    product_templates = [
        ("Samsung Galaxy S24 Ultra", 2, 1, 35000, 45000),
        ("iPhone 15 Pro Max", 2, 2, 40000, 55000),
        ("Xiaomi 14", 2, 3, 15000, 20000),
        ("MacBook Pro M3", 3, 2, 55000, 80000),
        ("Dell XPS 15", 3, 14, 45000, 60000),
        ("Sony WH-1000XM5 Headphones", 4, 14, 8000, 12000),
        ("Nike Air Max 2024", 8, 6, 3500, 6000),
        ("Adidas Ultraboost 23", 8, 7, 4000, 7000),
        ("Uniqlo Heattech Crew Neck", 6, 9, 299, 599),
        ("IKEA LACK Side Table", 10, 19, 599, 999),
        ("Philips Air Fryer", 11, 13, 2500, 4500),
        ("Cetaphil Moisturizing Lotion", 13, 20, 350, 550),
        ("L'Oreal Serum", 13, 1, 800, 1500),
        ("Vitamin C Supplement 1000mg", 14, 14, 250, 600),
        ("Yoga Mat Premium", 15, 7, 500, 1200),
    ]

    for i in range(200):
        tmpl = product_templates[i % len(product_templates)]
        name = tmpl[0] + f" - Model {i+1}"
        cat_id = tmpl[1]
        brand_id = tmpl[2]
        min_p = tmpl[3] * random.uniform(0.8, 1.2)
        max_p = tmpl[4] * random.uniform(0.8, 1.2)
        seller_id = random.choice(seller_ids)
        created = rand_date(500, 0)

        cur.execute("""
            INSERT INTO products
                (seller_id, category_id, brand_id, name, slug, status, condition_type,
                 min_price, max_price, total_sold, total_views, rating, review_count, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            seller_id, cat_id, brand_id, name,
            name.lower().replace(" ", "-")[:100] + f"-{i}",
            "active", "new",
            round(min_p, 2), round(max_p, 2),
            random.randint(0, 10000),
            random.randint(100, 500000),
            round(random.uniform(3.0, 5.0), 2),
            random.randint(0, 2000),
            created
        ))
        product_id = cur.lastrowid
        product_ids.append(product_id)

        # 1-4 SKUs per product
        colors = ["Red", "Blue", "Black", "White", "Green", "Gold"]
        sizes = ["S", "M", "L", "XL", "XXL", "One Size"]
        for j in range(random.randint(1, 4)):
            attrs = {}
            if cat_id in [6, 7, 8]:
                attrs = {"color": random.choice(colors), "size": random.choice(sizes)}
            elif cat_id == 2:
                attrs = {"color": random.choice(colors), "storage": random.choice(["128GB", "256GB", "512GB"])}
            else:
                attrs = {"variant": f"Option {j+1}"}

            price = round(random.uniform(min_p, max_p), 2)
            sku_code = f"SKU-{product_id:06d}-{j:02d}"
            stock = random.randint(0, 500)

            cur.execute("""
                INSERT INTO product_skus
                    (product_id, sku_code, variant_name, attributes, price, original_price,
                     cost_price, stock_quantity, weight_kg, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                product_id, sku_code,
                " / ".join(attrs.values()),
                json.dumps(attrs),
                price,
                round(price * random.uniform(1.1, 1.5), 2),
                round(price * random.uniform(0.4, 0.7), 2),
                stock,
                round(random.uniform(0.1, 10.0), 3),
                "active" if stock > 0 else "out_of_stock"
            ))
            sku_id = cur.lastrowid
            sku_ids.append(sku_id)

            # Inventory per warehouse
            for wh_id in warehouse_ids:
                qty = random.randint(0, 200)
                cur.execute("""
                    INSERT INTO inventory (sku_id, warehouse_id, quantity, reserved_qty, reorder_point, reorder_qty)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (sku_id, wh_id, qty, random.randint(0, min(qty, 20)), 10, 50))
    conn.commit()
    print(f"  Created {len(product_ids)} products, {len(sku_ids)} SKUs")

    # ── Orders ───────────────────────────────────────────────
    print("Seeding 2000 orders...")
    order_ids = []
    statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
    weights = [5, 10, 10, 15, 50, 10]

    for _ in range(2000):
        user_id = random.choice(user_ids)
        seller_id = random.choice(seller_ids)
        status = random.choices(statuses, weights=weights)[0]
        pay_method = random.choice(PAYMENT_METHODS)
        pay_status = "paid" if status in ["confirmed", "processing", "shipped", "delivered"] else "pending"
        created = rand_date(365, 0)
        subtotal = round(random.uniform(200, 15000), 2)
        shipping = round(random.uniform(30, 150), 2)
        discount = round(subtotal * random.uniform(0, 0.15), 2)
        total = round(subtotal + shipping - discount, 2)

        city = random.choice(CITIES_TH)
        addr = {
            "recipient": fake.name(),
            "phone": f"+66{random.randint(800000000,899999999)}",
            "address": fake.street_address(),
            "city": city,
            "postal_code": str(random.randint(10000, 99999)),
            "country": "TH"
        }

        shipped_at = (created + timedelta(days=random.randint(1, 3))) if status in ["shipped", "delivered"] else None
        delivered_at = (shipped_at + timedelta(days=random.randint(1, 7))) if status == "delivered" and shipped_at else None

        cur.execute("""
            INSERT INTO orders
                (order_no, user_id, seller_id, status, payment_status, payment_method,
                 subtotal, shipping_fee, discount_amount, total_amount, currency,
                 shipping_address, shipped_at, delivered_at, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            rand_order_no(), user_id, seller_id, status, pay_status, pay_method,
            subtotal, shipping, discount, total, "THB",
            json.dumps(addr), shipped_at, delivered_at, created
        ))
        order_id = cur.lastrowid
        order_ids.append((order_id, seller_id, pay_status, status, total, created))

        # Order items (1-5 items per order)
        item_count = random.randint(1, 5)
        chosen_skus = random.sample(sku_ids, min(item_count, len(sku_ids)))
        for sku_id in chosen_skus:
            qty = random.randint(1, 5)
            price = round(random.uniform(100, 5000), 2)
            cur.execute("""
                INSERT INTO order_items
                    (order_id, product_id, sku_id, quantity, unit_price, subtotal, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                order_id,
                random.choice(product_ids),
                sku_id, qty, price,
                round(qty * price, 2),
                status
            ))
    conn.commit()
    print(f"  Created {len(order_ids)} orders")

    # ── Payments ─────────────────────────────────────────────
    print("Seeding payments...")
    gateways = ["omise", "scb", "kbank", "2c2p", "stripe"]
    for order_id, seller_id, pay_status, status, total, created in order_ids:
        if pay_status == "paid":
            cur.execute("""
                INSERT INTO payments
                    (order_id, payment_ref, payment_method, gateway, amount, currency, status, paid_at, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                order_id,
                "PAY" + "".join(random.choices(string.ascii_uppercase + string.digits, k=16)),
                random.choice(PAYMENT_METHODS),
                random.choice(gateways),
                total, "THB", "success",
                created + timedelta(minutes=random.randint(1, 30)),
                created
            ))
    conn.commit()

    # ── Shipments ────────────────────────────────────────────
    print("Seeding shipments...")
    for order_id, seller_id, pay_status, status, total, created in order_ids:
        if status in ["shipped", "delivered"]:
            shipped = created + timedelta(days=random.randint(1, 3))
            delivered = (shipped + timedelta(days=random.randint(1, 7))) if status == "delivered" else None
            cur.execute("""
                INSERT INTO shipments
                    (order_id, tracking_no, carrier, status, weight_kg, shipping_fee,
                     estimated_date, actual_date, shipped_at, delivered_at, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                order_id,
                "TH" + "".join(random.choices(string.digits, k=13)),
                random.choice(CARRIERS),
                "delivered" if status == "delivered" else "in_transit",
                round(random.uniform(0.1, 20.0), 3),
                round(random.uniform(30, 200), 2),
                (shipped + timedelta(days=5)).date(),
                delivered.date() if delivered else None,
                shipped, delivered, created
            ))
    conn.commit()

    # ── Reviews ──────────────────────────────────────────────
    print("Seeding reviews...")
    delivered_orders = [(oid, sid, ps, s, t, c) for oid, sid, ps, s, t, c in order_ids if s == "delivered"]
    for order_id, _, _, _, _, created in random.sample(delivered_orders, min(800, len(delivered_orders))):
        product_id = random.choice(product_ids)
        user_id = random.choice(user_ids)
        rating = random.choices([1, 2, 3, 4, 5], weights=[2, 3, 10, 25, 60])[0]
        cur.execute("""
            INSERT INTO reviews (order_id, product_id, user_id, rating, content, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            order_id, product_id, user_id, rating,
            fake.paragraph(nb_sentences=random.randint(1, 4)),
            "published",
            created + timedelta(days=random.randint(1, 14))
        ))
    conn.commit()

    # ── User Events (Clickstream) ─────────────────────────────
    print("Seeding 10000 user events...")
    event_types = ["view", "click", "add_to_cart", "search", "purchase", "wishlist"]
    event_weights = [40, 20, 15, 15, 5, 5]
    for _ in range(10000):
        uid = random.choice(user_ids) if random.random() > 0.2 else None
        event_type = random.choices(event_types, weights=event_weights)[0]
        cur.execute("""
            INSERT INTO user_events
                (user_id, session_id, event_type, entity_type, entity_id,
                 device_type, platform, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            uid,
            "sess_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=16)),
            event_type, "product",
            random.choice(product_ids) if product_ids else None,
            random.choice(DEVICE_TYPES),
            random.choice(PLATFORMS),
            rand_date(90, 0)
        ))
    conn.commit()

    # ── Vouchers ─────────────────────────────────────────────
    print("Seeding vouchers...")
    voucher_codes = ["SAVE10", "NEWUSER50", "FLASH20", "VIP100", "FREE_SHIP", "SPECIAL15", "MEGA30"]
    for code in voucher_codes:
        vtype = "percentage" if code not in ["VIP100", "FREE_SHIP"] else ("fixed" if code == "VIP100" else "free_shipping")
        value = random.uniform(5, 30) if vtype == "percentage" else random.uniform(50, 200)
        cur.execute("""
            INSERT IGNORE INTO vouchers
                (code, name, type, value, min_order, usage_limit, start_date, end_date, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            code, f"Voucher {code}", vtype, round(value, 2),
            random.uniform(200, 1000),
            random.randint(100, 10000),
            datetime.now() - timedelta(days=30),
            datetime.now() + timedelta(days=60),
            1
        ))
    conn.commit()

    cur.close()
    conn.close()
    print("\n✅ Seed complete!")
    print(f"  Users: 500 | Sellers: 50 | Products: 200 | SKUs: ~{len(sku_ids)}")
    print(f"  Orders: 2000 | Events: 10000 | Reviews: ~800")


if __name__ == "__main__":
    seed_all()
