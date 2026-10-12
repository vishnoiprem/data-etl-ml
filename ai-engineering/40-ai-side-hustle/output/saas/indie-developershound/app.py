from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Indie DevelopersHound")

@app.get('/')
def root():
    return {'name': 'Indie DevelopersHound', 'tagline': "AI copilot that finds indie developers bugs before they ship."}

class Signup(BaseModel):
    email: str

@app.post('/signup')
def signup(s: Signup):
    # TODO: charge via Stripe, persist to DB
    return {'ok': True, 'email': s.email}
