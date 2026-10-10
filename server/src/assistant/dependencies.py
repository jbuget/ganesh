"""Wiring of the model, for the person asking."""

from fastapi import Depends, Request

from src.assistant.answerer import Answerer
from src.assistant.gemini_answerer import GeminiAnswerer
from src.assistant.shelf import Shelf
from src.core.config import Settings, get_settings
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.users.domain.entities.user import User


def get_answerer(
    request: Request,
    settings: Settings = Depends(get_settings),
    person: User = Depends(get_current_user),
) -> Answerer:
    """The model that answers, reading the tools for the person asking.

    The same model and key as the gazette. The shelf honours the overrides of
    the API it serves, so a tool reached through it is stood in for exactly as
    a route's use case is.
    """
    return GeminiAnswerer(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        toolbox=Shelf(person, request.app.dependency_overrides),
    )
