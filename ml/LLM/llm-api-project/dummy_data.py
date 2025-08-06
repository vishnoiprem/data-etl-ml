import random
from faker import Faker

fake = Faker()

def generate_dummy_users(count=10):
    return {
        f"user_{i}": {
            "credits": random.randint(10, 100),
            "name": fake.name(),
            "email": fake.email()
        } for i in range(count)
    }

if __name__ == "__main__":
    users = generate_dummy_users()
    print(users)