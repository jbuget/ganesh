"""What a period of exchanges says about the assistant, counted.

Read by an administrator who studies it: whether the answers help, why the
ones that do not went wrong, how long people wait, and which tools carry the
load. Every figure is computed here, from the exchanges, so that the screen and
an export read the same thing.
"""

import math
import statistics
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from src.modules.assistant.domain.entities.exchange import Cause, Exchange, Verdict


@dataclass(frozen=True)
class Indicators:
    questions: int
    conversations: int
    askers: int
    helpful: int
    unhelpful: int
    unjudged: int
    #: Every cause named, zero included: a cause nobody picked is a finding.
    causes: dict[Cause, int]
    unannotated: int
    #: None when nobody asked: zero would read as an instant answer.
    median_elapsed_ms: int | None
    p95_elapsed_ms: int | None
    input_tokens: int
    output_tokens: int
    #: Each tool with how often the model asked for it, most asked first.
    tools: tuple[tuple[str, int], ...]


def indicators_of(exchanges: Sequence[Exchange]) -> Indicators:
    verdicts = Counter(exchange.verdict for exchange in exchanges)
    causes = Counter(
        exchange.annotation.cause
        for exchange in exchanges
        if exchange.annotation is not None
    )
    tools = Counter(
        consultation.tool
        for exchange in exchanges
        for consultation in exchange.answer.consultations
    )
    elapsed = sorted(exchange.answer.elapsed_ms for exchange in exchanges)
    return Indicators(
        questions=len(exchanges),
        conversations=len({exchange.conversation_id for exchange in exchanges}),
        askers=len({exchange.asker_id for exchange in exchanges}),
        helpful=verdicts[Verdict.HELPFUL],
        unhelpful=verdicts[Verdict.UNHELPFUL],
        unjudged=verdicts[None],
        causes={cause: causes[cause] for cause in Cause},
        unannotated=len(exchanges) - causes.total(),
        median_elapsed_ms=int(statistics.median(elapsed)) if elapsed else None,
        p95_elapsed_ms=_nearest_rank(elapsed, 0.95),
        input_tokens=sum(exchange.answer.input_tokens for exchange in exchanges),
        output_tokens=sum(exchange.answer.output_tokens for exchange in exchanges),
        # Ties broken by name, so that two readings of one period agree.
        tools=tuple(sorted(tools.items(), key=lambda held: (-held[1], held[0]))),
    )


def _nearest_rank(ordered: Sequence[int], share: float) -> int | None:
    """The value under which `share` of the readings fall, one that was read.

    Nearest rank rather than interpolation: a time somebody actually waited.
    """
    if not ordered:
        return None
    return ordered[math.ceil(share * len(ordered)) - 1]
