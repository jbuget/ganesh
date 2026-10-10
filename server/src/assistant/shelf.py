"""The tools, read on behalf of somebody asking the assistant.

A terminal client reaches the tools with a key; the assistant's model reaches
the same ones, in the API's own process, for the person signed in. Same
functions, same sentences, same use cases underneath — the second way in costs
no process and no second description of a project.

**What is on the shelf reads the projects and who is free for them.** Nothing
that writes: a model that misread a question must not be able to act on it. Not the moods
either — they were given in confidence to an internal screen, and a frame
changed quietly is what costs the answering rate.

A refusal is a reading like any other. The model is told the project does not
exist or the date does not parse, and says so, rather than the whole answer
failing on it.
"""

import inspect
from collections.abc import Callable, Mapping, Sequence
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from typing import Any, get_args

from sqlalchemy.ext.asyncio import AsyncSession

from mcp.server.mcpserver.exceptions import ToolError
from src.assistant.toolbox import Tool, Toolbox
from src.mcp.door import Machine, standing
from src.mcp.tools.brief import project_brief
from src.mcp.tools.news import project_news
from src.mcp.tools.plan import person_plan
from src.mcp.tools.portfolio import portfolio_status
from src.mcp.tools.projects import find_project
from src.mcp.tools.updates import what_changed
from src.mcp.wiring import Provider, Wiring, session_scope
from src.modules.api_keys.domain.entities.api_key import NEVER_BROAD, ApiKeyScope
from src.modules.assistant.domain.entities.exchange import Consultation
from src.modules.users.domain.entities.user import User

#: `person_plan` is the one tool here no key reaches: the projection of the
#: « Planification » screen is an arbitration, and `roadmap:read` opens the
#: roadmap to machines while deliberately leaving it shut (`docs/api-keys.md`).
#: A person signed in reads that screen already; the assistant reads it for
#: them, and for nobody else.
SHELF: tuple[Tool, ...] = (
    find_project,
    project_brief,
    project_news,
    what_changed,
    portfolio_status,
    person_plan,
)


@dataclass(frozen=True)
class PersonCaller:
    """A person, asking through the assistant.

    Granted what reads and nothing else, whatever their role: the shelf holds
    no writing tool, and this says so a second time where a tool checks.
    """

    person: User

    @property
    def actor_id(self) -> int:
        assert self.person.id is not None
        return self.person.id

    def grants(self, scope: ApiKeyScope) -> bool:
        return scope.is_read and scope not in NEVER_BROAD

    def may(self, scope: ApiKeyScope) -> bool:
        return scope.is_read or self.person.can_write()


#: Where a reading's session comes from. One per reading, opened and closed
#: around it: the model takes seconds between two reads, and a transaction held
#: open across them is a connection the pool does not get back.
Sessions = Callable[[], AbstractAsyncContextManager[AsyncSession]]


class Shelf(Toolbox):
    def __init__(
        self,
        person: User,
        overrides: Mapping[Provider, Provider],
        sessions: Sessions = session_scope,
    ) -> None:
        self._caller = PersonCaller(person)
        self._overrides = overrides
        self._sessions = sessions

    @property
    def tools(self) -> Sequence[Tool]:
        return SHELF

    async def consult(self, tool: str, arguments: Mapping[str, Any]) -> Consultation:
        found = next((held for held in SHELF if held.__name__ == tool), None)
        if found is None:
            return Consultation(
                tool, dict(arguments), f"L'outil « {tool} » n'existe pas."
            )

        try:
            given = _bound(found, arguments)
        except TypeError:
            said = ", ".join(f"{name}=« {value} »" for name, value in arguments.items())
            return Consultation(
                tool,
                dict(arguments),
                f"« {tool} » ne prend pas ces paramètres : {said}.",
            )

        async with self._sessions() as session:
            wiring = Wiring(session=session, overrides=self._overrides)
            with standing(Machine(caller=self._caller, wiring=wiring)):
                try:
                    result = await found(**given)
                except ToolError as refusal:
                    result = str(refusal)
        return Consultation(tool, given, result)


def _bound(tool: Tool, arguments: Mapping[str, Any]) -> dict[str, Any]:
    """The arguments as the tool declares them, or `TypeError`.

    JSON knows numbers, not integers: an identifier handed over as `7.0` is
    still project 7. One handed over as « 7 » is not — it is refused here, as
    a reading the model corrects, rather than reaching a repository that would
    raise and take the whole answer with it.
    """
    signature = inspect.signature(tool)
    signature.bind(**arguments)
    return {
        name: _as_declared(signature.parameters[name].annotation, value)
        for name, value in arguments.items()
    }


def _as_declared(annotation: Any, value: Any) -> Any:
    accepted = get_args(annotation) or (annotation,)
    if value is None and type(None) in accepted:
        return None
    if int in accepted and isinstance(value, float) and value.is_integer():
        return int(value)
    if int in accepted and isinstance(value, int) and not isinstance(value, bool):
        return value
    if str in accepted and isinstance(value, str):
        return value
    raise TypeError(f"{value!r} is not a {annotation}")
