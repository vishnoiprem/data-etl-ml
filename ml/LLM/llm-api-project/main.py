# main.py
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
import ollama
from auth import create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from rate_limiter import rate_limit
from cache import get_cache, set_cache
from dummy_data import DUMMY_USERS, DUMMY_API_KEYS, DUMMY_PROMPTS
from pydantic import BaseModel
from datetime import timedelta
import threading
import time

app = FastAPI()


# Keep Ollama model warm
def keep_warm():
    while True:
        ollama.generate(model="mistral", prompt="ping")
        time.sleep(300)  # Every 5 minutes


threading.Thread(target=keep_warm, daemon=True).start()


class PromptRequest(BaseModel):
    prompt: str


@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = DUMMY_USERS.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/chat")
@rate_limit(max_requests=5, window_seconds=60)
async def chat(request: Request, prompt_request: PromptRequest, user: dict = Depends(get_current_user)):
    prompt = prompt_request.prompt
    if user["credits"] <= 0:
        raise HTTPException(403, "No credits left")

    # Check cache
    cached_response = get_cache(prompt)
    if cached_response:
        return {"response": cached_response, "source": "cache"}

    # Call Ollama
    try:
        response = ollama.chat(model="mistral", messages=[{"role": "user", "content": prompt}])
        response_text = response['message']['content']

        # Update credits and cache
        user["credits"] -= 1
        set_cache(prompt, response_text)
        return {"response": response_text, "source": "ollama"}
    except Exception as e:
        raise HTTPException(500, f"LLM error: {str(e)}")


@app.post("/api_key_chat")
async def api_key_chat(request: Request, prompt_request: PromptRequest, api_key: str):
    if api_key not in DUMMY_API_KEYS or DUMMY_API_KEYS[api_key]["credits"] <= 0:
        raise HTTPException(403, "Invalid or exhausted API key")

    prompt = prompt_request.prompt
    cached_response = get_cache(prompt)
    if cached_response:
        return {"response": cached_response, "source": "cache"}

    try:
        response = ollama.chat(model="mistral", messages=[{"role": "user", "content": prompt}])
        response_text = response['message']['content']

        DUMMY_API_KEYS[api_key]["credits"] -= 1
        set_cache(prompt, response_text)
        return {"response": response_text, "source": "ollama"}
    except Exception as e:
        raise HTTPException(500, f"LLM error: {str(e)}")