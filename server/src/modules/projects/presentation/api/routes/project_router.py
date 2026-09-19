"""Routes of the mission reference list.

Creating and changing status are open to the whole team: trust is the stance,
traceability the safeguard.
"""

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    MachineCaller,
)
from src.modules.api_keys.domain.entities.api_key import ApiKeyScope
from src.modules.api_keys.presentation.dependencies import require_scope
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.projects.application.dtos.assignment_dto import AssignmentCommand
from src.modules.projects.application.dtos.project_dto import (
    ArchiveProjectCommand,
    AttachProjectCommand,
    ChangeProjectStatusCommand,
    CreateProjectCommand,
    DeleteProjectCommand,
    DetachProjectCommand,
    ImportProjectsCommand,
    MoveProjectCommand,
    ProjectImportLine,
    UnarchiveProjectCommand,
    UpdateProjectCommand,
)
from src.modules.projects.application.dtos.update_dto import (
    EditUpdateCommand,
    PostUpdateCommand,
    RemoveUpdateCommand,
)
from src.modules.projects.application.use_cases.archive_project import (
    ArchiveProjectUseCase,
    UnarchiveProjectUseCase,
)
from src.modules.projects.application.use_cases.assign_member import (
    AssignMemberUseCase,
    UnassignMemberUseCase,
)
from src.modules.projects.application.use_cases.attach_project import (
    AttachProjectUseCase,
    DetachProjectUseCase,
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
from src.modules.projects.application.use_cases.export_catalog import (
    ExportCatalogUseCase,
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
from src.modules.projects.application.use_cases.update_project_registry import (
    UpdateProjectRegistryCommand,
    UpdateProjectRegistryUseCase,
)
from src.modules.projects.domain.entities.project_role import ProjectRole
from src.modules.projects.presentation.api.mappers.project_mapper import (
    to_board_response,
    to_catalog_entry_response,
    to_listed_project_response,
    to_project_detail_response,
    to_project_response,
    to_project_update_response,
)
from src.modules.projects.presentation.api.schemas.project_schemas import (
    AddLinkRequest,
    ArchiveProjectRequest,
    AttachProjectRequest,
    BoardResponse,
    CatalogEntryResponse,
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
    UpdateProjectRegistryRequest,
    UpdateProjectRequest,
)
from src.modules.projects.presentation.dependencies import (
    get_add_project_link_use_case,
    get_archive_project_use_case,
    get_assign_member_use_case,
    get_attach_project_use_case,
    get_board_use_case,
    get_change_status_use_case,
    get_create_project_use_case,
    get_delete_project_use_case,
    get_detach_project_use_case,
    get_edit_update_use_case,
    get_export_catalog_use_case,
    get_import_projects_use_case,
    get_list_projects_use_case,
    get_list_updates_use_case,
    get_move_project_use_case,
    get_post_update_use_case,
    get_project_detail_use_case,
    get_remove_project_link_use_case,
    get_remove_update_use_case,
    get_unarchive_project_use_case,
    get_unassign_member_use_case,
    get_update_description_use_case,
    get_update_project_detail_use_case,
    get_update_project_registry_use_case,
    get_update_project_use_case,
)
from src.modules.users.domain.entities.user import User

router = APIRouter(prefix="/projects", tags=["projects"])

#: Built once: a dependency is a value, and calling it in an argument default
#: would rebuild it on every import of this module.
catalog_reader = require_scope(ApiKeyScope.CATALOG_READ)


@router.get(
    "", response_model=list[ProjectListItemResponse], operation_id="listProjects"
)
async def list_projects(
    include_inactive: bool = Query(default=False),
    _: User = Depends(get_current_user),
    use_case: ListProjectsUseCase = Depends(get_list_projects_use_case),
) -> list[ProjectListItemResponse]:
    """Lists the missions in the reference list."""
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
    """Declares a new mission."""
    assert current_user.id is not None
    project = await use_case.execute(
        CreateProjectCommand(
            actor_id=current_user.id,
            label=payload.label,
            kind=payload.kind,
            status=payload.status,
            parent_id=payload.parent_id,
            estimated_days=payload.estimated_days,
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
    """Moves a mission to another phase."""
    assert current_user.id is not None
    project = await use_case.execute(
        ChangeProjectStatusCommand(
            actor_id=current_user.id, project_id=project_id, status=payload.status
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
    """Changes a mission. Only the fields provided are applied."""
    assert current_user.id is not None
    provided = payload.model_dump(exclude_unset=True)
    project = await use_case.execute(
        UpdateProjectCommand(
            actor_id=current_user.id, project_id=project_id, **provided
        )
    )
    await session.commit()
    return to_project_response(project)


@router.patch(
    "/{project_id}/parent",
    response_model=ProjectResponse,
    operation_id="attachProject",
)
async def attach_project(
    project_id: int,
    payload: AttachProjectRequest,
    current_user: User = Depends(get_current_user),
    use_case: AttachProjectUseCase = Depends(get_attach_project_use_case),
    session: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Makes a mission a work package of another project."""
    assert current_user.id is not None
    mission = await use_case.execute(
        AttachProjectCommand(
            actor_id=current_user.id,
            project_id=project_id,
            parent_id=payload.parent_id,
        )
    )
    await session.commit()
    return to_project_response(mission)


@router.delete(
    "/{project_id}/parent",
    response_model=ProjectResponse,
    operation_id="detachProject",
)
async def detach_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    use_case: DetachProjectUseCase = Depends(get_detach_project_use_case),
    session: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Makes a work package a project of its own again."""
    assert current_user.id is not None
    mission = await use_case.execute(
        DetachProjectCommand(actor_id=current_user.id, project_id=project_id)
    )
    await session.commit()
    return to_project_response(mission)


@router.post(
    "/{project_id}/archive",
    response_model=ProjectResponse,
    operation_id="archiveProject",
)
async def archive_project(
    project_id: int,
    payload: ArchiveProjectRequest,
    current_user: User = Depends(get_current_user),
    use_case: ArchiveProjectUseCase = Depends(get_archive_project_use_case),
    session: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Takes a mission out of the reference list, without losing anything.

    A project cut into packages says what becomes of them in the same breath:
    archiving is not an edit of one field, it is a gesture that reaches what
    hangs from the mission.
    """
    assert current_user.id is not None
    mission = await use_case.execute(
        ArchiveProjectCommand(
            actor_id=current_user.id,
            project_id=project_id,
            sub_projects=payload.sub_projects,
        )
    )
    await session.commit()
    return to_project_response(mission)


@router.post(
    "/{project_id}/unarchive",
    response_model=ProjectResponse,
    operation_id="unarchiveProject",
)
async def unarchive_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    use_case: UnarchiveProjectUseCase = Depends(get_unarchive_project_use_case),
    session: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Puts a mission back into the reference list. It comes back on its own."""
    assert current_user.id is not None
    mission = await use_case.execute(
        UnarchiveProjectCommand(actor_id=current_user.id, project_id=project_id)
    )
    await session.commit()
    return to_project_response(mission)


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
    """Imports a mission reference list. Managers only."""
    assert current_user.id is not None
    report = await use_case.execute(
        ImportProjectsCommand(
            actor_id=current_user.id,
            rows=[ProjectImportLine(**line.model_dump()) for line in payload.rows],
        )
    )
    await session.commit()
    return ImportReportResponse(
        created=report.created, skipped=report.skipped, errors=report.errors
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
    """Deletes a mission never used. Otherwise, it must be archived."""
    assert current_user.id is not None
    await use_case.execute(
        DeleteProjectCommand(actor_id=current_user.id, project_id=project_id)
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/catalog",
    response_model=list[CatalogEntryResponse],
    operation_id="exportCatalog",
)
async def export_catalog(
    _: MachineCaller = Depends(catalog_reader),
    use_case: ExportCatalogUseCase = Depends(get_export_catalog_use_case),
) -> list[CatalogEntryResponse]:
    """The published services, in the vocabulary of the public catalogue.

    The one route a machine may reach in V1. It asks for `catalog:read` and
    nothing else opens by accident: every other route still depends on
    `get_current_user`, which turns keys away.
    """
    return [to_catalog_entry_response(entry) for entry in await use_case.execute()]


@router.get("/board", response_model=BoardResponse, operation_id="getBoard")
async def get_board(
    include_inactive: bool = Query(default=False),
    _: User = Depends(get_current_user),
    use_case: GetBoardUseCase = Depends(get_board_use_case),
) -> BoardResponse:
    """Project board, one column per phase."""
    return to_board_response(await use_case.execute(include_inactive=include_inactive))


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
    """Drops a card into a column, at a given rank."""
    assert current_user.id is not None
    mission = await use_case.execute(
        MoveProjectCommand(
            actor_id=current_user.id,
            project_id=project_id,
            status=payload.status,
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
        default=ProjectRole.CONTRIBUTOR, description="A quel titre."
    ),
    current_user: User = Depends(get_current_user),
    use_case: AssignMemberUseCase = Depends(get_assign_member_use_case),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Declares that someone is working, or about to work, on the mission."""
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
        default=ProjectRole.CONTRIBUTOR, description="A quel titre."
    ),
    current_user: User = Depends(get_current_user),
    use_case: UnassignMemberUseCase = Depends(get_unassign_member_use_case),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Removes someone from the mission's contributors."""
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
    """The full sheet of a mission."""
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
    """Saves the departments concerned and the business contacts."""
    assert current_user.id is not None
    await use_case.execute(
        UpdateProjectDetailCommand(
            actor_id=current_user.id,
            project_id=project_id,
            departments=payload.departments,
            business_contacts=payload.business_contacts,
        )
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/{project_id}/registry",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="updateProjectRegistry",
)
async def update_project_registry(
    project_id: int,
    payload: UpdateProjectRegistryRequest,
    current_user: User = Depends(get_current_user),
    use_case: UpdateProjectRegistryUseCase = Depends(
        get_update_project_registry_use_case
    ),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Saves the stack, the tags and the dependencies of the service."""
    assert current_user.id is not None
    await use_case.execute(
        UpdateProjectRegistryCommand(
            actor_id=current_user.id,
            project_id=project_id,
            stack=payload.stack,
            tags=payload.tags,
            depends_on=payload.depends_on,
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
    """Attaches a useful link to the mission."""
    assert current_user.id is not None
    link = await use_case.execute(
        AddLinkCommand(
            actor_id=current_user.id,
            project_id=project_id,
            label=payload.label,
            url=payload.url,
            icon=payload.icon,
        )
    )
    await session.commit()
    assert link.id is not None
    return ProjectLinkResponse(
        id=link.id, label=link.label, url=link.url, icon=link.icon
    )


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
    """Detaches a link from the mission."""
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
    """Saves the service sheet, in markdown."""
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
    """A mission's follow-up thread, most recent first."""
    assert current_user.id is not None
    return [
        to_project_update_response(signed, current_user.id)
        for signed in await use_case.execute(project_id)
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
    list_updates: ListProjectUpdatesUseCase = Depends(get_list_updates_use_case),
    session: AsyncSession = Depends(get_db),
) -> ProjectUpdateResponse:
    """Posts an update on the mission."""
    assert current_user.id is not None
    update = await use_case.execute(
        PostUpdateCommand(
            actor_id=current_user.id, project_id=project_id, body=payload.body
        )
    )
    await session.commit()
    signed = next(
        s for s in await list_updates.execute(project_id) if s.update.id == update.id
    )
    return to_project_update_response(signed, current_user.id)


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
    """Corrects an update. Only its author may."""
    assert current_user.id is not None
    await use_case.execute(
        EditUpdateCommand(
            actor_id=current_user.id, update_id=update_id, body=payload.body
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
    """Withdraws an update. It keeps its place in the thread."""
    assert current_user.id is not None
    await use_case.execute(
        RemoveUpdateCommand(actor_id=current_user.id, update_id=update_id)
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
