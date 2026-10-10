"""Places several teammates in one team, from the command line.

    python -m scripts.place_in_team ENGINEERING j.buget@waat.fr d.dehe@waat.fr

The screen places one person at a time; this places a whole team on the day
it is first said who is in it, without opening fifteen sheets.

Everything is checked before anything is written, and the whole list goes in
one transaction: a typo in the fifth address leaves the four before it
untouched, rather than a team half placed that nobody notices is half placed.

- An address it cannot find is refused, never created: an account made here
  would sit beside the one the person's first sign-in creates.
- An account filed under another department is refused: a team is only ever
  read under its own, and moving somebody across departments is a decision
  for their sheet, not a side effect of this list.
- An account with no department at all takes the team's: saying which team
  somebody is in says which department too.

It only ever adds: whoever is in the team and not on the list stays in it.
Running it twice changes nothing the second time.

Nothing is traced, for the reason `grant_role` traces nothing: the register
records who did what inside Ganesh, and this happened outside it.
"""

import asyncio
import logging
import sys

from sqlalchemy import select

from src.core.database import AsyncSessionLocal
from src.modules.users.infrastructure.database.models.user_model import UserModel
from src.shared.enums.team import Team

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("place_in_team")


def _name(model: UserModel) -> str:
    civil = " ".join(part for part in (model.first_name, model.last_name) if part)
    return f"{civil or model.display_name} <{model.email}>"


async def place(team: Team, emails: list[str]) -> int:
    wanted = list(dict.fromkeys(email.strip().lower() for email in emails))
    async with AsyncSessionLocal() as session:
        rows = (
            (
                await session.execute(
                    select(UserModel).where(UserModel.email.in_(wanted))
                )
            )
            .scalars()
            .all()
        )
        found = {model.email: model for model in rows}

        refusals = [
            f"Aucun compte pour « {email} »." for email in wanted if email not in found
        ]
        refusals += [
            f"{_name(model)} est rattaché au département "
            f"{model.department.value}, pas à {team.department.value}."
            for model in found.values()
            if model.department is not None and model.department is not team.department
        ]
        if refusals:
            for refusal in refusals:
                logger.error(refusal)
            logger.error("Rien n'a été écrit.")
            return 1

        for email in wanted:
            model = found[email]
            if model.team is team:
                logger.info("= %s, déjà dans %s", _name(model), team.value)
                continue
            if model.department is None:
                model.department = team.department
                logger.info(
                    "+ %s, département %s renseigné au passage",
                    _name(model),
                    team.department.value,
                )
            previous = model.team.value if model.team else "aucune équipe"
            model.team = team
            logger.info("→ %s : %s → %s", _name(model), previous, team.value)

        await session.commit()
        logger.info("%d compte(s) dans %s.", len(wanted), team.value)
        return 0


def main() -> int:
    if len(sys.argv) < 3:
        logger.error("Usage : python -m scripts.place_in_team <EQUIPE> <email>…")
        logger.error("Équipes : %s", ", ".join(team.name for team in Team))
        return 2
    raw, emails = sys.argv[1].upper(), sys.argv[2:]
    try:
        team = Team[raw]
    except KeyError:
        logger.error("Équipe inconnue : %s", raw)
        logger.error("Équipes : %s", ", ".join(team.name for team in Team))
        return 2
    return asyncio.run(place(team, emails))


if __name__ == "__main__":
    raise SystemExit(main())
