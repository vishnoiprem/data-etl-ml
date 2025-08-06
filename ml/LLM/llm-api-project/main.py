# main.py
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import Dict, List
import ollama
import random
from datetime import datetime, timedelta
import time
from collections import defaultdict
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="LLM API with Dummy Data",
    description="Complete implementation with both dummy and real LLM modes",
    version="1.0.0"
)

# Configuration
API_KEYS = os.getenv("API_KEYS", "demo_key:100,test_key:50").split(",")
API_KEYS = {k.split(":")[0]: int(k.split(":")[1]) for k in API_KEYS}
DUMMY_MODE = os.getenv("DUMMY_MODE", "False").lower() == "true"
MODEL_NAME = "mistral"

# Dummy data setup
dummy_responses = [
    "According to dummy data, the answer is 42.",
    "Dummy response: This would be the LLM's answer.",
    "Simulated response for: {prompt}",
    "In a real system, this would return proper results.",
    "This is a placeholder response from the dummy dataset."
]

# Rate limiting storage
request_logs = defaultdict(list)
api_key_header = APIKeyHeader(name="X-API-Key")


# Models
class ChatRequest(BaseModel):
    prompt: str
    max_length: int = 100


class UserCredits(BaseModel):
    api_key: str
    remaining_credits: int


# Helper functions
def get_dummy_response(prompt: str) -> str:
    """Generate realistic dummy responses"""
    base = random.choice(dummy_responses)
    return base.replace("{prompt}", prompt[:50])


def rate_limit(key: str, limit: int = 10, window: int = 60) -> bool:
    """Simple rate limiting"""
    now = time.time()
    window_start = now - window

    # Clear old requests
    request_logs[key] = [t for t in request_logs[key] if t > window_start]

    if len(request_logs[key]) >= limit:
        return False

    request_logs[key].append(now)
    return True


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize Ollama model if not in dummy mode"""
    if not DUMMY_MODE:
        try:
            ollama.pull(MODEL_NAME)
            logging.info(f"Successfully loaded {MODEL_NAME} model")
        except Exception as e:
            logging.error(f"Failed to load Ollama model: {e}")
            global DUMMY_MODE
            DUMMY_MODE = True


# Endpoints
@app.post("/chat", response_model=Dict[str, str])
async def chat_endpoint(
        request: ChatRequest,
        api_key: str = Depends(api_key_header)
):
    """
    Main chat endpoint with:
    - API key authentication
    - Rate limiting
    - Credit tracking
    - Dummy/real mode switching
    """
    # Authentication
    if api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Rate limiting
    if not rate_limit(api_key):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded (10 requests/minute)"
        )

    # Credit check
    if API_KEYS[api_key] <= 0:
        raise HTTPException(status_code=403, detail="No credits remaining")

    API_KEYS[api_key] -= 1

    # Generate response
    if DUMMY_MODE:
        response = get_dummy_response(request.prompt)
    else:
        try:
            result = ollama.chat(
                model=MODEL_NAME,
                messages=[{'role': 'user', 'content': request.prompt}]
            )
            response = result['message']['content']
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"LLM service unavailable: {str(e)}"
            )

    return {
        "response": response,
        "remaining_credits": API_KEYS[api_key],
        "mode": "dummy" if DUMMY_MODE else "real"
    }


@app.get("/credits/{api_key}", response_model=UserCredits)
async def check_credits(api_key: str):
    """Check remaining credits"""
    if api_key not in API_KEYS:
        raise HTTPException(status_code=404, detail="API key not found")
    return {
        "api_key": api_key,
        "remaining_credits": API_KEYS[api_key]
    }


# Health check
@app.get("/health")
async def health_check():
    """Service health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "dummy_mode": DUMMY_MODE,
        "model_loaded": not DUMMY_MODE
    }