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
    ) -> None: ...

    @abstractmethod
    def get_history(self, user_id: str) -> List[MessageRecord]: ...

    @abstractmethod
    def get_recent_context(self, user_id: str, limit: int = 10) -> List[dict]: ...

    @abstractmethod
    def wipe_memory(self, user_id: str) -> None: ...
