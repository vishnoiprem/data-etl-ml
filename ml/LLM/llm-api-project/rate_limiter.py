# rate_limiter.py
from fastapi import HTTPException
from collections import defaultdict
import time

request_counts = defaultdict(list)

def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            client_ip = kwargs.get('request').client.host
            now = time.time()
            request_counts[client_ip] = [
                req_time for req_time in request_counts[client_ip]
                if now - req_time < window_seconds
            ]
            if len(request_counts[client_ip]) >= max_requests:
                raise HTTPException(429, "Rate limit exceeded")
            request_counts[client_ip].append(now)
            return await func(*args, **kwargs)
        return wrapper
    return decorator