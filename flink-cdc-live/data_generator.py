# data_generator.py
import psycopg2
import random
import time
from faker import Faker

fake = Faker()


def generate_order():
    conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="postgres"
    )
    cur = conn.cursor()

    while True:
        user_id = f"user_{random.randint(1, 10)}"
        amount = round(random.uniform(10, 500), 2)

        cur.execute(
            "INSERT INTO orders (user_id, amount) VALUES (%s, %s)",
            (user_id, amount)
        )
        conn.commit()
        print(f"Inserted order: {user_id}, ${amount}")
        time.sleep(random.uniform(0.1, 1.0))  # Simulate real-time


if __name__ == "__main__":
    generate_order()