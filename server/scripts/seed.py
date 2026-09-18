"""Seeds the database: teammates, off-project activities and public holidays.

The script is idempotent: it can be replayed without creating a duplicate.

Users are created without an Entra id. On the first sign-in, provisioning finds
them by their email and attaches their `oid`, which preserves the role handed
out here.
"""

import asyncio
import logging
from datetime import date

from sqlalchemy import select

from src.core.database import AsyncSessionLocal
from src.modules.calendar.domain.services.working_days import (
    _french_holidays,  # noqa: PLC2701
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

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("seed")

TEAM: list[tuple[str, str, Role]] = [
    ("j.buget@waat.fr", "Jeremy Buget", Role.MANAGER),
    ("f.lebreuilly@waat.fr", "Fabien Lebreuilly", Role.MANAGER),
    ("v.lestrat.ext@waat.fr", "Valentin Le Strat", Role.MANAGER),
    ("d.dehe@waat.fr", "D. Dehe", Role.TEAMMATE),
    ("n.garo.ext@waat.fr", "N. Garo", Role.TEAMMATE),
    ("n.boulangeaot@waat.fr", "N. Boulangeaot", Role.TEAMMATE),
    ("l.chen@waat.fr", "L. Chen", Role.TEAMMATE),
    ("g.belhadj@waat.fr", "G. Belhadj", Role.TEAMMATE),
]

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


async def seed_users() -> int:
    created = 0
    async with AsyncSessionLocal() as session:
        for email, display_name, role in TEAM:
            existing = await session.execute(
                select(UserModel).where(UserModel.email == email)
            )
            if existing.scalar_one_or_none() is not None:
                continue
            session.add(
                UserModel(
                    entra_oid=None,
                    email=email,
                    display_name=display_name,
                    role=role,
                    is_active=True,
                )
            )
            created += 1
        await session.commit()
    return created


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
    users = await seed_users()
    activities = await seed_off_project_activities()
    holidays = await seed_holidays()

    logger.info("Collaborateurs crees        : %s", users)
    logger.info("Activites hors projet creees: %s", activities)
    logger.info("Jours feries crees          : %s", holidays)
    logger.info("Seed termine (%s).", date.today())


if __name__ == "__main__":
    asyncio.run(main())
