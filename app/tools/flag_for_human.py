from sqlalchemy.orm import Session as DBSession
from app.db.models import HumanFlagLog


def flag_for_human(user_id: str, session_id: str, reason: str, db: DBSession) -> str:
    flag = HumanFlagLog(user_id=user_id, session_id=session_id, reason=reason)
    db.add(flag)
    db.commit()
    return f"Conversation flagged for human review. Reason: {reason}"
