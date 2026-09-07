from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """A tool is a named callable with a declared JSON schema.

    `name` and `schema` describe the tool to the model; `__call__` executes
    one invocation and returns the observation as a string.
    """

    name: str
    schema: Dict[str, Any]

    @abstractmethod
    async def __call__(self, **arguments) -> str:
        ...
