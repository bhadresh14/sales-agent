import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from app.db.database import get_db
from app.models.schemas import (
    ChatRequest, ChatResponse, HistoryResponse, DeleteMemoryResponse,
    CatalogResponse, HealthResponse, EvalAggregateResponse,
)
from app.services.chat_service import handle_chat, get_history, delete_memory, get_eval_aggregates

router = APIRouter()
_CATALOG_PATH = Path(__file__).parent.parent.parent / "catalog.json"


@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    return HealthResponse(status="ok", version="1.0.0")


@router.get("/catalog", response_model=CatalogResponse, tags=["Catalog"])
def get_catalog():
    with open(_CATALOG_PATH, "r") as f:
        data = json.load(f)
    return CatalogResponse(**data)


@router.post("/chat/{user_id}", response_model=ChatResponse, tags=["Chat"])
def chat(user_id: str, request: ChatRequest, db: DBSession = Depends(get_db)):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    return handle_chat(user_id=user_id, message=request.message, db=db)


@router.get("/chat/{user_id}/history", response_model=HistoryResponse, tags=["Chat"])
def conversation_history(user_id: str, db: DBSession = Depends(get_db)):
    return get_history(user_id=user_id, db=db)


@router.delete("/chat/{user_id}/memory", response_model=DeleteMemoryResponse, tags=["Chat"])
def wipe_memory(user_id: str, db: DBSession = Depends(get_db)):
    return delete_memory(user_id=user_id, db=db)


@router.get("/chat/{user_id}/evals", response_model=EvalAggregateResponse, tags=["Evals"])
def eval_aggregates(user_id: str, db: DBSession = Depends(get_db)):
    return get_eval_aggregates(user_id=user_id, db=db)
