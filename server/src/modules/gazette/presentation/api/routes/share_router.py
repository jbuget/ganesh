"""The links that open a digest to whoever holds them.

Three routes for the team and one for everybody. The team's open, list and
close the links, behind the doors the rest of the application uses. The last
is the only route of Ganesh that answers somebody who has not signed in with
anything of the register, and it answers with a narrative and no more: see
`PublicDigest`.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.auth.presentation.dependencies import get_contributor, get_current_user
from src.modules.gazette.application.dtos.gazette_dtos import (
    ListShareLinksQuery,
    ReadSharedDigestQuery,
    RevokeShareLinkCommand,
    ShareDigestCommand,
)
from src.modules.gazette.application.use_cases.list_share_links import (
    ListShareLinksUseCase,
)
from src.modules.gazette.application.use_cases.read_shared_digest import (
    ReadSharedDigestUseCase,
)
from src.modules.gazette.application.use_cases.revoke_share_link import (
    RevokeShareLinkUseCase,
)
from src.modules.gazette.application.use_cases.share_digest import ShareDigestUseCase
from src.modules.gazette.presentation.api.mappers.share_mapper import (
    to_public_digest_response,
    to_share_link_response,
)
from src.modules.gazette.presentation.api.schemas.gazette_schemas import (
    PublicDigestResponse,
    ShareDigestRequest,
    ShareLinkResponse,
)
from src.modules.gazette.presentation.dependencies import (
    get_list_share_links_use_case,
    get_read_shared_digest_use_case,
    get_revoke_share_link_use_case,
    get_share_digest_use_case,
)
from src.modules.users.domain.entities.user import User

router = APIRouter(prefix="/gazette", tags=["gazette"])

#: What the answer to the public route carries about being read.
#:
#: The token is in the address, so the address must not travel: without
#: `no-referrer` a link in a mail would hand its token to every site its page
#: loaded something from. The rest keeps a narrative that was meant for one
#: reader out of search engines and shared caches.
PUBLIC_HEADERS = {
    "X-Robots-Tag": "noindex, nofollow",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "private, no-store",
}


@router.post(
    "/share-links",
    response_model=ShareLinkResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="createShareLink",
)
async def create_share_link(
    payload: ShareDigestRequest,
    current_user: User = Depends(get_contributor),
    use_case: ShareDigestUseCase = Depends(get_share_digest_use_case),
    session: AsyncSession = Depends(get_db),
) -> ShareLinkResponse:
    """Opens a link on one version of a digest: its narrative, read-only."""
    assert current_user.id is not None
    view = await use_case.execute(
        ShareDigestCommand(
            month=payload.month, version=payload.version, actor_id=current_user.id
        )
    )
    await session.commit()
    return to_share_link_response(view)


@router.get(
    "/share-links",
    response_model=list[ShareLinkResponse],
    operation_id="listShareLinks",
)
async def list_share_links(
    month: date = Query(description="Any day of the month"),
    version: int = Query(ge=1, description="Which generation"),
    _: User = Depends(get_current_user),
    use_case: ListShareLinksUseCase = Depends(get_list_share_links_use_case),
) -> list[ShareLinkResponse]:
    """The links still open on a version, for the whole team to see."""
    views = await use_case.execute(ListShareLinksQuery(month=month, version=version))
    return [to_share_link_response(view) for view in views]


@router.delete(
    "/share-links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="revokeShareLink",
)
async def revoke_share_link(
    link_id: int,
    current_user: User = Depends(get_contributor),
    use_case: RevokeShareLinkUseCase = Depends(get_revoke_share_link_use_case),
    session: AsyncSession = Depends(get_db),
) -> None:
    """Closes a link. Anyone on the team may, whoever opened it."""
    assert current_user.id is not None
    await use_case.execute(
        RevokeShareLinkCommand(link_id=link_id, actor_id=current_user.id)
    )
    await session.commit()


@router.get(
    "/shared/{token}",
    response_model=PublicDigestResponse,
    operation_id="readSharedDigest",
)
async def read_shared_digest(
    token: str,
    response: Response,
    use_case: ReadSharedDigestUseCase = Depends(get_read_shared_digest_use_case),
) -> PublicDigestResponse:
    """What a link opens. No sign-in: the token is the whole of the right."""
    digest = await use_case.execute(ReadSharedDigestQuery(token=token))
    response.headers.update(PUBLIC_HEADERS)
    return to_public_digest_response(digest)
