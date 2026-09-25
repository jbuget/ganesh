"""What a mission is told of the need it was born of.

A request says three things a mission has no field for — the situation, who
lives with it, what would change — and losing them at the moment a project is
created would leave the team with a title and nothing else. They are written
into the sheet, under their own headings, in the words whoever asked for it
used.

Markdown, because that is what `description` holds and what the sheet renders.
"""

from src.modules.requests.domain.entities.request import Request

#: What each part of the need is called in the sheet the mission carries.
HEADINGS = (
    ("Le problème", "problem"),
    ("Qui est concerné", "impact"),
    ("Résultat attendu", "expected_outcome"),
    ("Coût de l'inaction", "cost_of_inaction"),
    ("Échéance souhaitée", "desired_timing"),
    ("Piste envisagée", "envisaged_solution"),
)


def brief_of(request: Request) -> str | None:
    """The need, written as the opening of the mission's sheet.

    What was left unsaid gets no heading: an empty section would read as a
    question nobody answered, where the truth is that nobody was asked.
    """
    parts = [
        f"## {heading}\n\n{value}"
        for heading, field in HEADINGS
        if (value := getattr(request, field)) is not None
    ]
    return "\n\n".join(parts) if parts else None


def contacts_of(request: Request, requester: str, sponsors: list[str]) -> str:
    """Who asked for it, and who carried it — in the mission's own field.

    The two names the mission would otherwise lose the day nobody reads the
    request any more. Free text, as `business_contacts` already is.
    """
    carried = ", ".join(sponsors)
    return f"Demandé par {requester}" + (f", porté par {carried}" if carried else "")
