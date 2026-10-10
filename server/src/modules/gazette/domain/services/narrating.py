"""Holding what a model wrote to the rules, piece by piece.

A model answers in one breath and gets one thing wrong. Refusing the whole
answer for it would cost the numéro four good paragraphs over one stray
figure, so each piece is checked alone and the ones that fail are dropped.
Nothing is repaired: a text amended by the application is no longer the one
the model wrote.
"""

from collections.abc import Iterable, Mapping

from src.modules.gazette.domain.entities.brief import Brief
from src.modules.gazette.domain.entities.narrative import Narrative
from src.modules.gazette.domain.entities.prose import Prose
from src.modules.gazette.domain.entities.spotlight import Spotlight
from src.modules.gazette.domain.services.figures import allowed_figures
from src.shared.exceptions.domain_exceptions import ValidationError


def hold_narrative(
    brief: Brief,
    model: str,
    editorial: Iterable[str],
    spotlights: Mapping[int, str],
) -> Narrative:
    """What the model wrote that holds, and nothing else.

    A spotlight is kept only for a project the brief chose: a model naming
    another one has invented a flagship.
    """
    allowed = allowed_figures(brief)
    paragraphs = [
        text.strip()
        for text in editorial
        if Prose.accepted(text, model, allowed) is not None
    ]
    kept = []
    for focus in brief.focus:
        text = spotlights.get(focus.project_id)
        if text is None or Prose.accepted(text, model, allowed) is None:
            continue
        try:
            kept.append(Spotlight(focus.project_id, focus.label, text, model))
        except ValidationError:
            continue
    return Narrative(
        editorial=(
            Prose.accepted("\n\n".join(paragraphs), model, allowed)
            if paragraphs
            else None
        ),
        spotlights=tuple(kept),
    )
