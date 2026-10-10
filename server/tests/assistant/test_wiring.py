"""The real wiring, which the route tests stand in for and therefore never run.

The route builds a model reading a shelf of tools, and the adapter turns each
tool into a declaration the model reads. A tool Gemini cannot describe would
only show as a 503 in production: it is checked here, without a network.
"""

from types import SimpleNamespace
from typing import Any

from google.genai import types

from src.assistant.dependencies import get_answerer
from src.assistant.gemini_answerer import GeminiAnswerer
from src.assistant.shelf import SHELF, Shelf
from src.core.config import Settings
from src.main import app
from src.modules.assistant.domain.entities.conversation import Conversation
from src.modules.users.domain.entities.user import Role, User

SYLVAIN = User(
    id=4, entra_oid="oid-4", email="s@waat.fr", display_name="S. P", role=Role.MANAGER
)


class Recorded:
    """A model that answers at once, keeping the configuration it was sent."""

    def __init__(self) -> None:
        self.config: Any = None

    async def generate_content(self, *, model: str, contents: Any, config: Any) -> Any:
        self.config = config
        return types.GenerateContentResponse(
            candidates=[
                types.Candidate(
                    content=types.Content(
                        role="model", parts=[types.Part(text="Oui.")]
                    ),
                    finish_reason=types.FinishReason.STOP,
                )
            ]
        )


def configured(key: str) -> Settings:
    return Settings(gemini_api_key=key, gemini_model="gemini-test")  # type: ignore[call-arg]


def test_with_a_key_the_route_is_handed_a_model_to_ask() -> None:
    answerer = get_answerer(SimpleNamespace(app=app), configured("key"), SYLVAIN)  # type: ignore[arg-type]

    assert isinstance(answerer, GeminiAnswerer)
    assert answerer.is_available


def test_without_a_key_the_route_is_handed_a_model_that_never_answers() -> None:
    answerer = get_answerer(SimpleNamespace(app=app), configured(""), SYLVAIN)  # type: ignore[arg-type]

    assert not answerer.is_available


async def test_every_tool_on_the_shelf_is_declared_to_the_model() -> None:
    models = Recorded()
    answerer = GeminiAnswerer(
        api_key="key",
        model="gemini-test",
        toolbox=Shelf(SYLVAIN, {}),
        client=SimpleNamespace(aio=SimpleNamespace(models=models)),  # type: ignore[arg-type]
    )

    await answerer.answer(Conversation.opened(4), "Question ?", None)

    declared = models.config.tools[0].function_declarations
    assert [declaration.name for declaration in declared] == [
        tool.__name__ for tool in SHELF
    ]
    assert all(declaration.description for declaration in declared)
