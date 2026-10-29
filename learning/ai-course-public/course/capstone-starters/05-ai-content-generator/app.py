"""
AI Content Generator - FastAPI entry point
==========================================
Generate SEO-optimized blog articles from a topic + keyword.

Run:  uvicorn app:app --reload

Environment:
  OPENAI_API_KEY    required
  TAVILY_API_KEY    required
  DATABASE_URL      default: sqlite:///./app.db
  JWT_SECRET        default: dev-secret-change-in-prod
"""

import os
import uuid
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from researcher import research_serp
from writer import write_article
from optimizer import score_seo, generate_meta

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
logger = logging.getLogger("content-generator")

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


class Article(Base):
    __tablename__ = "articles"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    topic = Column(String, nullable=False)
    keyword = Column(String, nullable=False)
    tone = Column(String, default="informative")
    target_words = Column(Integer, default=1500)
    outline = Column(Text, nullable=True)         # JSON: list of section titles
    body = Column(Text, nullable=True)             # markdown
    research = Column(Text, nullable=True)         # JSON: SERP data
    seo_report = Column(Text, nullable=True)       # JSON
    meta_title = Column(String, nullable=True)
    meta_description = Column(Text, nullable=True)
    cost_usd = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)

# =============================================================================
# AUTH
# =============================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_token(user_id: str) -> str:
    return jwt.encode({"sub": user_id, "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Optional[str]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM]).get("sub")
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

app = FastAPI(title="AI Content Generator", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="frontend"), name="static")


class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=200)
    keyword: str = Field(..., min_length=2, max_length=100)
    target_words: int = Field(default=1500, ge=300, le=5000)
    tone: str = Field(default="informative", pattern=r"^(informative|witty|formal|casual|persuasive)$")


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


@app.post("/generate")
async def generate(req: GenerateRequest, user_id: str = Depends(get_current_user)):
    """Generate an SEO-optimized article. Runs research → outline → write → optimize."""
    start = time.time()
    total_cost = 0.0
    article_id = str(uuid.uuid4())
    db = SessionLocal()
    try:
        # Step 1: research
        try:
            research, cost = research_serp(req.keyword, tavily_api_key=TAVILY_API_KEY, openai_api_key=OPENAI_API_KEY)
            total_cost += cost
        except Exception as e:
            logger.error(f"research failed: {e}")
            raise HTTPException(500, f"Research failed: {e}")

        # Step 2: outline + write
        try:
            outline, body, cost = write_article(
                topic=req.topic,
                keyword=req.keyword,
                research=research,
                target_words=req.target_words,
                tone=req.tone,
                openai_api_key=OPENAI_API_KEY,
            )
            total_cost += cost
        except Exception as e:
            logger.error(f"write failed: {e}")
            raise HTTPException(500, f"Writing failed: {e}")

        # Step 3: SEO scoring
        seo_report = score_seo(body, req.keyword, target_words=req.target_words)

        # Step 4: meta
        meta_title, meta_desc, cost = generate_meta(
            topic=req.topic, keyword=req.keyword, body=body,
            openai_api_key=OPENAI_API_KEY,
        )
        total_cost += cost

        latency_ms = round((time.time() - start) * 1000)

        article = Article(
            id=article_id,
            user_id=user_id,
            topic=req.topic,
            keyword=req.keyword,
            tone=req.tone,
            target_words=req.target_words,
            outline=json.dumps(outline),
            body=body,
            research=json.dumps(research),
            seo_report=json.dumps(seo_report),
            meta_title=meta_title,
            meta_description=meta_desc,
            cost_usd=int(total_cost * 1_000_000),
            latency_ms=latency_ms,
        )
        db.add(article)
        db.commit()

        logger.info(
            f"article generated user={user_id} article={article_id} "
            f"words={len(body.split())} seo={seo_report['overall_score']} "
            f"cost=${total_cost:.4f} ms={latency_ms}"
        )
        return {
            "article_id": article_id,
            "topic": req.topic,
            "keyword": req.keyword,
            "outline": outline,
            "body": body,
            "seo_report": seo_report,
            "meta_title": meta_title,
            "meta_description": meta_desc,
            "cost_usd": total_cost,
            "latency_ms": latency_ms,
        }
    finally:
        db.close()


@app.get("/articles")
async def list_articles(user_id: str = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = (
            db.query(Article)
            .filter(Article.user_id == user_id)
            .order_by(Article.created_at.desc())
            .limit(50)
            .all()
        )
        return [
            {
                "id": a.id,
                "topic": a.topic,
                "keyword": a.keyword,
                "target_words": a.target_words,
                "created_at": a.created_at.isoformat(),
                "cost_usd": (a.cost_usd or 0) / 1_000_000,
                "latency_ms": a.latency_ms,
            }
            for a in rows
        ]
    finally:
        db.close()


@app.get("/articles/{article_id}")
async def get_article(article_id: str, user_id: str = Depends(get_current_user)):
    db = SessionLocal()
    try:
        a = db.query(Article).filter(Article.id == article_id).first()
        if not a or a.user_id != user_id:
            raise HTTPException(404, "Article not found")
        return {
            "id": a.id,
            "topic": a.topic,
            "keyword": a.keyword,
            "tone": a.tone,
            "target_words": a.target_words,
            "outline": json.loads(a.outline) if a.outline else [],
            "body": a.body,
            "research": json.loads(a.research) if a.research else {},
            "seo_report": json.loads(a.seo_report) if a.seo_report else {},
            "meta_title": a.meta_title,
            "meta_description": a.meta_description,
            "cost_usd": (a.cost_usd or 0) / 1_000_000,
            "latency_ms": a.latency_ms,
            "created_at": a.created_at.isoformat(),
        }
    finally:
        db.close()