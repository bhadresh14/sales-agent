from sqlalchemy.orm import Session as DBSession
from app.agents.sales_agent import run_agent
from app.memory.memory_factory import get_memory
from app.models.schemas import ChatResponse, HistoryResponse, DeleteMemoryResponse, EvalAggregateResponse
from app.db.models import EvalLog


def handle_chat(user_id: str, message: str, db: DBSession) -> ChatResponse:
    return run_agent(user_id=user_id, user_message=message, db=db)


def get_history(user_id: str, db: DBSession) -> HistoryResponse:
    memory = get_memory(db)
    messages = memory.get_history(user_id)
    return HistoryResponse(user_id=user_id, total_messages=len(messages), messages=messages)


def delete_memory(user_id: str, db: DBSession) -> DeleteMemoryResponse:
    memory = get_memory(db)
    memory.wipe_memory(user_id)
    return DeleteMemoryResponse(user_id=user_id, message=f"All memory for user '{user_id}' has been deleted.")


def get_eval_aggregates(user_id: str, db: DBSession) -> EvalAggregateResponse:
    evals = db.query(EvalLog).filter_by(user_id=user_id).all()

    if not evals:
        return EvalAggregateResponse(
            user_id=user_id, total_responses=0,
            avg_groundedness=0.0, avg_relevance=0.0, avg_confidence=0.0,
            high_confidence_pct=0.0, flagged_count=0,
        )

    total = len(evals)
    return EvalAggregateResponse(
        user_id=user_id,
        total_responses=total,
        avg_groundedness=round(sum(e.groundedness for e in evals) / total, 3),
        avg_relevance=round(sum(e.relevance for e in evals) / total, 3),
        avg_confidence=round(sum(e.confidence for e in evals) / total, 3),
        high_confidence_pct=round(sum(1 for e in evals if e.confidence >= 0.8) / total * 100, 1),
        flagged_count=sum(1 for e in evals if e.flagged),
    )
