"""Routes du referentiel des missions.

La creation et le changement de statut sont ouverts a toute l'equipe : le parti
pris est la confiance, la tracabilite est le garde-fou.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.projects.application.dtos.project_dto import (
    ChangeProjectStatusCommand,
    CreateProjectCommand,
)
from src.modules.projects.application.use_cases.change_project_status import (
    ChangeProjectStatusUseCase,
)
from src.modules.projects.application.use_cases.create_project import (
    CreateProjectUseCase,
)
from src.modules.projects.application.use_cases.list_projects import ListProjectsUseCase
from src.modules.projects.presentation.api.mappers.project_mapper import (
    to_project_response,
)
from src.modules.projects.presentation.api.schemas.project_schemas import (
    ChangeStatusRequest,
    CreateProjectRequest,
    ProjectResponse,
)
from src.modules.projects.presentation.dependencies import (
    get_change_status_use_case,
    get_create_project_use_case,
    get_list_projects_use_case,
)
from src.modules.users.domain.entities.user import User

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse], operation_id="listProjects")
async def list_projects(
    include_inactive: bool = Query(default=False),
    _: User = Depends(get_current_user),
    use_case: ListProjectsUseCase = Depends(get_list_projects_use_case),
) -> list[ProjectResponse]:
    """Liste les missions du referentiel."""
    projects = await use_case.execute(include_inactive=include_inactive)
    return [to_project_response(project) for project in projects]


@router.post(
    "", response_model=ProjectResponse, status_code=201, operation_id="createProject"
)
async def create_project(
    payload: CreateProjectRequest,
    current_user: User = Depends(get_current_user),
    use_case: CreateProjectUseCase = Depends(get_create_project_use_case),
    session: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Declare une nouvelle mission."""
    assert current_user.id is not None
    project = await use_case.execute(
        CreateProjectCommand(
            actor_id=current_user.id,
            label=payload.label,
            kind=payload.kind,
            statut=payload.statut,
            parent_id=payload.parent_id,
            estime_j=payload.estime_j,
        )
    )
    await session.commit()
    return to_project_response(project)


@router.patch(
    "/{project_id}/status",
    response_model=ProjectResponse,
    operation_id="changeProjectStatus",
)
async def change_status(
    project_id: int,
    payload: ChangeStatusRequest,
    current_user: User = Depends(get_current_user),
    use_case: ChangeProjectStatusUseCase = Depends(get_change_status_use_case),
    session: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Fait changer la phase d'une mission."""
    assert current_user.id is not None
    project = await use_case.execute(
        ChangeProjectStatusCommand(
            actor_id=current_user.id, project_id=project_id, statut=payload.statut
        )
    )
    await session.commit()
    return to_project_response(project)
