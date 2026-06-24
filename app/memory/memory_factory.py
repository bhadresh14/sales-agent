"""
Single place to swap the memory backend.
Change the import here to switch from SQLite → Postgres → Mem0, etc.
"""
from sqlalchemy.orm import Session as DBSession
from app.memory.base import BaseMemory
from app.memory.sqlite_memory import SQLiteMemory


def get_memory(db: DBSession) -> BaseMemory:
    """
    Factory function. To swap backends:
      from app.memory.postgres_memory import PostgresMemory
      return PostgresMemory(db)
    """
    return SQLiteMemory(db)
