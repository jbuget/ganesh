"""Seeds the database: teammates, off-project activities and public holidays.

The script is idempotent: it can be replayed without creating a duplicate, and
it is the reference for who makes up the team — replayed on a database that
already knows someone, it brings their civil name and their department back in
line with what is written here.

Users are created without an Entra id. On the first sign-in, provisioning finds
them by their email and attaches their `oid`, which preserves the role handed
out here.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select

from src.core.database import AsyncSessionLocal
from src.modules.calendar.domain.services.working_days import (  # noqa: PLC2701
    _french_holidays,
)
from src.modules.calendar.infrastructure.database.models.holiday_model import (
    HolidayModel,
)
from src.modules.projects.domain.entities.project import ProjectKind
from src.modules.projects.infrastructure.database.models.project_model import (
    ProjectModel,
)
from src.modules.users.domain.entities.user import Role
from src.modules.users.infrastructure.database.models.user_model import UserModel
from src.shared.enums.department import Department

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("seed")


@dataclass(frozen=True)
class Teammate:
    """One line of the team reference list."""

    email: str
    first_name: str
    last_name: str
    role: Role = Role.TEAMMATE
    #: The whole team works in the information systems department today. The
    #: field stays per person: the day someone sits elsewhere, only their line
    #: changes.
    department: Department = Department.INFORMATION_SYSTEMS


#: Roles are handed out on creation only: one promoted from the screen keeps
#: what was given there, and a replay of this script does not take it back.
TEAM: list[Teammate] = [
    Teammate("j.buget@waat.fr", "Jérémy", "BUGET", Role.MANAGER),
    Teammate("f.lebreuilly@waat.fr", "Fabien", "LEBREUILLY", Role.MANAGER),
    Teammate("v.lestrat.ext@waat.fr", "Valentin", "LE STRAT", Role.MANAGER),
    Teammate("d.gourdon@waat.fr", "Damien", "GOURDON", Role.MANAGER),
    Teammate("sp.dobrzynski@waat.fr", "Sylvain-Pierre", "DOBRZYNSKI", Role.MANAGER),
    Teammate("te.bastiegermain@waat.fr", "Thibault-Enzo", "BASTIE-GERMAIN"),
    Teammate("a.hanane@waat.fr", "Adam", "HANANE"),
    Teammate("c.debray.ext@waat.fr", "Christopher", "DEBRAY"),
    Teammate("n.boulangeot@waat.fr", "Nathan", "BOULANGEOT"),
    Teammate("g.belhadj@waat.fr", "Ghouti", "BELHADJ"),
    Teammate("l.chen@waat.fr", "Lucas", "CHEN"),
    Teammate("l.watrelot.ext@waat.fr", "Laurène", "WATRELOT"),
    Teammate("l.nicolas.ext@waat.fr", "Laurent", "NICOLAS"),
    Teammate("n.garo.ext@waat.fr", "Nino", "GARO"),
    Teammate("t.vandemeulebroucke@waat.fr", "Thomas", "VANDEMEULEBROUCKE"),
    Teammate("n.taleb@waat.fr", "Nora", "TALEB"),
    Teammate("k.hocini@waat.fr", "Katia", "HOCINI"),
    Teammate("v.herrero@waat.fr", "Vincent", "HERRERO"),
    Teammate("d.dehe@waat.fr", "David", "DEHE"),
]

#: Addresses this script used to hand out, and what they should have been.
#:
#: An account is found by its email: without this, the correction would create
#: a second one beside the first rather than putting it right.
CORRECTED_EMAILS: dict[str, str] = {
    "n.boulangeaot@waat.fr": "n.boulangeot@waat.fr",
}

#: Without these rows, working days would spill over onto the projects and
#: what they consumed would read too high.
OFF_PROJECT_ACTIVITIES: list[str] = [
    "Absences (conges, RTT, maladie)",
    "Formation",
    "Interne / Reunions",
    "Avant-vente",
    "Support",
]

HOLIDAY_YEARS = (2026, 2027, 2028)


async def correct_emails() -> int:
    """Puts right the addresses handed out with a typo, before anything reads them."""
    corrected = 0
    async with AsyncSessionLocal() as session:
        for wrong, right in CORRECTED_EMAILS.items():
            found = await session.execute(
                select(UserModel).where(UserModel.email == wrong)
            )
            account = found.scalar_one_or_none()
            if account is None:
                continue
            # Unless the right address already exists, in which case the wrong
            # one is a duplicate nobody should be merging automatically.
            taken = await session.execute(
                select(UserModel).where(UserModel.email == right)
            )
            if taken.scalar_one_or_none() is not None:
                logger.warning(
                    "« %s » et « %s » coexistent : a traiter a la main.", wrong, right
                )
                continue
            account.email = right
            corrected += 1
        await session.commit()
    return corrected


async def seed_users() -> tuple[int, int]:
    """Creates who is missing, and brings back in line who has drifted."""
    created = 0
    updated = 0
    async with AsyncSessionLocal() as session:
        for teammate in TEAM:
            found = await session.execute(
                select(UserModel).where(UserModel.email == teammate.email)
            )
            account = found.scalar_one_or_none()

            if account is None:
                session.add(
                    UserModel(
                        entra_oid=None,
                        email=teammate.email,
                        # Entra will write its own on the first sign-in; until
                        # then the name read is the one given here.
                        display_name=f"{teammate.first_name} {teammate.last_name}",
                        role=teammate.role,
                        is_active=True,
                        first_name=teammate.first_name,
                        last_name=teammate.last_name,
                        department=teammate.department,
                    )
                )
                created += 1
                continue

            # The role and the access are left alone: they are given out from
            # the screen, and this script has no business taking them back.
            drifted = (
                account.first_name != teammate.first_name
                or account.last_name != teammate.last_name
                or account.department is not teammate.department
            )
            if drifted:
                account.first_name = teammate.first_name
                account.last_name = teammate.last_name
                account.department = teammate.department
                updated += 1

        await session.commit()
    return created, updated


async def seed_off_project_activities() -> int:
    created = 0
    async with AsyncSessionLocal() as session:
        for label in OFF_PROJECT_ACTIVITIES:
            existing = await session.execute(
                select(ProjectModel).where(
                    ProjectModel.label == label,
                    ProjectModel.kind == ProjectKind.OFF_PROJECT,
                )
            )
            if existing.scalar_one_or_none() is not None:
                continue
            session.add(
                ProjectModel(
                    label=label,
                    kind=ProjectKind.OFF_PROJECT,
                    status=None,
                    is_active=True,
                )
            )
            created += 1
        await session.commit()
    return created


async def seed_holidays() -> int:
    created = 0
    async with AsyncSessionLocal() as session:
        for year in HOLIDAY_YEARS:
            for day, label in _french_holidays(year).items():
                if await session.get(HolidayModel, day) is not None:
                    continue
                session.add(HolidayModel(day=day, label=label))
                created += 1
        await session.commit()
    return created


async def main() -> None:
    corrected = await correct_emails()
    created, updated = await seed_users()
    activities = await seed_off_project_activities()
    holidays = await seed_holidays()

    logger.info("Adresses corrigees          : %s", corrected)
    logger.info("Collaborateurs crees        : %s", created)
    logger.info("Collaborateurs mis a jour   : %s", updated)
    logger.info("Activites hors projet creees: %s", activities)
    logger.info("Jours feries crees          : %s", holidays)
    logger.info("Seed termine (%s).", date.today())


if __name__ == "__main__":
    asyncio.run(main())
