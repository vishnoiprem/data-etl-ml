"""
AI Data Analyst - FastAPI entry point
======================================
Upload CSVs. Ask questions in plain English. Get answers + charts.

Run:  uvicorn app:app --reload

Environment:
  OPENAI_API_KEY    required
  DATABASE_URL      default: sqlite:///./app.db
  JWT_SECRET        default: dev-secret-change-in-prod
  DATA_DIR          default: ./data (where CSVs live in dev)
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
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from dataframe_ops import infer_schema, generate_pandas_code
from code_executor import run_pandas_code
from visualizer import pick_and_render_chart

# =============================================================================
# CONFIG
# =============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-prod")
DATA_DIR = os.getenv("DATA_DIR", "./data")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable is required")

os.makedirs(DATA_DIR, exist_ok=True)

# =============================================================================
# LOGGING
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='{"ts": "%(asctime)s", "level": "%(levelname)s", "msg": "%(message)s"}',
)
logger = logging.getLogger("data-analyst")

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


class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False)
    n_rows = Column(Integer, default=0)
    n_cols = Column(Integer, default=0)
    schema = Column(Text, nullable=True)         # JSON
    cost_usd = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    dataset_id = Column(String, nullable=False, index=True)
    question = Column(Text, nullable=False)
    code = Column(Text, nullable=False)
    insight = Column(Text, nullable=True)
    chart = Column(Text, nullable=True)         # JSON for Plotly
    result_rows = Column(Integer, default=0)
    cost_usd = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    error = Column(Text, nullable=True)
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

app = FastAPI(title="AI Data Analyst", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="frontend"), name="static")


class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AnalyzeRequest(BaseModel):
    dataset_id: str
    question: str


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


@app.post("/datasets/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
):
    """Upload a CSV. Returns dataset_id + inferred schema."""
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(400, "Only CSV files are supported")

    contents = await file.read()
    max_bytes = 100 * 1024 * 1024  # 100MB
    if len(contents) > max_bytes:
        raise HTTPException(413, "File too large (max 100MB)")

    dataset_id = str(uuid.uuid4())
    path = os.path.join(DATA_DIR, f"{dataset_id}.csv")
    with open(path, "wb") as f:
        f.write(contents)

    try:
        schema, n_rows, n_cols = infer_schema(path)
    except Exception as e:
        os.remove(path)
        raise HTTPException(400, f"Could not parse CSV: {e}")

    db = SessionLocal()
    try:
        ds = Dataset(
            id=dataset_id,
            user_id=user_id,
            name=file.filename,
            path=path,
            n_rows=n_rows,
            n_cols=n_cols,
            schema=json.dumps(schema),
        )
        db.add(ds)
        db.commit()
        logger.info(f"dataset uploaded user={user_id} ds={dataset_id} rows={n_rows} cols={n_cols}")
        return {
            "dataset_id": dataset_id,
            "name": file.filename,
            "n_rows": n_rows,
            "n_cols": n_cols,
            "schema": schema,
        }
    finally:
        db.close()


@app.get("/datasets")
async def list_datasets(user_id: str = Depends(get_current_user)):
    db = SessionLocal()
    try:
        rows = (
            db.query(Dataset)
            .filter(Dataset.user_id == user_id)
            .order_by(Dataset.created_at.desc())
            .limit(50)
            .all()
        )
        return [
            {
                "id": d.id,
                "name": d.name,
                "n_rows": d.n_rows,
                "n_cols": d.n_cols,
                "created_at": d.created_at.isoformat(),
            }
            for d in rows
        ]
    finally:
        db.close()


@app.get("/datasets/{dataset_id}/schema")
async def get_schema(dataset_id: str, user_id: str = Depends(get_current_user)):
    db = SessionLocal()
    try:
        ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not ds or ds.user_id != user_id:
            raise HTTPException(404, "Dataset not found")
        return {
            "id": ds.id,
            "name": ds.name,
            "n_rows": ds.n_rows,
            "n_cols": ds.n_cols,
            "schema": json.loads(ds.schema) if ds.schema else [],
        }
    finally:
        db.close()


@app.post("/analyze")
async def analyze(req: AnalyzeRequest, user_id: str = Depends(get_current_user)):
    """Ask a question about a dataset. Returns code, result, chart, insight."""
    start = time.time()
    db = SessionLocal()
    try:
        ds = db.query(Dataset).filter(Dataset.id == req.dataset_id).first()
        if not ds or ds.user_id != user_id:
            raise HTTPException(404, "Dataset not found")
        if not os.path.exists(ds.path):
            raise HTTPException(410, "Dataset file no longer available")

        schema = json.loads(ds.schema) if ds.schema else []

        # Step 1: generate code
        try:
            code, code_cost = generate_pandas_code(
                question=req.question,
                schema=schema,
                csv_path=ds.path,
                openai_api_key=OPENAI_API_KEY,
            )
        except Exception as e:
            raise HTTPException(500, f"Code generation failed: {e}")

        # Step 2: execute code
        try:
            result_df_json, exec_log = run_pandas_code(code, ds.path, timeout_s=30)
        except Exception as e:
            db.add(Analysis(
                id=str(uuid.uuid4()), user_id=user_id, dataset_id=ds.id,
                question=req.question, code=code, error=str(e),
                cost_usd=int(code_cost * 1_000_000),
                latency_ms=round((time.time() - start) * 1000),
            ))
            db.commit()
            raise HTTPException(400, f"Code execution failed: {e}")

        # Step 3: render chart
        chart = pick_and_render_chart(result_df_json)

        # Step 4: generate insight (lightweight)
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        insight_resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You summarize a pandas DataFrame result in 1-2 sentences. Be specific with numbers."},
                {"role": "user", "content": f"Question: {req.question}\n\nResult (first 10 rows as JSON):\n{result_df_json[:2000]}"},
            ],
            temperature=0.0,
            max_tokens=150,
        )
        insight = insight_resp.choices[0].message.content
        insight_cost = (insight_resp.usage.prompt_tokens / 1e6) * 0.15 + \
                       (insight_resp.usage.completion_tokens / 1e6) * 0.60

        total_cost = code_cost + insight_cost
        latency_ms = round((time.time() - start) * 1000)

        analysis_id = str(uuid.uuid4())
        analysis = Analysis(
            id=analysis_id, user_id=user_id, dataset_id=ds.id,
            question=req.question, code=code, insight=insight,
            chart=json.dumps(chart) if chart else None,
            cost_usd=int(total_cost * 1_000_000),
            latency_ms=latency_ms,
        )
        db.add(analysis)
        db.commit()

        logger.info(
            f"analyze user={user_id} ds={ds.id} "
            f"cost=${total_cost:.4f} ms={latency_ms}"
        )
        return {
            "analysis_id": analysis_id,
            "code": code,
            "result": result_df_json,
            "chart": chart,
            "insight": insight,
            "cost_usd": total_cost,
            "latency_ms": latency_ms,
        }
    finally:
        db.close()
