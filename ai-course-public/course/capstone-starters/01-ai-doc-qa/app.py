"""
AI Document Q&A - FastAPI entry point
======================================
A "ChatGPT for your PDFs" service.

Run:  uvicorn app:app --reload

Environment:
  OPENAI_API_KEY    required
  PINECONE_API_KEY  required
  DATABASE_URL      default: sqlite:///./app.db
  JWT_SECRET        default: dev-secret-change-in-prod
"""

import os
import time
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from jose import jwt, JWTError
from passlib.context import CryptContext
import PyPDF2
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from rag import RAGPipeline

# =============================================================================
# CONFIG
# =============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable is required")
if not PINECONE_API_KEY:
    raise RuntimeError("PINECONE_API_KEY environment variable is required")

# =============================================================================
# LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='{"ts": "%(asctime)s", "level": "%(levelname)s", "msg": "%(message)s"}',
)
logger = logging.getLogger("doc-qa")

# =============================================================================
# DATABASE (SQLAlchemy)
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


class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    num_chunks = Column(Integer, default=0)
    status = Column(String, default="processing")  # processing, indexed, failed
    created_at = Column(DateTime, default=datetime.utcnow)


class Query(Base):
    __tablename__ = "queries"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    document_id = Column(String, nullable=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    citations = Column(Text, nullable=True)  # JSON string
    latency_ms = Column(Integer, default=0)
    cost_usd = Column(Integer, default=0)  # stored as microdollars
    created_at = Column(DateTime, default=datetime.utcnow)


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
    """Extract user_id from Authorization header. Replace with Clerk in production."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid Authorization header")
    token = authorization[7:]
    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(401, "Invalid or expired token")
    return user_id


# =============================================================================
# RAG PIPELINE
# =============================================================================

rag = RAGPipeline(openai_api_key=OPENAI_API_KEY, pinecone_api_key=PINECONE_API_KEY)

# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(title="AI Document Q&A", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend
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


class ChatRequest(BaseModel):
    question: str
    document_id: Optional[str] = None  # if None, search across all user's docs


class Citation(BaseModel):
    chunk_id: str
    document_title: str
    page: int
    score: float
    text: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    latency_ms: int


# =============================================================================
# ROUTES
# =============================================================================

@app.get("/health")
async def health():
    return {"status": "ok", "ts": datetime.utcnow().isoformat()}


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the minimal HTML frontend."""
    with open("frontend/index.html") as f:
        return f.read()


@app.post("/auth/signup")
async def signup(req: SignupRequest):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == req.email).first()
        if existing:
            raise HTTPException(400, "Email already registered")
        user = User(
            email=req.email,
            password_hash=pwd_context.hash(req.password),
        )
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


@app.post("/upload")
async def upload(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
):
    """Upload a PDF. Extracts text, chunks, embeds, stores in Pinecone."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    start = time.time()
    db = SessionLocal()
    try:
        # Read PDF
        contents = await file.read()
        if len(contents) > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(413, "File too large (max 50MB)")

        pdf_reader = PyPDF2.PdfReader(__import__("io").BytesIO(contents))
        pages = [page.extract_text() for page in pdf_reader.pages]

        # Index in Pinecone
        doc_id, num_chunks = rag.index_document(
            user_id=user_id,
            document_id=str(uuid.uuid4()),
            title=file.filename,
            pages=pages,
        )

        # Save to DB
        doc = Document(
            id=doc_id,
            user_id=user_id,
            title=file.filename,
            num_chunks=num_chunks,
            status="indexed",
        )
        db.add(doc)
        db.commit()

        elapsed = round((time.time() - start) * 1000)
        logger.info(f"upload user={user_id} doc={doc_id} chunks={num_chunks} ms={elapsed}")

        return {"document_id": doc_id, "title": file.filename, "num_chunks": num_chunks}
    except Exception as e:
        logger.error(f"upload failed: {e}")
        raise HTTPException(500, str(e))
    finally:
        db.close()


@app.get("/documents")
async def list_documents(user_id: str = Depends(get_current_user)):
    db = SessionLocal()
    try:
        docs = db.query(Document).filter(Document.user_id == user_id).all()
        return [
            {
                "id": d.id,
                "title": d.title,
                "num_chunks": d.num_chunks,
                "status": d.status,
                "created_at": d.created_at.isoformat(),
            }
            for d in docs
        ]
    finally:
        db.close()


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, user_id: str = Depends(get_current_user)):
    """Ask a question. Returns answer with citations."""
    start = time.time()
    db = SessionLocal()
    try:
        result = rag.query(
            user_id=user_id,
            question=req.question,
            document_id=req.document_id,
        )
        elapsed_ms = round((time.time() - start) * 1000)

        # Save to history
        query_record = Query(
            user_id=user_id,
            document_id=req.document_id,
            question=req.question,
            answer=result["answer"],
            citations=str(result["citations"]),
            latency_ms=elapsed_ms,
            cost_usd=int(result.get("cost_usd", 0) * 1_000_000),
        )
        db.add(query_record)
        db.commit()

        logger.info(
            f"chat user={user_id} q_len={len(req.question)} "
            f"citations={len(result['citations'])} ms={elapsed_ms}"
        )

        return ChatResponse(
            answer=result["answer"],
            citations=[Citation(**c) for c in result["citations"]],
            latency_ms=elapsed_ms,
        )
    except Exception as e:
        logger.error(f"chat failed: {e}")
        raise HTTPException(500, str(e))
    finally:
        db.close()
