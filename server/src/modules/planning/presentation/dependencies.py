"""Wiring of the workload plan use case."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.entries.domain.repositories.entry_repository import EntryRepository
from src.modules.entries.presentation.dependencies import (
    get_entry_repository,
    get_project_repository,
    get_user_repository,
)
from src.modules.planning.application.use_cases.get_roadmap import GetRoadmapUseCase
from src.modules.planning.application.use_cases.get_workload_plan import (
    GetWorkloadPlanUseCase,
)
from src.modules.planning.application.use_cases.manage_simulations import (
    DeleteSimulationUseCase,
    ListSimulationsUseCase,
    SaveSimulationUseCase,
    UpdateSimulationUseCase,
)
from src.modules.planning.domain.repositories.simulation_repository import (
    SimulationRepository,
)
from src.modules.planning.infrastructure.database.repositories.simulation_repository_impl import (
    SqlSimulationRepository,
)
from src.modules.projects.domain.repositories.project_assignee_repository import (
    ProjectAssigneeRepository,
)
from src.modules.projects.domain.repositories.project_detail_repository import (
    ProjectDetailRepository,
)
from src.modules.projects.domain.repositories.project_repository import (
    ProjectRepository,
)
from src.modules.projects.presentation.dependencies import (
    get_project_assignee_repository,
    get_project_detail_repository,
)
from src.modules.users.domain.repositories.user_repository import UserRepository


def get_workload_plan_use_case(
    projects: ProjectRepository = Depends(get_project_repository),
    entries: EntryRepository = Depends(get_entry_repository),
    assignees: ProjectAssigneeRepository = Depends(get_project_assignee_repository),
    users: UserRepository = Depends(get_user_repository),
) -> GetWorkloadPlanUseCase:
    return GetWorkloadPlanUseCase(
        projects=projects, entries=entries, assignees=assignees, users=users
    )


def get_roadmap_use_case(
    projects: ProjectRepository = Depends(get_project_repository),
    entries: EntryRepository = Depends(get_entry_repository),
    details: ProjectDetailRepository = Depends(get_project_detail_repository),
    assignees: ProjectAssigneeRepository = Depends(get_project_assignee_repository),
    users: UserRepository = Depends(get_user_repository),
) -> GetRoadmapUseCase:
    return GetRoadmapUseCase(
        projects=projects,
        entries=entries,
        details=details,
        assignees=assignees,
        users=users,
    )


def get_simulation_repository(
    session: AsyncSession = Depends(get_db),
) -> SimulationRepository:
    return SqlSimulationRepository(session)


def get_list_simulations_use_case(
    simulations: SimulationRepository = Depends(get_simulation_repository),
) -> ListSimulationsUseCase:
    return ListSimulationsUseCase(simulations)


def get_save_simulation_use_case(
    simulations: SimulationRepository = Depends(get_simulation_repository),
) -> SaveSimulationUseCase:
    return SaveSimulationUseCase(simulations)


def get_update_simulation_use_case(
    simulations: SimulationRepository = Depends(get_simulation_repository),
) -> UpdateSimulationUseCase:
    return UpdateSimulationUseCase(simulations)


def get_delete_simulation_use_case(
    simulations: SimulationRepository = Depends(get_simulation_repository),
) -> DeleteSimulationUseCase:
    return DeleteSimulationUseCase(simulations)
