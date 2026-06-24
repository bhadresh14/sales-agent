"""
SQLite-backed memory implementation.
To swap to Postgres: create postgres_memory.py implementing BaseMemory,
update memory_factory.py — nothing else changes.
"""
import json
from typing import List, Optional

from sqlalchemy.orm import Session as DBSession

from app.db.models import Session, Message, EvalLog
from app.memory.base import BaseMemory
from app.models.schemas import MessageRecord, EvalRecord


class SQLiteMemory(BaseMemory):

    def __init__(self, db: DBSession):
        self.db = db

    def save_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        tools_called: Optional[List[str]] = None,
        eval_data: Optional[dict] = None,
    ) -> None:
        # Ensure the session row exists
        session = self.db.query(Session).filter_by(id=session_id).first()
        if not session:
            session = Session(id=session_id, user_id=user_id)
            self.db.add(session)
            self.db.flush()

        msg = Message(
            session_id=session_id,
            user_id=user_id,
            role=role,
            content=content,
            tools_called=json.dumps(tools_called) if tools_called else None,
        )
        self.db.add(msg)
        self.db.flush()

        # Attach eval log for assistant messages
        if role == "assistant" and eval_data:
            ev = EvalLog(
                message_id=msg.id,
                user_id=user_id,
                groundedness=eval_data.get("groundedness", 0.0),
                relevance=eval_data.get("relevance", 0.0),
                confidence=eval_data.get("confidence", 0.0),
                flagged=eval_data.get("flagged", False),
                reasoning=eval_data.get("reasoning", ""),
            )
            self.db.add(ev)

        self.db.commit()

    def get_history(self, user_id: str) -> List[MessageRecord]:
        messages = (
            self.db.query(Message)
            .filter_by(user_id=user_id)
            .order_by(Message.created_at.asc())
            .all()
        )
        records = []
        for m in messages:
            eval_record = None
            if m.eval:
                eval_record = EvalRecord(
                    groundedness=m.eval.groundedness,
                    relevance=m.eval.relevance,
                    confidence=m.eval.confidence,
                    flagged=m.eval.flagged,
                    reasoning=m.eval.reasoning or "",
                )
            records.append(
                MessageRecord(
                    id=m.id,
                    session_id=m.session_id,
                    role=m.role,
                    content=m.content,
                    tools_called=json.loads(m.tools_called) if m.tools_called else [],
                    eval=eval_record,
                    created_at=m.created_at,
                )
            )
        return records

    def get_recent_context(self, user_id: str, limit: int = 10) -> List[dict]:
        messages = (
            self.db.query(Message)
            .filter_by(user_id=user_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )
        # Return in chronological order for LLM context
        return [
            {"role": m.role, "content": m.content}
            for m in reversed(messages)
        ]

    def wipe_memory(self, user_id: str) -> None:
        # Deletes cascade from sessions → messages → eval_logs
        self.db.query(Session).filter_by(user_id=user_id).delete()
        self.db.commit()
