"""Asking Gemini for the chapeau of a numéro.

A deliberate divergence from WAATcher, which calls Gemini through
`google-generativeai`: that SDK is retired, and it has no async call, so
WAATcher hands the blocking one to a thread pool. Ganesh asks for
`async/await` on every I/O, and `google-genai` answers it natively. The shape
of the thing is WAATcher's all the same — a provider behind a port, a missing
key that disables rather than breaks.

Nothing here decides what a chapeau may say. Whatever comes back goes through
`Prose`, which refuses anything carrying a figure: an adapter cannot widen the
rule, only fail to produce prose at all.
"""

import logging

from google import genai
from google.genai import types

from src.modules.gazette.domain.entities.brief import Brief
from src.modules.gazette.domain.entities.prose import Prose
from src.modules.gazette.domain.repositories.prose_writer import ProseWriter
from src.modules.gazette.domain.services.prompts.chapeau_prompt import compose

logger = logging.getLogger(__name__)

#: A chapeau is two or three sentences. The budget is what stops a model that
#: has decided to write an essay, and it is shared with the model's own
#: reasoning — which is why that is turned off below rather than left to eat
#: the whole allowance and return a truncated sentence.
MAX_OUTPUT_TOKENS = 400

#: Low, not zero. The chapeau is a reading of facts, not a variation on them.
TEMPERATURE = 0.3


class GeminiProseWriter(ProseWriter):
    """Writes the chapeau, or says nothing at all.

    Saying nothing is a normal outcome, not a failure to handle upstream: no
    key configured, the API down, a model in a mood, or prose that counted.
    The numéro goes out on its facts either way.
    """

    def __init__(self, api_key: str, model: str) -> None:
        self._model = model
        self._client = genai.Client(api_key=api_key) if api_key else None
        if self._client is None:
            logger.info("No Gemini key configured: numéros go out without a chapeau.")

    async def write(self, brief: Brief) -> Prose | None:
        if self._client is None:
            return None

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=compose(brief),
                config=types.GenerateContentConfig(
                    temperature=TEMPERATURE,
                    max_output_tokens=MAX_OUTPUT_TOKENS,
                    # The chapeau restates facts it has been handed. Thinking
                    # buys nothing here and spends the output budget.
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
        except Exception as error:
            logger.warning("Gemini wrote no chapeau for %s: %s", brief.month, error)
            return None

        text = response.text
        if not text:
            logger.warning("Gemini answered nothing for %s.", brief.month)
            return None

        prose = Prose.accepted(text, self._model)
        if prose is None:
            logger.warning(
                "The chapeau written for %s counted, and was dropped.", brief.month
            )
        return prose
