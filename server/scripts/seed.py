"""Amorce la base : collaborateurs, activites hors projet et jours feries.

Le script est idempotent : il peut etre rejoue sans creer de doublon.

Les utilisateurs sont crees sans identifiant Entra. Au premier login, le
provisionnement les retrouve par leur email et leur rattache leur `oid`, ce qui
preserve le role pre-attribue ici.
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

#: Sans ces lignes, les jours ouvres se reporteraient sur les projets et le
#: consomme serait surevalue.
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
                    actif=True,
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
                    ProjectModel.kind == ProjectKind.HORS_PROJET,
                )
            )
            if existing.scalar_one_or_none() is not None:
                continue
            session.add(
                ProjectModel(
                    label=label,
                    kind=ProjectKind.HORS_PROJET,
                    statut=None,
                    actif=True,
                )
            )
            created += 1
        await session.commit()
    return created


async def seed_holidays() -> int:
    created = 0
    async with AsyncSessionLocal() as session:
        for year in HOLIDAY_YEARS:
            for jour, label in _french_holidays(year).items():
                if await session.get(HolidayModel, jour) is not None:
                    continue
                session.add(HolidayModel(jour=jour, label=label))
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
