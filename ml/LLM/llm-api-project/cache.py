# cache.py
from redis import Redis
import hashlib

r = Redis(host='localhost', port=6379, decode_responses=True)

def get_cache(prompt: str):
    cache_key = f"cache:{hashlib.md5(prompt.encode()).hexdigest()}"
    return r.get(cache_key)

def set_cache(prompt: str, response: str, ttl: int = 3600):
    cache_key = f"cache:{hashlib.md5(prompt.encode()).hexdigest()}"
    r.setex(cache_key, ttl, response)