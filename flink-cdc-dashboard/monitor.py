# monitor.py
import redis
import json
import time

r = redis.Redis(host='localhost', port=6379)

def display_dashboard():
    while True:
        print("\n=== LIVE USER ANALYTICS ===")
        for key in r.scan_iter("user_analytics:*"):
            data = json.loads(r.get(key))
            print(f"User {key.decode().split(':')[1]}:")
            print(f"  Orders: {data['total_orders']}")
            print(f"  Revenue: ${data['total_revenue']:.2f}")
        time.sleep(2)

if __name__ == "__main__":
    display_dashboard()