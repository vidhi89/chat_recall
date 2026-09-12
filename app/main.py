from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Semantic search engine for messy group conversations.",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": "ChatRecall API is running."
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }