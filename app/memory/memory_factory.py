from sqlalchemy.orm import Session as DBSession
from app.memory.base import BaseMemory
from app.memory.sqlite_memory import SQLiteMemory


def get_memory(db: DBSession) -> BaseMemory:
    return SQLiteMemory(db)
