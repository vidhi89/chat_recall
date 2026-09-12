from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import settings
from src.retrieval.search import SemanticSearch


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


# Load the retrieval engine once when the API starts.
search_engine = SemanticSearch()


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": "ChatRecall API is running.",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/search")
def search(request: SearchRequest):
    results = search_engine.search(
        request.query,
        top_k=request.top_k,
    )

    analysis = {
        "intent": results[0].get("query_intent") if results else None,
        "person": results[0].get("query_person") if results else None,
        "time": results[0].get("query_time") if results else None,
        "topic": results[0].get("query_topic") if results else None,
    }

    return {
        "query": request.query,
        "analysis": analysis,
        "results": results,
    }