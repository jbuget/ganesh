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
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal
from src.modules.calendar.domain.services.working_days import (
    DayKind,
    _french_holidays,
    classify_day,
)
from src.modules.calendar.infrastructure.database.models.holiday_model import (
    HolidayModel,
)
from src.modules.moods.domain.entities.mood import MoodLevel
from src.modules.moods.infrastructure.database.models.mood_model import MoodModel
from src.modules.projects.domain.entities.project import (
    ProjectCategory,
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
from src.modules.projects.infrastructure.database.models.project_update_model import (
    ProjectUpdateModel,
)
from src.modules.users.domain.entities.user import Role
from src.modules.users.infrastructure.database.models.user_model import UserModel
from src.shared.enums.department import Department
from src.shared.enums.org_level import OrgLevel

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
    #: Their handle on GitHub, which is where their contributions are found.
    github_username: str | None = None
    #: Where they sit in the company. Said here for whoever has to be told
    #: apart before they ever sign in — the members of the COMEX a need is
    #: carried to have to be in the picker on the day the recueil opens, and
    #: an account nobody can create from a screen has to come from somewhere.
    org_level: OrgLevel | None = None
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
            github_username=row.get("github_username"),
            org_level=(
                OrgLevel(row["org_level"]) if row.get("org_level") else None
            ),
            previous_emails=tuple(row.get("previous_emails", ())),
        )
        for row in rows
    ]


#: Without these rows, working days would spill over onto the projects and
#: what they consumed would read too high.
@dataclass(frozen=True)
class OffProjectActivity:
    """One line of work that belongs to no mission.

    These rows exist so that working days do not spill over onto the projects,
    which would read as time they never consumed. They are few on purpose: the
    finer the list, the more filling it becomes an exercise in classification,
    and the less the figure means.
    """

    label: str
    #: Labels this activity was given before. An activity is found by its
    #: label: renaming it in the list alone would add a second one beside the
    #: first rather than putting it right.
    previous_labels: tuple[str, ...] = ()


OFF_PROJECT_ACTIVITIES: list[OffProjectActivity] = [
    OffProjectActivity(
        "Absences (congés, RTT, maladie)", ("Absences (conges, RTT, maladie)",)
    ),
    OffProjectActivity("Formation"),
    OffProjectActivity(
        "Évènementiel / communication",
        # Every label this line has worn, so a database left behind is caught
        # up rather than given a second row beside the first.
        ("Interne / Reunions", "Interne / Réunions"),
    ),
    OffProjectActivity("Avant-vente / relation partenaire", ("Avant-vente",)),
    OffProjectActivity("Management / pilotage", ("Management / encadrement",)),
    OffProjectActivity("Recrutement / intégration"),
    OffProjectActivity("Support"),
]

HOLIDAY_YEARS = (2026, 2027, 2028)

#: How far back the seeded moods go, in calendar days.
MOOD_WINDOW = 20

#: How a teammate answers, and where their days sit on the scale.
#:
#: Three of them, cycled over the team in order: a morale screen is only worth
#: looking at once the silences are uneven, and everyone answering every day
#: would make participation say nothing.
#:
#: `answers` is how often the day gets an answer at all; `centre` is where that
#: person's days fall on the 1-to-5 scale, and `spread` how far they wander
#: from it. Nobody is centred on 3: a team where every temperament is the same
#: draws a flat chart.
MOOD_PROFILES: tuple[tuple[str, float, float, float], ...] = (
    ("assidu", 0.9, 3.8, 0.8),
    ("irregulier", 0.4, 3.1, 1.1),
    ("silencieux", 0.08, 2.9, 1.0),
)

#: The same draw every time the seed runs, so replaying it adds nothing and
#: two developers describe the same screen.
MOOD_SEED = 20260919

#: How much a day weighs on everybody at once. Without it each person wanders
#: on their own, the means all land near the middle, and the trend line comes
#: out flat — where a team actually has good weeks and bad ones.
MOOD_WEATHER = 0.6

#: The service sheets, drawn from the catalogue waat.tools publishes.
#:
#: They are the reverse of `make catalog`: the catalogue is exported from
#: Ganesh, so reading it back in is how Ganesh becomes the source it is meant to
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

#: What was said on a mission on the board, brought over to its thread.
#:
#: Monday nests replies under the update they answer; the thread here is flat
#: and ordered by time, so a reply comes over as a message of its own, at the
#: moment it was written. Nothing is lost, and the thread reads in the order it
#: was spoken.
UPDATES_FILE = DATA / "updates.json"

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
                        github_username=teammate.github_username,
                        org_level=teammate.org_level,
                    )
                )
                created += 1
                continue

            # The role and the access are left alone: they are given out from
            # the screen, and this script has no business taking them back.
            # The handle and the level are only ever added: a list that says
            # nothing about someone's GitHub account, or about where they sit,
            # does not say they have neither.
            drifted = (
                account.first_name != teammate.first_name
                or account.last_name != teammate.last_name
                or account.department is not teammate.department
                or (
                    teammate.github_username is not None
                    and account.github_username != teammate.github_username
                )
                or (
                    teammate.org_level is not None
                    and account.org_level is not teammate.org_level
                )
            )
            if drifted:
                account.first_name = teammate.first_name
                account.last_name = teammate.last_name
                account.department = teammate.department
                if teammate.github_username is not None:
                    account.github_username = teammate.github_username
                if teammate.org_level is not None:
                    account.org_level = teammate.org_level
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
    """Brings over what the steering board holds, and it alone.

    Priority, strategic axis and estimate are maintained on the board and
    nowhere else — unlike the phase, which the wall carries. What the board
    leaves empty is left alone here: it says nothing, it does not say « none ».
    """
    attached = 0
    filled = 0
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

            # Counted only when it changes something: every other line of the
            # report reads as « what moved », and a replay must show zeros.
            changed = False
            priority = ProjectPriority(row["priority"]) if row["priority"] else None
            if priority is not None and mission.priority is not priority:
                mission.priority = priority
                changed = True

            category = ProjectCategory(row["category"]) if row.get("category") else None
            if category is not None and mission.category is not category:
                mission.category = category
                changed = True

            estimate = row.get("estimated_days")
            if estimate is not None and mission.estimated_days != estimate:
                mission.estimated_days = estimate
                changed = True

            if changed:
                filled += 1

        await session.commit()
    return attached, filled


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


async def seed_updates() -> tuple[int, int]:
    """Posts on each mission what was said about it on the board.

    An update is recognised by its mission, its author and the moment it was
    published: Monday's own id has nowhere to live here, and no two people
    write on the same mission in the same second.
    """
    posted = 0
    orphans = 0
    rows = read_data(UPDATES_FILE, "les mises a jour")
    if rows is None:
        return 0, 0

    async with AsyncSessionLocal() as session:
        authors: dict[str, int] = {}
        for email in {row["author_email"] for row in rows}:
            found = await session.execute(
                select(UserModel).where(UserModel.email == email)
            )
            account = found.scalar_one_or_none()
            if account is not None:
                authors[email] = account.id

        for row in rows:
            missions = await session.execute(
                select(ProjectModel).where(
                    ProjectModel.monday_item_id == row["monday_item_id"]
                )
            )
            mission = missions.scalar_one_or_none()
            if mission is None or row["author_email"] not in authors:
                orphans += 1
                continue

            published_at = datetime.fromisoformat(row["published_at"])
            author_id = authors[row["author_email"]]
            already = await session.execute(
                select(ProjectUpdateModel).where(
                    ProjectUpdateModel.project_id == mission.id,
                    ProjectUpdateModel.author_id == author_id,
                    ProjectUpdateModel.published_at == published_at,
                )
            )
            if already.scalar_one_or_none() is not None:
                continue

            session.add(
                ProjectUpdateModel(
                    project_id=mission.id,
                    author_id=author_id,
                    body=row["body"],
                    published_at=published_at,
                )
            )
            posted += 1

        await session.commit()
    return posted, orphans


async def seed_off_project_activities() -> tuple[int, int]:
    """Creates what is missing, and renames what has been renamed."""
    created = 0
    renamed = 0
    async with AsyncSessionLocal() as session:
        for activity in OFF_PROJECT_ACTIVITIES:
            found = await session.execute(
                select(ProjectModel).where(
                    ProjectModel.label.in_((activity.label, *activity.previous_labels)),
                    ProjectModel.kind == ProjectKind.OFF_PROJECT,
                )
            )
            rows = list(found.scalars().all())

            if not rows:
                session.add(
                    ProjectModel(
                        label=activity.label,
                        kind=ProjectKind.OFF_PROJECT,
                        status=None,
                        is_active=True,
                    )
                )
                created += 1
                continue

            # Renaming, never duplicating: the entries already booked against
            # the old label stay where they are, under the new one.
            for row in rows:
                if row.label != activity.label:
                    row.label = activity.label
                    renamed += 1

        await session.commit()
    return created, renamed


async def seed_moods() -> int:
    """Fills the last working days with moods, for the morale screen.

    Dev data, like everything else here: the moods are drawn, not collected,
    and they carry the names of real teammates. Never run this script against
    anything but a development database.

    Working days only, because the domain refuses the rest: seeding a Sunday
    would write a row the API itself could never have produced, and which no
    screen would ever show.

    A day someone has already answered for is left alone: what a person said
    about their own day is not something a seed gets to overwrite.
    """
    levels = list(MoodLevel)
    rng = random.Random(MOOD_SEED)
    today = date.today()
    days = [
        day
        for offset in range(MOOD_WINDOW)
        if classify_day(day := today - timedelta(days=offset)) is DayKind.WORKING
    ]
    weather = {day: rng.gauss(0, MOOD_WEATHER) for day in days}

    created = 0
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserModel.id).where(UserModel.is_active).order_by(UserModel.id)
        )
        # Deactivated teammates are left out: they are no longer expected to
        # answer, and the screen counts them nowhere.
        people = list(result.scalars().all())

        for rank, user_id in enumerate(people):
            _, answers, centre, spread = MOOD_PROFILES[rank % len(MOOD_PROFILES)]

            for day in days:
                # Both draws happen whatever the database already holds. Skipping
                # one of them on a day that is taken would shift every draw that
                # follows, and replaying the seed would answer for other days than
                # the first run did — which is exactly what it did before.
                answered = rng.random() <= answers
                score = round(rng.gauss(centre, spread) + weather[day])
                if not answered:
                    continue

                taken = await session.execute(
                    select(MoodModel.id).where(
                        MoodModel.user_id == user_id, MoodModel.day == day
                    )
                )
                if taken.scalar_one_or_none() is not None:
                    continue

                level = levels[min(len(levels), max(1, score)) - 1]
                session.add(MoodModel(user_id=user_id, day=day, level=level))
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
    attached, filled = await seed_board_fields()
    moved, assigned = await seed_kanban()
    posted, orphans = await seed_updates()
    activities, renamed = await seed_off_project_activities()
    holidays = await seed_holidays()
    moods = await seed_moods()

    logger.info("Adresses corrigees          : %s", corrected)
    logger.info("Collaborateurs crees        : %s", created)
    logger.info("Collaborateurs mis a jour   : %s", updated)
    logger.info("Missions creees             : %s", missions)
    logger.info("Fiches service remplies     : %s", sheets)
    logger.info("Missions reliees a Monday   : %s", attached)
    logger.info("Missions renseignees        : %s", filled)
    logger.info("Missions deplacees de phase : %s", moved)
    logger.info("Intervenants affectes       : %s", assigned)
    logger.info("Mises a jour publiees       : %s", posted)
    logger.info("Mises a jour sans mission   : %s", orphans)
    logger.info("Activites hors projet creees: %s", activities)
    logger.info("Activites renommees         : %s", renamed)
    logger.info("Jours feries crees          : %s", holidays)
    logger.info("Moraux tires au sort        : %s", moods)
    logger.info("Seed termine (%s).", date.today())


if __name__ == "__main__":
    asyncio.run(main())
