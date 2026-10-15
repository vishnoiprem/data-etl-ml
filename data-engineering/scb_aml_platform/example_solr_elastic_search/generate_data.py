

from faker import Faker
import random
import json

fake = Faker()

CATEGORIES = ["Electronics", "Clothing", "Home & Kitchen",
              "Sports", "Books", "Toys", "Automotive"]

BRANDS = ["TechCorp", "StyleMax", "HomeBase",
          "ActiveGear", "ReadMore", "FunZone"]

def generate_products(n=10000):
    products = []
    for i in range(n):
        product = {
            "id":          str(i + 1),
            "name":        fake.catch_phrase(),
            "description": fake.paragraph(nb_sentences=4),
            "category":    random.choice(CATEGORIES),
            "brand":       random.choice(BRANDS),
            "price":       round(random.uniform(5.0, 2000.0), 2),
            "rating":      round(random.uniform(1.0, 5.0), 1),
            "in_stock":    random.choice([True, False]),
            "reviews":     random.randint(0, 15000),
        }
        products.append(product)
    return products

if __name__ == "__main__":
    data = generate_products(10000)
    with open("products.json", "w") as f:
        json.dump(data, f)
    print(f"Generated {len(data)} products → products.json")
