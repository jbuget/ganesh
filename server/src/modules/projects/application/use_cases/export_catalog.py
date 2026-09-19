"""The published missions, as the service catalogue reads them.

This is a projection, not a list: what comes out is shaped for waat.tools and
for nothing else. Everything a mission holds for steering — phase history,
cost, contacts, follow-up thread — stops at this boundary.
"""

from dataclasses import dataclass, field
from datetime import date

from src.modules.projects.domain.entities.project import Project, ProjectStatus
from src.modules.projects.domain.entities.project_link import ProjectLink
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.domain.repositories.project_assignee_repository import (
    ProjectAssigneeRepository,
)
from src.modules.projects.domain.repositories.project_detail_repository import (
    ProjectDetailRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.shared.utils.slugify import slugify

#: A service was first put in front of users when it reached deployment. A
#: mission that went straight to operations is dated from there instead.
FIRST_DEPLOYED_PHASES = (ProjectStatus.DEPLOYMENT, ProjectStatus.OPERATIONS)


@dataclass
class CatalogEntry:
    """One service, ready to be published."""

    slug: str
    name: str
    #: The one-line summary a catalogue card shows.
    description: str
    status: ProjectStatus
    #: The service left the referential: the catalogue says so rather than
    #: showing the phase it stopped at.
    archived: bool
    criticality: str
    service_type: str
    #: The full sheet, in markdown. The catalogue renders it.
    body: str | None = None

    production_link: str | None = None
    staging_link: str | None = None
    repository_link: str | None = None
    documentation_link: str | None = None
    project_management_link: str | None = None
    monitoring_link: str | None = None
    stats_page_link: str | None = None
    stats_api_link: str | None = None
    secondary_links: list[ProjectLink] = field(default_factory=list)

    first_deployed_at: date | None = None
    team: str | None = None
    slack_channel: str | None = None
    hosting: str | None = None
    has_microsoft_entra: bool = False
    #: Handles, derived from display names: the catalogue names people by the
    #: file that describes them.
    contributors: list[str] = field(default_factory=list)
    stack: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    #: Slugs of the services depended on, published ones only.
    depends_on: list[str] = field(default_factory=list)


class ExportCatalogUseCase:
    """Gathers the published missions, in the shape the catalogue expects.

    Only published missions are read, so the loop runs over a handful of rows
    rather than the whole reference list: asking for their collections one by
    one costs less than widening the ports for a build-time read.
    """

    def __init__(
        self,
        projects: ProjectRepository,
        details: ProjectDetailRepository,
        assignees: ProjectAssigneeRepository,
        users: UserRepository,
    ) -> None:
        self._projects = projects
        self._details = details
        self._assignees = assignees
        self._users = users

    async def execute(self) -> list[CatalogEntry]:
        published = [
            mission
            for mission in await self._projects.list_all(include_inactive=True)
            if mission.is_published and mission.id is not None
        ]

        # A dependency on something unpublished would draw a dead link on the
        # catalogue page: only what has an address of its own is kept.
        addresses = {
            mission.id: mission.slug
            for mission in published
            if mission.slug is not None
        }

        names = {
            user.id: user.display_name for user in await self._users.list_all(True)
        }
        leads = await self._assignees.list_all(ProjectRole.LEAD)
        contributors = await self._assignees.list_all(ProjectRole.CONTRIBUTOR)

        reached = {
            phase: await self._details.list_dates_reached(phase)
            for phase in FIRST_DEPLOYED_PHASES
        }

        entries = [
            await self._entry(mission, addresses, names, leads, contributors, reached)
            for mission in published
        ]
        return sorted(entries, key=lambda entry: entry.name.lower())

    async def _entry(
        self,
        mission: Project,
        addresses: dict[int | None, str],
        names: dict[int | None, str],
        leads: dict[int, list[int]],
        contributors: dict[int, list[int]],
        reached: dict[ProjectStatus, dict[int, date]],
    ) -> CatalogEntry:
        assert mission.id is not None
        assert mission.slug is not None
        assert mission.summary is not None
        assert mission.status is not None
        assert mission.criticality is not None
        assert mission.service_type is not None

        return CatalogEntry(
            slug=mission.slug,
            name=mission.label,
            description=mission.summary,
            status=mission.status,
            archived=not mission.is_active,
            criticality=mission.criticality.value,
            service_type=mission.service_type.value,
            body=mission.description,
            production_link=mission.production_link,
            staging_link=mission.staging_link,
            repository_link=mission.repository_link,
            documentation_link=mission.documentation_link,
            project_management_link=mission.project_management_link,
            monitoring_link=mission.monitoring_link,
            stats_page_link=mission.stats_page_link,
            stats_api_link=mission.stats_api_link,
            secondary_links=await self._details.list_links(mission.id),
            first_deployed_at=self._first_deployed_at(mission.id, reached),
            team=mission.team,
            slack_channel=mission.slack_channel,
            hosting=mission.hosting,
            has_microsoft_entra=mission.has_microsoft_entra,
            contributors=self._handles(mission.id, names, leads, contributors),
            stack=await self._details.list_stack(mission.id),
            tags=await self._details.list_tags(mission.id),
            depends_on=sorted(
                address
                for other_id in await self._details.list_dependencies(mission.id)
                if (address := addresses.get(other_id)) is not None
            ),
        )

    @staticmethod
    def _first_deployed_at(
        project_id: int, reached: dict[ProjectStatus, dict[int, date]]
    ) -> date | None:
        """The day the service first reached users, if it ever did."""
        dates = [
            reached[phase][project_id]
            for phase in FIRST_DEPLOYED_PHASES
            if project_id in reached[phase]
        ]
        return min(dates) if dates else None

    @staticmethod
    def _handles(
        project_id: int,
        names: dict[int | None, str],
        leads: dict[int, list[int]],
        contributors: dict[int, list[int]],
    ) -> list[str]:
        """Everyone attached to the mission, leads first, named by handle.

        The catalogue makes no difference between leading and contributing: it
        lists who is behind the service. Holding both roles still lists one.
        """
        ordered = leads.get(project_id, []) + contributors.get(project_id, [])
        handles = [
            slugify(names[user_id])
            for user_id in dict.fromkeys(ordered)
            if user_id in names
        ]
        return list(dict.fromkeys(handles))
