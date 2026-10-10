"""What the adapter does when the model does not answer."""

from datetime import date
from typing import Any

import pytest

from src.modules.gazette.domain.entities.brief import Brief, Tally
from src.modules.gazette.domain.entities.dossier import Dossier
from src.modules.gazette.infrastructure.ai.gemini_prose_writer import GeminiProseWriter


class _Models:
    """A model that is down."""

    async def generate_content(self, **_: Any) -> Any:
        raise RuntimeError("down")


class _Aio:
    def __init__(self, models: _Models) -> None:
        self.models = models


class _Client:
    def __init__(self, models: _Models) -> None:
        self.aio = _Aio(models)


@pytest.mark.asyncio
async def test_a_failing_model_costs_the_text_and_never_the_month() -> None:
    models = _Models()
    writer = GeminiProseWriter(api_key="key", model="m")
    writer._client = _Client(models)  # type: ignore[assignment]

    narrative = await writer.write(
        Dossier(brief=Brief(month=date(2026, 9, 1), tally=Tally()))
    )

    assert narrative.editorial is None
    assert narrative.spotlights == ()
