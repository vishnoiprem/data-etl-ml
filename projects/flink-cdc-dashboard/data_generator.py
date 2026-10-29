import psycopg2
import random
import time
from faker import Faker

fake = Faker()


def generate_orders():
    conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="postgres"
    )

    print("🛒 Generating live orders...")
    while True:
        try:
            with conn.cursor() as cur:
                user_id = f"user_{random.randint(1, 10)}"
                amount = round(random.uniform(10, 500), 2)

                cur.execute(
                    "INSERT INTO orders (user_id, amount) VALUES (%s, %s)",
                    (user_id, amount)
                )
                conn.commit()
                print(f"Inserted: {user_id}, ${amount:.2f}")
        except Exception as e:
            print(f"Error: {e}")
            conn = psycopg2.connect(
                host="localhost",
                database="postgres",
                user="postgres",
                password="postgres"
            )

        time.sleep(random.uniform(0.1, 0.5))


if __name__ == "__main__":
    generate_orders()