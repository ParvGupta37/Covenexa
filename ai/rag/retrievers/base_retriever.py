"""
Abstract Retriever interface.
"""
from abc import ABC, abstractmethod
from typing import Any, List


class BaseRetriever(ABC):
    """
    Abstract retriever base class.
    """

    @abstractmethod
    async def retrieve(self, query: str, limit: int = 5, **kwargs: Any) -> List[dict]:
        """
        Query target data source and return list of matched node/row/vector dictionaries.
        """
        ...
