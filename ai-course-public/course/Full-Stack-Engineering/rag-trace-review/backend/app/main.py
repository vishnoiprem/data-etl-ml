"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .routes.traces import router as traces_router
from .routes.feedback import router as feedback_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("rag.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    log.info("startup complete")
    yield
    log.info("shutdown")


app = FastAPI(title="RAG Trace Review API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(traces_router)
app.include_router(feedback_router)


@app.get("/health")
def health():
    return {"status": "ok"}
