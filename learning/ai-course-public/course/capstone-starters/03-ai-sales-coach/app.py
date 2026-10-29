"""
AI Sales Coach - FastAPI entry point
=====================================
Upload sales calls, get AI coaching feedback.

Run:  uvicorn app:app --reload

Environment:
  OPENAI_API_KEY    required
  DATABASE_URL      default: sqlite:///./app.db
  JWT_SECRET        default: dev-secret-change-in-prod
  AUDIO_DIR         default: ./audio (where uploaded audio is stored in dev)
"""

import os
import uuid
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Float
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from audio_processor import transcribe_audio
from analyzer import analyze_call
from feedback_engine import generate_feedback

# =============================================================================
# CONFIG
# =============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-prod")
AUDIO_DIR = os.getenv("AUDIO_DIR", "./audio")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable is required")

os.makedirs(AUDIO_DIR, exist_ok=True)

# =============================================================================
# LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='{"ts": "%(asctime)s", "level": "%(levelname)s", "msg": "%(message)s"}',
)
logger = logging.getLogger("sales-coach")

# =============================================================================
# DATABASE
# =============================================================================

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Call(Base):
    __tablename__ = "calls"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    audio_path = Column(String, nullable=False)
    duration_s = Column(Float, default=0.0)
    status = Column(String, default="uploaded")  # uploaded, transcribing, transcribed, analyzing, analyzed, failed
    transcript = Column(Text, nullable=True)     # JSON
    analysis = Column(Text, nullable=True)       # JSON
    feedback = Column(Text, nullable=True)       # JSON
    cost_usd = Column(Integer, default=0)        # microdollars
    latency_ms = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


Base.metadata.create_all(bind=engine)

# =============================================================================
# AUTH
# =============================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


def get_current_user(authorization: str = None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid Authorization header")
    user_id = verify_token(authorization[7:])
    if not user_id:
        raise HTTPException(401, "Invalid or expired token")
    return user_id

# =============================================================================
# APP
# =============================================================================

app = FastAPI(title="AI Sales Coach", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="frontend"), name="static")


# =============================================================================
# MODELS
# =============================================================================

class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# =============================================================================
# ROUTES
# =============================================================================

@app.get("/health")
async def health():
    return {"status": "ok", "ts": datetime.utcnow().isoformat()}


@app.get("/", response_class=HTMLResponse)
async def root():
    with open("frontend/index.html") as f:
        return f.read()


@app.post("/auth/signup")
async def signup(req: SignupRequest):
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == req.email).first():
            raise HTTPException(400, "Email already registered")
        user = User(email=req.email, password_hash=pwd_context.hash(req.password))
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"token": create_token(user.id), "user_id": user.id}
    finally:
        db.close()


@app.post("/auth/login")
async def login(req: LoginRequest):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == req.email).first()
        if not user or not pwd_context.verify(req.password, user.password_hash):
            raise HTTPException(401, "Invalid credentials")
        return {"token": create_token(user.id), "user_id": user.id}
    finally:
        db.close()


@app.post("/calls/upload")
async def upload_call(
    file: UploadFile = File(...),
    title: str = "Untitled call",
    user_id: str = Depends(get_current_user),
):
    """Upload an audio file. Returns call_id; transcribe + analyze in the background."""
    allowed = {".mp3", ".wav", ".m4a", ".mp4", ".mpeg", ".mpga", ".webm"}
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported audio format: {ext}")

    contents = await file.read()
    max_bytes = 200 * 1024 * 1024  # 200MB
    if len(contents) > max_bytes:
        raise HTTPException(413, "File too large (max 200MB)")

    call_id = str(uuid.uuid4())
    audio_path = os.path.join(AUDIO_DIR, f"{call_id}{ext}")
    with open(audio_path, "wb") as f:
        f.write(contents)

    db = SessionLocal()
    try:
        call = Call(
            id=call_id,
            user_id=user_id,
            title=title,
            audio_path=audio_path,
            status="uploaded",
        )
        db.add(call)
        db.commit()
        logger.info(f"call uploaded user={user_id} call={call_id} size={len(contents)}")
        return {"call_id": call_id, "status": "uploaded", "bytes": len(contents)}
    finally:
        db.close()


@app.post("/calls/{call_id}/analyze")
async def analyze(call_id: str, user_id: str = Depends(get_current_user)):
    """Run transcription + analysis + feedback on an uploaded call."""
    start = time.time()
    db = SessionLocal()
    try:
        call = db.query(Call).filter(Call.id == call_id).first()
        if not call or call.user_id != user_id:
            raise HTTPException(404, "Call not found")
        if not os.path.exists(call.audio_path):
            raise HTTPException(410, "Audio file no longer available")

        total_cost = 0.0

        # Step 1: transcribe
        call.status = "transcribing"
        db.commit()
        try:
            transcript, dur, cost = transcribe_audio(call.audio_path, OPENAI_API_KEY)
            call.transcript = json.dumps(transcript)
            call.duration_s = dur
            total_cost += cost
        except Exception as e:
            call.status = "failed"
            call.error = f"transcribe: {e}"
            db.commit()
            raise HTTPException(500, f"Transcription failed: {e}")
        call.status = "transcribed"
        db.commit()

        # Step 2: analyze (function-calling extraction)
        try:
            analysis, cost = analyze_call(transcript, OPENAI_API_KEY)
            call.analysis = json.dumps(analysis)
            total_cost += cost
        except Exception as e:
            call.status = "failed"
            call.error = f"analyze: {e}"
            db.commit()
            raise HTTPException(500, f"Analysis failed: {e}")
        call.status = "analyzed"
        db.commit()

        # Step 3: feedback (narrative)
        try:
            feedback, cost = generate_feedback(analysis, transcript, OPENAI_API_KEY)
            call.feedback = json.dumps(feedback)
            total_cost += cost
        except Exception as e:
            logger.warning(f"feedback failed for {call_id}: {e}")
            call.feedback = json.dumps({"error": str(e)})

        call.cost_usd = int(total_cost * 1_000_000)
        call.latency_ms = round((time.time() - start) * 1000)
        call.completed_at = datetime.utcnow()
        call.status = "complete"
        db.commit()

        logger.info(
            f"call analyzed user={user_id} call={call_id} "
            f"cost=${total_cost:.3f} ms={call.latency_ms}"
        )
        return {
            "call_id": call_id,
            "status": call.status,
            "latency_ms": call.latency_ms,
            "cost_usd": total_cost,
        }
    finally:
        db.close()


@app.get("/calls")
async def list_calls(user_id: str = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = (
            db.query(Call)
            .filter(Call.user_id == user_id)
            .order_by(Call.created_at.desc())
            .limit(50)
            .all()
        )
        return [
            {
                "id": c.id,
                "title": c.title,
                "duration_s": c.duration_s,
                "status": c.status,
                "created_at": c.created_at.isoformat(),
                "completed_at": c.completed_at.isoformat() if c.completed_at else None,
                "cost_usd": (c.cost_usd or 0) / 1_000_000,
            }
            for c in rows
        ]
    finally:
        db.close()


@app.get("/calls/{call_id}")
async def get_call(call_id: str, user_id: str = Depends(get_current_user)):
    db = SessionLocal()
    try:
        c = db.query(Call).filter(Call.id == call_id).first()
        if not c or c.user_id != user_id:
            raise HTTPException(404, "Call not found")
        return {
            "id": c.id,
            "title": c.title,
            "duration_s": c.duration_s,
            "status": c.status,
            "transcript": json.loads(c.transcript) if c.transcript else None,
            "analysis": json.loads(c.analysis) if c.analysis else None,
            "feedback": json.loads(c.feedback) if c.feedback else None,
            "cost_usd": (c.cost_usd or 0) / 1_000_000,
            "latency_ms": c.latency_ms,
        }
    finally:
        db.close()
