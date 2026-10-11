"""« Qu'est-ce qui s'est passé ce mois-ci, en gros ? »

The gazette reads the register across, a month at a time. This reads **what it
already holds** and generates nothing: asking for a digest writes a version
and costs a model call, and a terminal client asking « et septembre ? » has
not asked for either.

Three rules the gazette keeps are kept here:

- **the register counts, the model only turns the phrase.** The figures are
  said as the register computed them; what a model wrote — the editorial, a
  spotlight — is announced as machine-written, a reader weighing it
  differently once they know;
- **a worry is about a project, never about a person.** `Highlight` refuses
  the combination; a teammate arriving, returning or leaving is a fact of the
  month and is named plainly;
- **nothing is invented.** A month nobody generated is read from the register
  with no chapeau, and says so. A generated month without an editorial says
  the model was not heard, rather than leaving a silence a reader fills.

The chapters, movement by movement, stay on the screen: reading them is what a
project's « Journal » and `what_changed` are for. Only what the gazette
**stands out** and **counts** is said here — which is also what keeps a
request, which is not a mission, out of a reading that is not about them.

The month is read as the gazette reads it: a digest's own figures, never the
register as it stands today.
"""

from src.mcp.door import answers, current_machine
from src.mcp.tools import say
from src.mcp.tools.when import month_asked
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.gazette.application.dtos.gazette_dtos import (
    DigestView,
    ReadDigestQuery,
)
from src.modules.gazette.domain.entities.brief import Tally
from src.modules.gazette.domain.entities.highlight import Highlight, HighlightKind, Tone
from src.modules.gazette.presentation.dependencies import get_read_digest_use_case
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from src.shared.utils import clock

SCOPE = ApiKeyScope.AUDIT_READ

#: Each highlight, said as a noun phrase after the name it is about. A phrase
#: rather than a sentence: it agrees with nothing, so a project and a lot, a
#: man and a woman, read alike.
HIGHLIGHTS = {
    HighlightKind.WENT_LIVE: "mise en service",
    HighlightKind.TEAMMATE_JOINED: "arrivée dans l'équipe",
    HighlightKind.TEAMMATE_RETURNED: "retour dans l'équipe",
    HighlightKind.TEAMMATE_LEFT: "départ de l'équipe",
    HighlightKind.PHASE_STEPPED_BACK: "retour en arrière de phase",
    HighlightKind.ARCHIVED_BEFORE_DELIVERY: "archivé avant d'être livré",
    HighlightKind.GO_LIVE_OVERDUE: "date de mise en service dépassée",
}


@answers(SCOPE)
async def gazette(month: str | None = None, version: int | None = None) -> str:
    """Dit ce qui s'est passé un mois donné dans le registre : chiffres, faits.

    Rend ce que la Gazette compte — projets créés et archivés, changements de
    phase, mises à jour, mois validés, besoins déposés — puis ce qui ressort
    (mises en service, arrivées et départs) et ce qui doit inquiéter (un
    retour en arrière, une date dépassée, toujours à propos d'un projet,
    jamais d'une personne). Si le mois a été généré, rend aussi l'éditorial
    et les projets mis en avant, rédigés par un modèle et annoncés comme tels.
    Ne génère rien. Le mois se donne au format AAAA-MM ; sans rien, c'est le
    mois courant. `version` lit une génération précise, la dernière par défaut.
    """
    asked = month_asked(month)
    if asked is None:
        return (
            f"« {month} » ne se lit pas comme un mois. "
            "Le format est AAAA-MM, « 2026-09 » par exemple."
        )

    use_case = await current_machine().resolve(get_read_digest_use_case)
    try:
        view = await use_case.execute(ReadDigestQuery(month=asked, version=version))
    except EntityNotFoundError:
        return f"La Gazette de {say.month(asked)} n'a pas de version {version}."

    return "\n".join(
        [
            _headline(view, say.month(asked)),
            _counted(view.brief.tally),
            *_requests(view.brief.tally),
            *_standing_out(view.brief.highlights, Tone.NOTABLE, "À noter"),
            *_standing_out(view.brief.highlights, Tone.ATTENTION, "Points d'attention"),
            *_written(view),
        ]
    )


def _headline(view: DigestView, month: str) -> str:
    if view.generated_at is None:
        return (
            f"Gazette de {month} — pas encore générée : les faits seuls, "
            "tels que le registre les compte, sans éditorial."
        )
    generated = view.generated_at.astimezone(clock.PARIS).date()
    return (
        f"Gazette de {month} — version {view.version}, générée le "
        f"{say.dated(generated)} à la demande de {view.requested_by}."
    )


def _counted(tally: Tally) -> str:
    counts = [
        (
            tally.projects_created,
            f"{say.agreeing(tally.projects_created, 'projet')} "
            f"{say.agreed('créé', tally.projects_created)}",
        ),
        (
            tally.projects_archived,
            f"{tally.projects_archived} {say.agreed('archivé', tally.projects_archived)}",
        ),
        (
            tally.phase_changes,
            f"{say.agreeing(tally.phase_changes, 'changement')} de phase",
        ),
        (tally.news_posted, f"{say.agreeing(tally.news_posted, 'mise')} à jour"),
        (
            tally.months_validated,
            f"{tally.months_validated} mois {say.agreed('validé', tally.months_validated)}",
        ),
    ]
    said = [text for count, text in counts if count]
    if not said:
        return "Rien n'a bougé dans le registre ce mois-là."
    return f"Ce mois-là : {', '.join(said)}."


def _requests(tally: Tally) -> list[str]:
    """What was asked, kept apart from what was built: two facts, not one."""
    if not tally.requests_filed and not tally.requests_converted:
        return []
    asked = say.agreeing(tally.requests_filed, "besoin")
    filed = f"{asked} {say.agreed('déposé', tally.requests_filed)}"
    if tally.requests_converted == 0:
        return [f"{filed}, dont aucun devenu projet."]
    converted = tally.requests_converted
    became = (
        f"{converted} {say.agreed('devenu', converted)} "
        f"{'projets' if converted >= 2 else 'projet'}"
    )
    return [f"{filed}, dont {became}."]


def _standing_out(highlights: list[Highlight], tone: Tone, heading: str) -> list[str]:
    held = [h for h in highlights if h.tone is tone]
    if not held:
        return []
    return [f"{heading} :", *(f"- {h.label} — {HIGHLIGHTS[h.kind]}" for h in held)]


def _written(view: DigestView) -> list[str]:
    """What a model wrote over the facts, announced as such. See the module."""
    if view.generated_at is None:
        return []
    lines = []
    if view.prose is None:
        lines.append(
            "Cette version est sans éditorial : le modèle n'a rien rendu qui tienne."
        )
    else:
        lines += [
            f"Éditorial, rédigé par {view.prose.model} :",
            view.prose.text,
        ]
    lines += [
        f"Sur {spotlight.label} (rédigé par {spotlight.model}) : {spotlight.text}"
        for spotlight in view.spotlights
    ]
    return lines
