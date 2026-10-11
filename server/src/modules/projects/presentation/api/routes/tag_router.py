"""Routes of the tags: put on a mission, and the vocabulary they make up.

Putting a tag on a mission and taking it off are open to everyone who may write
into Ganesh, like the rest of the reference list. Looking after the vocabulary —
renaming, recolouring, folding a duplicate into the tag it should have been —
is for managers: it moves every mission carrying the tag at once.
"""

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.auth.presentation.dependencies import (
    get_contributor,
    get_current_manager,
    get_current_user,
)
from src.modules.projects.application.dtos.tag_dto import (
    MergeTagsCommand,
    RecolorTagCommand,
    RenameTagCommand,
    TagProjectCommand,
    UntagProjectCommand,
)
from src.modules.projects.application.use_cases.manage_tags import (
    ListTagsUseCase,
    MergeTagsUseCase,
    RecolorTagUseCase,
    RenameTagUseCase,
)
from src.modules.projects.application.use_cases.tag_project import (
    TagProjectUseCase,
    UntagProjectUseCase,
)
from src.modules.projects.presentation.api.mappers.project_mapper import (
    to_tag_response,
    to_tag_usage_response,
)
from src.modules.projects.presentation.api.schemas.project_schemas import (
    MergeTagsRequest,
    RecolorTagRequest,
    RenameTagRequest,
    TagProjectRequest,
    TagResponse,
    TagUsageResponse,
)
from src.modules.projects.presentation.dependencies import (
    get_list_tags_use_case,
    get_merge_tags_use_case,
    get_recolor_tag_use_case,
    get_rename_tag_use_case,
    get_tag_project_use_case,
    get_untag_project_use_case,
)
from src.modules.users.domain.entities.user import User

router = APIRouter(tags=["tags"])


@router.get("/tags", response_model=list[TagUsageResponse], operation_id="listTags")
async def list_tags(
    search: str | None = Query(default=None, max_length=80),
    _: User = Depends(get_current_user),
    use_case: ListTagsUseCase = Depends(get_list_tags_use_case),
) -> list[TagUsageResponse]:
    """The tags in use, the closest to what was typed first.

    Without a search, every tag in use, the most carried first: the list a
    filter is drawn from.
    """
    return [to_tag_usage_response(usage) for usage in await use_case.execute(search)]


@router.post(
    "/projects/{project_id}/tags",
    response_model=TagResponse,
    operation_id="tagProject",
)
async def tag_project(
    project_id: int,
    body: TagProjectRequest,
    current_user: User = Depends(get_contributor),
    use_case: TagProjectUseCase = Depends(get_tag_project_use_case),
    session: AsyncSession = Depends(get_db),
) -> TagResponse:
    """Puts a tag on a mission, opening it if nobody had.

    The name is all it takes: « Chronopost » and « chronopost » are the same
    tag. Putting a tag the mission already carries changes nothing.
    """
    assert current_user.id is not None
    tag = await use_case.execute(
        TagProjectCommand(
            actor_id=current_user.id, project_id=project_id, name=body.name
        )
    )
    await session.commit()
    return to_tag_response(tag)


@router.delete(
    "/projects/{project_id}/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="untagProject",
)
async def untag_project(
    project_id: int,
    tag_id: int,
    current_user: User = Depends(get_contributor),
    use_case: UntagProjectUseCase = Depends(get_untag_project_use_case),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Takes a tag off a mission. The tag itself stays for the others."""
    assert current_user.id is not None
    await use_case.execute(
        UntagProjectCommand(
            actor_id=current_user.id, project_id=project_id, tag_id=tag_id
        )
    )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/tags/{tag_id}/rename", response_model=TagResponse, operation_id="renameTag"
)
async def rename_tag(
    tag_id: int,
    body: RenameTagRequest,
    current_user: User = Depends(get_current_manager),
    use_case: RenameTagUseCase = Depends(get_rename_tag_use_case),
    session: AsyncSession = Depends(get_db),
) -> TagResponse:
    """Renames a tag for every mission that carries it.

    Refused when another tag already says the same: fold this one into it.
    """
    assert current_user.id is not None
    tag = await use_case.execute(
        RenameTagCommand(actor_id=current_user.id, tag_id=tag_id, name=body.name)
    )
    await session.commit()
    return to_tag_response(tag)


@router.post(
    "/tags/{tag_id}/recolor", response_model=TagResponse, operation_id="recolorTag"
)
async def recolor_tag(
    tag_id: int,
    body: RecolorTagRequest,
    current_user: User = Depends(get_current_manager),
    use_case: RecolorTagUseCase = Depends(get_recolor_tag_use_case),
    session: AsyncSession = Depends(get_db),
) -> TagResponse:
    """Gives a tag another colour of the palette."""
    assert current_user.id is not None
    tag = await use_case.execute(
        RecolorTagCommand(actor_id=current_user.id, tag_id=tag_id, color=body.color)
    )
    await session.commit()
    return to_tag_response(tag)


@router.post(
    "/tags/{tag_id}/merge", response_model=TagResponse, operation_id="mergeTags"
)
async def merge_tags(
    tag_id: int,
    body: MergeTagsRequest,
    current_user: User = Depends(get_current_manager),
    use_case: MergeTagsUseCase = Depends(get_merge_tags_use_case),
    session: AsyncSession = Depends(get_db),
) -> TagResponse:
    """Folds a tag into another one. Answers with the tag that is kept."""
    assert current_user.id is not None
    tag = await use_case.execute(
        MergeTagsCommand(
            actor_id=current_user.id, source_id=tag_id, target_id=body.target_id
        )
    )
    await session.commit()
    return to_tag_response(tag)
