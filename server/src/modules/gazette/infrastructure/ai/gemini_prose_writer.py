"""Asking Gemini for the editorial and the spotlights of a numéro.

A deliberate divergence from WAATcher, which calls Gemini through
`google-generativeai`: that SDK is retired, and it has no async call, so
WAATcher hands the blocking one to a thread pool. Ganesh asks for
`async/await` on every I/O, and `google-genai` answers it natively. The shape
of the thing is WAATcher's all the same — a provider behind a port, a missing
key that disables rather than breaks.

Nothing here decides what may be said. Whatever comes back is held to the
domain's rules piece by piece (`hold_narrative`): an adapter cannot widen
them, only fail to produce anything at all.
"""

import json
import logging
from typing import Any

from google import genai
from google.genai import types

from src.modules.gazette.domain.entities.dossier import Dossier
from src.modules.gazette.domain.entities.narrative import Narrative
from src.modules.gazette.domain.repositories.prose_writer import ProseWriter
from src.modules.gazette.domain.services.narrating import hold_narrative
from src.modules.gazette.domain.services.prompts.narrative_prompt import compose

logger = logging.getLogger(__name__)

#: A few paragraphs and up to three spotlights run to some two thousand tokens
#: of French. The rest of this budget is for the model's own reasoning, which
#: is billed as output and cannot be turned off: `thinking_budget=0` is quietly
#: ignored by the recent Flash models. Too small and the reasoning eats the
#: whole allowance, the answer is cut, and what comes back is not JSON.
MAX_OUTPUT_TOKENS = 12000

#: Low, not zero. The text is a reading of facts, not a variation on them, but
#: a month told in the same words every time would not read like a story.
TEMPERATURE = 0.4


class GeminiProseWriter(ProseWriter):
    """Writes the editorial and the spotlights, or says nothing at all.

    Saying nothing is a normal outcome, not a failure to handle upstream: no
    key configured, the API down, a model in a mood, or prose that counted.
    The numéro goes out on its facts either way.
    """

    def __init__(self, api_key: str, model: str) -> None:
        self._model = model
        self._client = genai.Client(api_key=api_key) if api_key else None
        if self._client is None:
            logger.info("No Gemini key configured: numéros go out without prose.")

    async def write(self, dossier: Dossier) -> Narrative:
        month = dossier.brief.month
        if self._client is None:
            return Narrative()

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=compose(dossier),
                config=types.GenerateContentConfig(
                    temperature=TEMPERATURE,
                    max_output_tokens=MAX_OUTPUT_TOKENS,
                    response_mime_type="application/json",
                ),
            )
        except Exception as error:
            logger.warning("Gemini wrote nothing for %s: %s", month, error)
            return Narrative()

        if not _finished(response):
            # Cut off mid-thought, what comes back is working-out rather than
            # a text — and working-out is not JSON, but a truncated one can
            # still parse. Refused here instead.
            logger.warning("Gemini was cut short on %s; nothing written.", month)
            return Narrative()

        parsed = _parse(response.text)
        if parsed is None:
            logger.warning("Gemini answered something unreadable for %s.", month)
            return Narrative()

        editorial, spotlights = parsed
        narrative = hold_narrative(dossier.brief, self._model, editorial, spotlights)
        kept = len(narrative.spotlights) + (
            len(narrative.editorial.paragraphs) if narrative.editorial else 0
        )
        if kept < len(editorial) + len(spotlights):
            logger.warning("Some of what was written for %s did not hold.", month)
        return narrative


def _parse(text: str | None) -> tuple[list[str], dict[int, str]] | None:
    """The two parts of the answer, or nothing if it is not what was asked."""
    if not text:
        return None
    try:
        payload: Any = json.loads(text)
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None

    editorial = [
        paragraph
        for paragraph in payload.get("editorial") or []
        if isinstance(paragraph, str)
    ]
    spotlights: dict[int, str] = {}
    for row in payload.get("spotlights") or []:
        if (
            isinstance(row, dict)
            and isinstance(row.get("project_id"), int)
            and isinstance(row.get("text"), str)
        ):
            spotlights[row["project_id"]] = row["text"]
    return editorial, spotlights


def _finished(response: types.GenerateContentResponse) -> bool:
    """Whether the model stopped because it had finished, not because it ran out."""
    candidates = response.candidates or []
    if not candidates:
        return False
    return candidates[0].finish_reason is types.FinishReason.STOP
