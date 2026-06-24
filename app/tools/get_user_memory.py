from typing import List
from sqlalchemy.orm import Session as DBSession
from app.db.models import Message


def get_user_memory(user_id: str, db: DBSession, limit: int = 10) -> str:
    messages: List[Message] = (
        db.query(Message)
        .filter_by(user_id=user_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )

    if not messages:
        return f"No previous conversation history found for user '{user_id}'."

    lines = [f"Past conversation history for user '{user_id}':"]
    for msg in reversed(messages):
        role_label = "User" if msg.role == "user" else "Assistant"
        lines.append(f"  [{role_label}]: {msg.content}")

    return "\n".join(lines)
