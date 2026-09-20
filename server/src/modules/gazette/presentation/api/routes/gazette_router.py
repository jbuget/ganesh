"""La Gazette routes.

Everyone reads a month, and everyone may ask for its digest: the facts come
from a register the whole team already has open, and reserving the gesture
would only mean waiting for somebody. What nobody can do is rewrite one —
asking again adds a version beside the last.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.auth.presentation.dependencies import get_current_user
from src.modules.gazette.application.dtos.gazette_dtos import (
    GenerateDigestCommand,
    ReadDigestQuery,
)
from src.modules.gazette.application.use_cases.generate_digest import (
    GenerateDigestUseCase,
)
from src.modules.gazette.application.use_cases.read_digest import ReadDigestUseCase
from src.modules.gazette.presentation.api.mappers.gazette_mapper import (
    to_digest_response,
)
from src.modules.gazette.presentation.api.schemas.gazette_schemas import (
    DigestResponse,
    GenerateDigestRequest,
)
from src.modules.gazette.presentation.dependencies import (
    get_generate_digest_use_case,
    get_read_digest_use_case,
)
from src.modules.users.domain.entities.user import User

router = APIRouter(prefix="/gazette", tags=["gazette"])


@router.get("", response_model=DigestResponse, operation_id="getDigest")
async def get_digest(
    month: date = Query(description="Any day of the month asked for"),
    version: int | None = Query(
        default=None,
        ge=1,
        description="Which generation to read. Defaults to the latest.",
    ),
    _: User = Depends(get_current_user),
    use_case: ReadDigestUseCase = Depends(get_read_digest_use_case),
) -> DigestResponse:
    """One month of the gazette.

    A month nobody has asked for yet reads straight from the register, with
    no chapeau: what a digest adds is a frozen copy, a date and a name.
    """
    return to_digest_response(
        await use_case.execute(ReadDigestQuery(month=month, version=version))
    )


@router.post(
    "",
    response_model=DigestResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="generateDigest",
)
async def generate_digest(
    payload: GenerateDigestRequest,
    current_user: User = Depends(get_current_user),
    use_case: GenerateDigestUseCase = Depends(get_generate_digest_use_case),
    session: AsyncSession = Depends(get_db),
) -> DigestResponse:
    """Reads a month out of the register and keeps it as a new version."""
    assert current_user.id is not None
    digest = await use_case.execute(
        GenerateDigestCommand(month=payload.month, actor_id=current_user.id)
    )
    await session.commit()
    return to_digest_response(digest)
