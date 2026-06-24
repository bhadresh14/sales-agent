"""
Abstract memory interface.
Swap the backend by changing one file — SQLiteMemory, PostgresMemory, Mem0Memory, etc.
All agent code depends only on this interface.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from app.models.schemas import MessageRecord


class BaseMemory(ABC):

    @abstractmethod
    def save_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        tools_called: Optional[List[str]] = None,
        eval_data: Optional[dict] = None,
    ) -> None:
        """Persist a single message turn."""
        ...

    @abstractmethod
    def get_history(self, user_id: str) -> List[MessageRecord]:
        """Return full conversation history for a user across all sessions."""
        ...

    @abstractmethod
    def get_recent_context(self, user_id: str, limit: int = 10) -> List[dict]:
        """
        Return the most recent N messages as plain dicts for LLM context injection.
        Format: [{"role": "user"|"assistant", "content": "..."}]
        """
        ...

    @abstractmethod
    def wipe_memory(self, user_id: str) -> None:
        """Delete all stored data for a user (GDPR reset)."""
        ...
