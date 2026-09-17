"""Routes du referentiel des missions.

La creation et le changement de statut sont ouverts a toute l'equipe : le parti
pris est la confiance, la tracabilite est le garde-fou.
"""

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.projects.application.dtos.assignment_dto import AssignmentCommand
from src.modules.projects.application.dtos.project_dto import (
    ChangeProjectStatusCommand,
    CreateProjectCommand,
    DeleteProjectCommand,
    ImportProjectsCommand,
    MoveProjectCommand,
    ProjectImportLine,
    UpdateProjectCommand,
)
from src.modules.projects.application.dtos.update_dto import (
    EditUpdateCommand,
    PostUpdateCommand,
    RemoveUpdateCommand,
)
from src.modules.projects.application.use_cases.assign_member import (
    AssignMemberUseCase,
    UnassignMemberUseCase,
)
from src.modules.projects.application.use_cases.change_project_status import (
    ChangeProjectStatusUseCase,
)
from src.modules.projects.application.use_cases.create_project import (
    CreateProjectUseCase,
)
from src.modules.projects.application.use_cases.delete_project import (
    DeleteProjectUseCase,
)
from src.modules.projects.application.use_cases.get_board import GetBoardUseCase
from src.modules.projects.application.use_cases.get_project_detail import (
    GetProjectDetailUseCase,
)
from src.modules.projects.application.use_cases.import_projects import (
    ImportProjectsUseCase,
)
from src.modules.projects.application.use_cases.list_projects import ListProjectsUseCase
from src.modules.projects.application.use_cases.move_project import MoveProjectUseCase
from src.modules.projects.application.use_cases.project_updates import (
    EditProjectUpdateUseCase,
    ListProjectUpdatesUseCase,
    PostProjectUpdateUseCase,
    RemoveProjectUpdateUseCase,
)
from src.modules.projects.application.use_cases.update_project import (
    UpdateProjectUseCase,
)
from src.modules.projects.application.use_cases.update_project_detail import (
    AddLinkCommand,
    AddProjectLinkUseCase,
    RemoveProjectLinkUseCase,
    UpdateDescriptionCommand,
    UpdateDescriptionUseCase,
    UpdateProjectDetailCommand,
    UpdateProjectDetailUseCase,
)
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.presentation.api.mappers.project_mapper import (
    to_board_response,
    to_listed_project_response,
    to_project_detail_response,
    to_project_response,
    to_project_update_response,
)
from src.modules.projects.presentation.api.schemas.project_schemas import (
    AddLinkRequest,
    BoardResponse,
    ChangeStatusRequest,
    CreateProjectRequest,
    ImportProjectsRequest,
    ImportReportResponse,
    MoveProjectRequest,
    PostUpdateRequest,
    ProjectDetailResponse,
    ProjectLinkResponse,
    ProjectListItemResponse,
    ProjectResponse,
    ProjectUpdateResponse,
    UpdateDescriptionRequest,
    UpdateProjectDetailRequest,
    UpdateProjectRequest,
)
from src.modules.projects.presentation.dependencies import (
    get_add_project_link_use_case,
    get_assign_member_use_case,
    get_board_use_case,
    get_change_status_use_case,
    get_create_project_use_case,
    get_delete_project_use_case,
    get_edit_update_use_case,
    get_import_projects_use_case,
    get_list_projects_use_case,
    get_list_updates_use_case,
    get_move_project_use_case,
    get_post_update_use_case,
    get_project_detail_use_case,
    get_remove_project_link_use_case,
    get_remove_update_use_case,
    get_unassign_member_use_case,
    get_update_description_use_case,
    get_update_project_detail_use_case,
    get_update_project_use_case,
)
from src.modules.users.domain.entities.user import User

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get(
    "", response_model=list[ProjectListItemResponse], operation_id="listProjects"
)
async def list_projects(
    include_inactive: bool = Query(default=False),
    _: User = Depends(get_current_user),
    use_case: ListProjectsUseCase = Depends(get_list_projects_use_case),
) -> list[ProjectListItemResponse]:
    """Liste les missions du referentiel."""
    missions = await use_case.execute(include_inactive=include_inactive)
    return [to_listed_project_response(mission) for mission in missions]


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


@router.patch(
    "/{project_id}", response_model=ProjectResponse, operation_id="updateProject"
)
async def update_project(
    project_id: int,
    payload: UpdateProjectRequest,
    current_user: User = Depends(get_current_user),
    use_case: UpdateProjectUseCase = Depends(get_update_project_use_case),
    session: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Modifie une mission. Seuls les champs fournis sont appliques."""
    assert current_user.id is not None
    fournis = payload.model_dump(exclude_unset=True)
    project = await use_case.execute(
        UpdateProjectCommand(actor_id=current_user.id, project_id=project_id, **fournis)
    )
    await session.commit()
    return to_project_response(project)


@router.post(
    "/import",
    response_model=ImportReportResponse,
    operation_id="importProjects",
)
async def import_projects(
    payload: ImportProjectsRequest,
    current_user: User = Depends(get_current_user),
    use_case: ImportProjectsUseCase = Depends(get_import_projects_use_case),
    session: AsyncSession = Depends(get_db),
) -> ImportReportResponse:
    """Importe un referentiel de missions. Reserve aux managers."""
    assert current_user.id is not None
    rapport = await use_case.execute(
        ImportProjectsCommand(
            actor_id=current_user.id,
            lignes=[
                ProjectImportLine(**ligne.model_dump()) for ligne in payload.lignes
            ],
        )
    )
    await session.commit()
    return ImportReportResponse(
        crees=rapport.crees, ignores=rapport.ignores, erreurs=rapport.erreurs
    )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteProject",
)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    use_case: DeleteProjectUseCase = Depends(get_delete_project_use_case),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Supprime une mission jamais utilisee. Sinon, il faut l'archiver."""
    assert current_user.id is not None
    await use_case.execute(
        DeleteProjectCommand(actor_id=current_user.id, project_id=project_id)
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/board", response_model=BoardResponse, operation_id="getBoard")
async def get_board(
    _: User = Depends(get_current_user),
    use_case: GetBoardUseCase = Depends(get_board_use_case),
) -> BoardResponse:
    """Tableau de bord des projets, une colonne par phase."""
    return to_board_response(await use_case.execute())


@router.patch(
    "/{project_id}/move",
    response_model=ProjectResponse,
    operation_id="moveProject",
)
async def move_project(
    project_id: int,
    payload: MoveProjectRequest,
    current_user: User = Depends(get_current_user),
    use_case: MoveProjectUseCase = Depends(get_move_project_use_case),
    session: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Depose une carte dans une colonne, a un rang donne."""
    assert current_user.id is not None
    mission = await use_case.execute(
        MoveProjectCommand(
            actor_id=current_user.id,
            project_id=project_id,
            statut=payload.statut,
            position=payload.position,
        )
    )
    await session.commit()
    return to_project_response(mission)


@router.put(
    "/{project_id}/intervenants/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="assignMember",
)
async def assign_member(
    project_id: int,
    member_id: int,
    role: ProjectRole = Query(
        default=ProjectRole.INTERVENANT, description="A quel titre."
    ),
    current_user: User = Depends(get_current_user),
    use_case: AssignMemberUseCase = Depends(get_assign_member_use_case),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Declare qu'une personne intervient, ou va intervenir, sur la mission."""
    assert current_user.id is not None
    await use_case.execute(
        AssignmentCommand(
            actor_id=current_user.id,
            project_id=project_id,
            member_id=member_id,
            role=role,
        )
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{project_id}/intervenants/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="unassignMember",
)
async def unassign_member(
    project_id: int,
    member_id: int,
    role: ProjectRole = Query(
        default=ProjectRole.INTERVENANT, description="A quel titre."
    ),
    current_user: User = Depends(get_current_user),
    use_case: UnassignMemberUseCase = Depends(get_unassign_member_use_case),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Retire une personne des intervenants de la mission."""
    assert current_user.id is not None
    await use_case.execute(
        AssignmentCommand(
            actor_id=current_user.id,
            project_id=project_id,
            member_id=member_id,
            role=role,
        )
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{project_id}/detail",
    response_model=ProjectDetailResponse,
    operation_id="getProjectDetail",
)
async def get_project_detail(
    project_id: int,
    _: User = Depends(get_current_user),
    use_case: GetProjectDetailUseCase = Depends(get_project_detail_use_case),
) -> ProjectDetailResponse:
    """La fiche complete d'une mission."""
    return to_project_detail_response(await use_case.execute(project_id))


@router.put(
    "/{project_id}/detail",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="updateProjectDetail",
)
async def update_project_detail(
    project_id: int,
    payload: UpdateProjectDetailRequest,
    current_user: User = Depends(get_current_user),
    use_case: UpdateProjectDetailUseCase = Depends(get_update_project_detail_use_case),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Enregistre les departements concernes et les contacts metier."""
    assert current_user.id is not None
    await use_case.execute(
        UpdateProjectDetailCommand(
            actor_id=current_user.id,
            project_id=project_id,
            departements=payload.departements,
            contacts_metier=payload.contacts_metier,
        )
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{project_id}/liens",
    response_model=ProjectLinkResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="addProjectLink",
)
async def add_project_link(
    project_id: int,
    payload: AddLinkRequest,
    current_user: User = Depends(get_current_user),
    use_case: AddProjectLinkUseCase = Depends(get_add_project_link_use_case),
    session: AsyncSession = Depends(get_db),
) -> ProjectLinkResponse:
    """Attache un lien utile a la mission."""
    assert current_user.id is not None
    lien = await use_case.execute(
        AddLinkCommand(
            actor_id=current_user.id,
            project_id=project_id,
            label=payload.label,
            url=payload.url,
        )
    )
    await session.commit()
    assert lien.id is not None
    return ProjectLinkResponse(id=lien.id, label=lien.label, url=lien.url)


@router.delete(
    "/{project_id}/liens/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="removeProjectLink",
)
async def remove_project_link(
    project_id: int,
    link_id: int,
    _: User = Depends(get_current_user),
    use_case: RemoveProjectLinkUseCase = Depends(get_remove_project_link_use_case),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Detache un lien de la mission."""
    await use_case.execute(link_id)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/{project_id}/description",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="updateProjectDescription",
)
async def update_project_description(
    project_id: int,
    payload: UpdateDescriptionRequest,
    current_user: User = Depends(get_current_user),
    use_case: UpdateDescriptionUseCase = Depends(get_update_description_use_case),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Enregistre la fiche de service, en markdown."""
    assert current_user.id is not None
    await use_case.execute(
        UpdateDescriptionCommand(
            actor_id=current_user.id,
            project_id=project_id,
            description=payload.description,
        )
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{project_id}/updates",
    response_model=list[ProjectUpdateResponse],
    operation_id="listProjectUpdates",
)
async def list_project_updates(
    project_id: int,
    current_user: User = Depends(get_current_user),
    use_case: ListProjectUpdatesUseCase = Depends(get_list_updates_use_case),
) -> list[ProjectUpdateResponse]:
    """Le fil de suivi d'une mission, de la plus recente a la plus ancienne."""
    assert current_user.id is not None
    return [
        to_project_update_response(signee, current_user.id)
        for signee in await use_case.execute(project_id)
    ]


@router.post(
    "/{project_id}/updates",
    response_model=ProjectUpdateResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="postProjectUpdate",
)
async def post_project_update(
    project_id: int,
    payload: PostUpdateRequest,
    current_user: User = Depends(get_current_user),
    use_case: PostProjectUpdateUseCase = Depends(get_post_update_use_case),
    lecture: ListProjectUpdatesUseCase = Depends(get_list_updates_use_case),
    session: AsyncSession = Depends(get_db),
) -> ProjectUpdateResponse:
    """Publie une mise a jour sur la mission."""
    assert current_user.id is not None
    maj = await use_case.execute(
        PostUpdateCommand(
            actor_id=current_user.id, project_id=project_id, texte=payload.texte
        )
    )
    await session.commit()
    signee = next(s for s in await lecture.execute(project_id) if s.update.id == maj.id)
    return to_project_update_response(signee, current_user.id)


@router.put(
    "/{project_id}/updates/{update_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="editProjectUpdate",
)
async def edit_project_update(
    project_id: int,
    update_id: int,
    payload: PostUpdateRequest,
    current_user: User = Depends(get_current_user),
    use_case: EditProjectUpdateUseCase = Depends(get_edit_update_use_case),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Corrige une mise a jour. Seul son auteur le peut."""
    assert current_user.id is not None
    await use_case.execute(
        EditUpdateCommand(
            actor_id=current_user.id, update_id=update_id, texte=payload.texte
        )
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{project_id}/updates/{update_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="removeProjectUpdate",
)
async def remove_project_update(
    project_id: int,
    update_id: int,
    current_user: User = Depends(get_current_user),
    use_case: RemoveProjectUpdateUseCase = Depends(get_remove_update_use_case),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Retire une mise a jour. Elle garde sa place dans le fil."""
    assert current_user.id is not None
    await use_case.execute(
        RemoveUpdateCommand(actor_id=current_user.id, update_id=update_id)
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
