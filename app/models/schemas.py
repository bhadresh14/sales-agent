from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class EvalRecord(BaseModel):
    groundedness: float
    relevance: float
    confidence: float
    flagged: bool
    reasoning: str


class ChatResponse(BaseModel):
    response: str
    eval: EvalRecord
    tools_called: List[str]
    session_id: str
    user_id: str


class MessageRecord(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    tools_called: List[str] = []
    eval: Optional[EvalRecord] = None
    created_at: datetime

    class Config:
        from_attributes = True


class HistoryResponse(BaseModel):
    user_id: str
    total_messages: int
    messages: List[MessageRecord]


class Plan(BaseModel):
    name: str
    price: str
    features: List[str]
    description: str


class FAQ(BaseModel):
    question: str
    answer: str


class CatalogResponse(BaseModel):
    plans: List[Plan]
    faqs: List[FAQ]


class HealthResponse(BaseModel):
    status: str
    version: str


class DeleteMemoryResponse(BaseModel):
    user_id: str
    message: str


class EvalAggregateResponse(BaseModel):
    user_id: str
    total_responses: int
    avg_groundedness: float
    avg_relevance: float
    avg_confidence: float
    high_confidence_pct: float
    flagged_count: int
