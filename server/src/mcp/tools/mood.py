"""« Comment va l'équipe, ces deux dernières semaines ? »

The only tool that reads something given in confidence, and the one written
mostly around what it must **not** say.

The team screen names everyone, on purpose: it is a mirror the team holds up
to itself. What it never does is aggregate *one person over time* — it
juxtaposes days, in columns. Handed the names, a model would do exactly that
(« X est sous la moyenne depuis huit jours »), and a judgement on a person is
what the screen is built not to produce. So nothing nominative leaves here:
no name, no initials, no identifier. Without one, nothing can be recomposed.

Two more rules ride on that:

- **a day too few answered is not averaged.** Two answers out of twelve say
  what two people felt, and a mean over them reads like the team's.
- **`moods:read` is carried explicitly or not at all** — `NEVER_BROAD` in the
  domain keeps `all:read` from reaching it. A key opens this because somebody
  decided it, on a key the whole team can read off the table.

Before this reaches the team, the team is told. The moods were given to an
internal screen; making them readable by an assistant changes the frame, and a
frame changed quietly is what costs the answering rate — a moodmètre nobody
fills in measures nothing at all.
"""

from src.mcp.door import answers, current_machine
from src.mcp.tools import say
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.moods.domain.services.mood_report import DayMoods, MoodReport
from src.modules.moods.presentation.dependencies import get_team_moods_use_case

SCOPE = ApiKeyScope.MOODS_READ

#: Below this many answers, a day is announced rather than averaged.
FLOOR = 3

#: Days whose mean sits under this are worth naming on their own.
DIP = 3.0

#: Past this, naming the days one by one is reading the screen out loud.
MOST_DIPS = 5


@answers(SCOPE)
async def team_mood() -> str:
    """Dit le moral de l'équipe sur la quinzaine, en chiffres d'ensemble.

    Ne rend aucun nom : ni qui a répondu, ni ce que chacun a dit. La question
    à laquelle il répond est « comment va l'équipe », pas « comment va qui ».
    """
    use_case = await current_machine().resolve(get_team_moods_use_case)
    team = await use_case.execute()
    return _read(team.report)


def _read(report: MoodReport) -> str:
    """The fortnight as figures nobody can be read out of."""
    answered = [day for day in report.days if day.participation >= FLOOR]
    thin = [day for day in report.days if 0 < day.participation < FLOOR]

    if not answered and not thin:
        return (
            "Personne n'a répondu sur la quinzaine. "
            f"L'équipe compte {report.headcount} personnes."
        )

    if not answered:
        return (
            "Trop peu de réponses sur la quinzaine pour en tirer une moyenne : "
            f"{_answers(thin)} en tout, dans une équipe de {report.headcount}."
        )

    lines = [_overall(report, answered)]
    if thin:
        lines.append(
            f"{len(thin)} {say.agreed('journée', len(thin))} "
            f"{say.agreed('compte', len(thin))} moins de {FLOOR} réponses : "
            "trop peu pour en dire quelque chose."
        )
    lines.extend(_dips(answered))
    return "\n".join(lines)


def _overall(report: MoodReport, answered: list[DayMoods]) -> str:
    """One figure for the fortnight, weighed by the answers it rests on.

    The mean of the daily means would weigh a day three people answered like
    one the whole team did. What is averaged is the answers themselves.
    """
    given = sum(day.participation for day in answered)
    total = sum((day.average or 0) * day.participation for day in answered)
    mean = round(total / given, 1)
    return (
        f"Le moral est à {say.number(mean)} sur 5 sur la quinzaine, "
        f"sur {_answers(answered)} réparties sur "
        f"{len(answered)} {say.agreed('journée', len(answered))}, "
        f"dans une équipe de {report.headcount}."
    )


def _dips(answered: list[DayMoods]) -> list[str]:
    """The days that sat low, named as days and never as people."""
    dips = [day for day in answered if (day.average or 0) < DIP]
    if not dips:
        return []

    named = [say.day(day.day) for day in dips[:MOST_DIPS]]
    left = len(dips) - len(named)
    tail = f", et {left} autres" if left else ""
    return [
        f"{len(dips)} {say.agreed('journée', len(dips))} sous "
        f"{say.number(DIP)} sur 5 : {say.listed(named)}{tail}."
    ]


def _answers(days: list[DayMoods]) -> str:
    given = sum(day.participation for day in days)
    return f"{given} {say.agreed('réponse', given)}"
