"""
AI Research Assistant - FastAPI entry point
============================================
An agentic research service that produces cited reports.

Run:  uvicorn app:app --reload

Environment:
  OPENAI_API_KEY    required
  TAVILY_API_KEY    required
  DATABASE_URL      default: sqlite:///./app.db
  JWT_SECRET        default: dev-secret-change-in-prod
"""

import os
import time
import uuid
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, AsyncGenerator

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from agent import ResearchAgent

# =============================================================================
# CONFIG
# =============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable is required")
if not TAVILY_API_KEY:
    raise RuntimeError("TAVILY_API_KEY environment variable is required")

# =============================================================================
# LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='{"ts": "%(asctime)s", "level": "%(levelname)s", "msg": "%(message)s"}',
)
logger = logging.getLogger("research-assistant")

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


class ResearchJob(Base):
    __tablename__ = "research_jobs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    question = Column(Text, nullable=False)
    status = Column(String, default="queued")  # queued, running, completed, failed
    plan = Column(Text, nullable=True)         # JSON: list of sub-questions
    sources = Column(Text, nullable=True)      # JSON: list of {url, title, text, score}
    report = Column(Text, nullable=True)       # final markdown
    cost_usd = Column(Integer, default=0)      # microdollars
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
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
    }
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
    token = authorization[7:]
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(401, "Invalid or expired token")
    return user_id

# =============================================================================
# AGENT
# =============================================================================

agent = ResearchAgent(openai_api_key=OPENAI_API_KEY, tavily_api_key=TAVILY_API_KEY)

# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(title="AI Research Assistant", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# =============================================================================
# REQUEST / RESPONSE MODELS
# =============================================================================

class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ResearchRequest(BaseModel):
    question: str
    max_sources: int = 30  # cap on scraped sources


class ReportSummary(BaseModel):
    id: str
    question: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    cost_usd: float


class ReportDetail(BaseModel):
    id: str
    question: str
    plan: list[str]
    sources: list[dict]
    report: str
    cost_usd: float
    latency_ms: int

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
        existing = db.query(User).filter(User.email == req.email).first()
        if existing:
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


@app.post("/research")
async def research(req: ResearchRequest, user_id: str = Depends(get_current_user)):
    """Start a research job. Returns the job_id immediately; poll or stream for status."""
    start = time.time()
    db = SessionLocal()
    try:
        job_id = str(uuid.uuid4())
        job = ResearchJob(
            id=job_id,
            user_id=user_id,
            question=req.question,
            status="running",
        )
        db.add(job)
        db.commit()

        # Run the agent synchronously for the MVP
        # In production, push to a queue (Celery / RQ)
        try:
            result = agent.run(question=req.question, max_sources=req.max_sources)
            job.plan = json.dumps(result.get("plan", []))
            job.sources = json.dumps(result.get("sources", []))
            job.report = result.get("report", "")
            job.cost_usd = int(result.get("cost_usd", 0) * 1_000_000)
            job.latency_ms = round((time.time() - start) * 1000)
            job.status = "completed"
            job.completed_at = datetime.utcnow()
        except Exception as e:
            logger.error(f"research job {job_id} failed: {e}")
            job.status = "failed"
            job.error = str(e)
        db.commit()

        logger.info(f"research user={user_id} job={job_id} status={job.status} ms={job.latency_ms}")

        return {
            "job_id": job_id,
            "status": job.status,
            "latency_ms": job.latency_ms,
            "cost_usd": job.cost_usd / 1_000_000,
        }
    finally:
        db.close()


@app.get("/reports")
async def list_reports(user_id: str = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = (
            db.query(ResearchJob)
            .filter(ResearchJob.user_id == user_id)
            .order_by(ResearchJob.created_at.desc())
            .limit(50)
            .all()
        )
        return [
            {
                "id": r.id,
                "question": r.question,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "cost_usd": (r.cost_usd or 0) / 1_000_000,
            }
            for r in rows
        ]
    finally:
        db.close()


@app.get("/report/{report_id}", response_model=ReportDetail)
async def get_report(report_id: str, user_id: str = Depends(get_current_user)):
    db = SessionLocal()
    try:
        job = db.query(ResearchJob).filter(ResearchJob.id == report_id).first()
        if not job or job.user_id != user_id:
            raise HTTPException(404, "Report not found")
        if job.status != "completed":
            raise HTTPException(409, f"Report is {job.status}")

        return ReportDetail(
            id=job.id,
            question=job.question,
            plan=json.loads(job.plan) if job.plan else [],
            sources=json.loads(job.sources) if job.sources else [],
            report=job.report or "",
            cost_usd=(job.cost_usd or 0) / 1_000_000,
            latency_ms=job.latency_ms or 0,
        )
    finally:
        db.close()


@app.get("/research/{job_id}/stream")
async def stream_research(job_id: str, user_id: str = Depends(get_current_user)):
    """SSE stream of agent progress for a running job. Replays events from the DB."""
    async def event_gen() -> AsyncGenerator[str, None]:
        db = SessionLocal()
        try:
            job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
            if not job or job.user_id != user_id:
                yield f"event: error\ndata: {json.dumps({'message': 'not found'})}\n\n"
                return
            if job.status == "completed":
                yield f"event: report_ready\ndata: {json.dumps({'report_id': job.id})}\n\n"
                return
            if job.status == "failed":
                yield f"event: failed\ndata: {json.dumps({'error': job.error})}\n\n"
                return
            # For a long-running job, this would subscribe to a Redis pub/sub channel
            # In the MVP, jobs run synchronously so we just yield a heartbeat
            for _ in range(30):
                db.refresh(job)
                if job.status in ("completed", "failed"):
                    yield f"event: {job.status}\ndata: {json.dumps({'report_id': job.id if job.status == 'completed' else None})}\n\n"
                    return
                yield f"event: heartbeat\ndata: {json.dumps({'status': job.status})}\n\n"
                await asyncio.sleep(1)
        finally:
            db.close()

    return StreamingResponse(event_gen(), media_type="text/event-stream")
