"""Port for what the model may consult: the tools, read on somebody's behalf.

The tools are the ones a terminal client reaches through MCP, and they are the
assistant's only source. `Shelf` is the one implementation; the port is what
lets the model's loop be tested without it.
"""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any

from src.modules.assistant.domain.entities.exchange import Consultation

#: A question somebody asks, answered in sentences. Its signature and its
#: docstring are what the model reads to decide when to ask it.
Tool = Callable[..., Awaitable[str]]


class Toolbox(ABC):
    @property
    @abstractmethod
    def tools(self) -> Sequence[Tool]: ...

    @abstractmethod
    async def consult(self, tool: str, arguments: Mapping[str, Any]) -> Consultation:
        """Runs one tool and keeps what it read.

        A refusal is a reading like any other: the model is told the project
        does not exist, rather than the conversation failing on it.
        """
        ...
