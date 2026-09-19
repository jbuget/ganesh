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
import json
import logging
import pathlib
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal
from src.modules.calendar.domain.services.working_days import (  # noqa: PLC2701
    _french_holidays,
)
from src.modules.calendar.infrastructure.database.models.holiday_model import (
    HolidayModel,
)
from src.modules.projects.domain.entities.project import (
    ProjectKind,
    ProjectPriority,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.domain.entities.service_registry import (
    Criticality,
    ServiceType,
)
from src.modules.projects.infrastructure.database.models.project_assignee_model import (
    ProjectAssigneeModel,
)
from src.modules.projects.infrastructure.database.models.project_detail_models import (
    ProjectStackModel,
    ProjectTagModel,
)
from src.modules.projects.infrastructure.database.models.project_model import (
    ProjectModel,
)
from src.modules.users.domain.entities.user import Role
from src.modules.users.infrastructure.database.models.user_model import UserModel
from src.shared.enums.department import Department

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("seed")

#: Where the reference data lives.
#:
#: The repository carries the script, never what it seeds: the team, the
#: missions and who works on them are the company's business, not the code's.
#: The directory is ignored by git, and each file is optional — what is not
#: there is simply not seeded.
DATA = pathlib.Path(__file__).parent / "data"
TEAM_FILE = DATA / "team.json"


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
    #: Addresses this person was handed before: an account is found by its
    #: email, so a typo corrected in the list alone would create a second
    #: account beside the first rather than putting it right.
    previous_emails: tuple[str, ...] = ()


def read_data(path: pathlib.Path, what: str) -> Any:
    """Reads one data file, or says plainly that it is not there.

    Each file is optional: what is not there is simply not seeded, and the
    script stays usable on a fresh clone that carries none of them.
    """
    if not path.exists():
        logger.warning("%s est absent : rien n'est fait pour %s.", path.name, what)
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_team() -> list[Teammate]:
    """Reads the team from the data file, which the repository does not carry.

    Who works here is the company's business, not the code's: the file stays
    out of the repository, and the script says so plainly when it is missing
    rather than seeding an empty team without a word.
    """
    rows = read_data(TEAM_FILE, "l'equipe")
    if rows is None:
        return []
    return [
        Teammate(
            email=row["email"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            role=Role(row.get("role", Role.TEAMMATE.value)),
            department=Department(
                row.get("department", Department.INFORMATION_SYSTEMS.value)
            ),
            previous_emails=tuple(row.get("previous_emails", ())),
        )
        for row in rows
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

#: The service sheets, drawn from the catalogue waat.tools publishes.
#:
#: They are the reverse of `make catalog`: the catalogue is exported from
#: Janus, so reading it back in is how Janus becomes the source it is meant to
#: be. The file is generated, then maintained by hand like any other reference.
SERVICES_FILE = DATA / "services.json"

#: What the steering board says of a mission, and nothing else.
#:
#: Monday holds the priority; the catalogue never did. A mission is found by
#: the board item it already carries — a label typed twice drifts, an id does
#: not — and by its label only when the rattachement is still to be made.
#:
#: « Indeterminé » on the board comes here as no priority at all: a mission
#: whose urgency has not been placed against the others says so by leaving the
#: field empty, which is exactly what the board means.
BOARD_FILE = DATA / "monday.json"

#: The wall the team reviews every week, as photographed.
#:
#: It says two things nothing else does: who has their hands on a mission right
#: now, and which column it sits in. The columns map onto the phases — a PoC is
#: still a framing exercise, so it lands on « cadrage » like the rest of
#: Discovery's right-hand side.
KANBAN_FILE = DATA / "kanban.json"

COLUMN_PHASES = {
    "idees": ProjectStatus.EXPLORATION,
    "cadrage": ProjectStatus.SCOPING,
    "delivery": ProjectStatus.DEVELOPMENT,
    "exploitation": ProjectStatus.OPERATIONS,
}

#: Sheet fields that go straight onto the mission, under the same name.
SHEET_FIELDS = (
    "summary",
    "description",
    "hosting",
    "team",
    "has_microsoft_entra",
    "production_link",
    "staging_link",
    "repository_link",
    "documentation_link",
    "project_management_link",
    "monitoring_link",
    "stats_page_link",
    "stats_api_link",
)


async def correct_emails(team: list[Teammate]) -> int:
    """Puts right the addresses handed out with a typo, before anything reads them."""
    corrected = 0
    async with AsyncSessionLocal() as session:
        for teammate in team:
            for wrong in teammate.previous_emails:
                right = teammate.email
                found = await session.execute(
                    select(UserModel).where(UserModel.email == wrong)
                )
                account = found.scalar_one_or_none()
                if account is None:
                    continue
                # Unless the right address already exists, in which case the
                # wrong one is a duplicate nobody should merge automatically.
                taken = await session.execute(
                    select(UserModel).where(UserModel.email == right)
                )
                if taken.scalar_one_or_none() is not None:
                    logger.warning(
                        "« %s » et « %s » coexistent : a traiter a la main.",
                        wrong,
                        right,
                    )
                    continue
                account.email = right
                corrected += 1
        await session.commit()
    return corrected


async def seed_users(team: list[Teammate]) -> tuple[int, int]:
    """Creates who is missing, and brings back in line who has drifted."""
    created = 0
    updated = 0
    async with AsyncSessionLocal() as session:
        for teammate in team:
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


async def _replace_collection(
    session: AsyncSession,
    model: type[ProjectStackModel] | type[ProjectTagModel],
    project_id: int,
    column: str,
    values: list[str],
) -> None:
    """Rewrites a mission's stack or tags, which are held as whole lists."""
    existing = await session.execute(
        select(model).where(model.project_id == project_id)
    )
    for row in existing.scalars().all():
        await session.delete(row)
    for value in values:
        session.add(model(project_id=project_id, **{column: value}))


async def seed_services() -> tuple[int, int]:
    """Creates the missions the catalogue knows of, and fills in their sheet.

    A mission is found by its label — the reference list has no other key a
    file written by hand could carry. What the sheet says wins: the catalogue
    is where these fields are maintained today.
    """
    created = 0
    filled = 0
    services = read_data(SERVICES_FILE, "les fiches service")
    if services is None:
        return 0, 0

    async with AsyncSessionLocal() as session:
        for service in services:
            found = await session.execute(
                select(ProjectModel).where(ProjectModel.label == service["label"])
            )
            mission = found.scalar_one_or_none()

            if mission is None:
                if not service["create"]:
                    logger.warning(
                        "« %s » est introuvable : fiche ignoree.", service["label"]
                    )
                    continue
                mission = ProjectModel(
                    label=service["label"], kind=ProjectKind.PROJECT, is_active=True
                )
                session.add(mission)
                await session.flush()
                created += 1
                is_new = True
            else:
                is_new = False

            for field in SHEET_FIELDS:
                if service.get(field) is not None:
                    setattr(mission, field, service[field])

            if service.get("slug"):
                mission.slug = service["slug"]
                # A sheet complete enough to have been published on waat.tools
                # is complete enough to be published from here.
                mission.is_published = True
            # Only on creation: the catalogue says what a service is, the wall
            # says how far its mission has got. Written on every run, the two
            # swapped the phase back and forth at each seed.
            if is_new and service.get("status"):
                mission.status = ProjectStatus(service["status"])
            if service.get("criticality"):
                mission.criticality = Criticality(service["criticality"])
            if service.get("service_type"):
                mission.service_type = ServiceType(service["service_type"])
            mission.is_active = service.get("is_active", True)

            await _replace_collection(
                session,
                ProjectStackModel,
                mission.id,
                "technology",
                service.get("stack", []),
            )
            await _replace_collection(
                session,
                ProjectTagModel,
                mission.id,
                "tag",
                service.get("tags", []),
            )
            filled += 1

        await session.commit()
    return created, filled


async def seed_board_fields() -> tuple[int, int]:
    """Brings over what the steering board holds: the rattachement, the priority."""
    attached = 0
    prioritised = 0
    rows = read_data(BOARD_FILE, "les priorites")
    if rows is None:
        return 0, 0

    async with AsyncSessionLocal() as session:
        for row in rows:
            found = await session.execute(
                select(ProjectModel).where(
                    ProjectModel.monday_item_id == row["monday_item_id"]
                )
            )
            mission = found.scalar_one_or_none()

            if mission is None:
                by_label = await session.execute(
                    select(ProjectModel).where(ProjectModel.label == row["label"])
                )
                mission = by_label.scalar_one_or_none()
                if mission is None:
                    logger.warning("« %s » est introuvable.", row["label"])
                    continue
                mission.monday_item_id = row["monday_item_id"]
                attached += 1

            if row["priority"] is not None:
                mission.priority = ProjectPriority(row["priority"])
                prioritised += 1

        await session.commit()
    return attached, prioritised


async def seed_kanban() -> tuple[int, int]:
    """Moves each mission to the column it sits in, and names who is on it.

    The contributors are replaced, not added to: the wall is a photograph of
    the moment, and someone who has left a mission left it.

    A lead is added and never removed. The wall carries no lead badge, so a
    card saying nothing about who answers for a mission is a card saying
    nothing — not a card saying « nobody ». Leads are named in review, and come
    here from there.
    """
    moved = 0
    assigned = 0
    board = read_data(KANBAN_FILE, "le kanban")
    if board is None:
        return 0, 0
    handles: dict[str, str] = board["handles"]

    async with AsyncSessionLocal() as session:
        people = {}
        for email in set(handles.values()):
            accounts = await session.execute(
                select(UserModel).where(UserModel.email == email)
            )
            account = accounts.scalar_one_or_none()
            if account is None:
                logger.warning("« %s » n'a pas de compte.", email)
                continue
            people[email] = account.id

        for card in board["cards"]:
            missions = await session.execute(
                select(ProjectModel).where(ProjectModel.label == card["label"])
            )
            mission = missions.scalar_one_or_none()
            if mission is None:
                logger.warning("« %s » est introuvable.", card["label"])
                continue

            phase = COLUMN_PHASES[card["column"]]
            if mission.status is not phase:
                mission.status = phase
                moved += 1

            wanted = {
                people[handles[handle]]
                for handle in card["contributors"]
                if handle in handles and handles[handle] in people
            }
            current = await session.execute(
                select(ProjectAssigneeModel).where(
                    ProjectAssigneeModel.project_id == mission.id,
                    ProjectAssigneeModel.role == ProjectRole.CONTRIBUTOR,
                )
            )
            for row in current.scalars().all():
                if row.user_id in wanted:
                    wanted.discard(row.user_id)
                else:
                    await session.delete(row)
            for user_id in wanted:
                session.add(
                    ProjectAssigneeModel(
                        project_id=mission.id,
                        user_id=user_id,
                        role=ProjectRole.CONTRIBUTOR,
                    )
                )
                assigned += 1

            for handle in card.get("leads", []):
                lead_email = handles.get(handle, "")
                if lead_email not in people:
                    continue
                held = await session.execute(
                    select(ProjectAssigneeModel).where(
                        ProjectAssigneeModel.project_id == mission.id,
                        ProjectAssigneeModel.user_id == people[lead_email],
                        ProjectAssigneeModel.role == ProjectRole.LEAD,
                    )
                )
                if held.scalar_one_or_none() is not None:
                    continue
                session.add(
                    ProjectAssigneeModel(
                        project_id=mission.id,
                        user_id=people[lead_email],
                        role=ProjectRole.LEAD,
                    )
                )
                assigned += 1

        await session.commit()
    return moved, assigned


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
    team = load_team()
    corrected = await correct_emails(team)
    created, updated = await seed_users(team)
    missions, sheets = await seed_services()
    attached, prioritised = await seed_board_fields()
    moved, assigned = await seed_kanban()
    activities = await seed_off_project_activities()
    holidays = await seed_holidays()

    logger.info("Adresses corrigees          : %s", corrected)
    logger.info("Collaborateurs crees        : %s", created)
    logger.info("Collaborateurs mis a jour   : %s", updated)
    logger.info("Missions creees             : %s", missions)
    logger.info("Fiches service remplies     : %s", sheets)
    logger.info("Missions reliees a Monday   : %s", attached)
    logger.info("Priorites posees            : %s", prioritised)
    logger.info("Missions deplacees de phase : %s", moved)
    logger.info("Intervenants affectes       : %s", assigned)
    logger.info("Activites hors projet creees: %s", activities)
    logger.info("Jours feries crees          : %s", holidays)
    logger.info("Seed termine (%s).", date.today())


if __name__ == "__main__":
    asyncio.run(main())
