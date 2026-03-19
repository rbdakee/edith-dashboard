from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Abstract base repository."""

    @abstractmethod
    async def get(self, id: str) -> T | None:
        ...

    @abstractmethod
    async def list(self, **filters) -> list[T]:
        ...

    @abstractmethod
    async def create(self, obj: T) -> T:
        ...

    @abstractmethod
    async def update(self, id: str, data: dict[str, Any]) -> T | None:
        ...

    @abstractmethod
    async def delete(self, id: str) -> bool:
        ...
