"""Request routes.

The one corner of the application a requester reaches. Every route here
depends on `get_signed_in_user` rather than on `get_current_user`: the door of
the application turns a requester away, and these say, one at a time and on
purpose, that they are meant for them too.

What each of them lets anybody do is not decided here: the request itself
says who may write it, hand it over or take it back, and the route only
passes on who is asking.
"""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.auth.presentation.dependencies import get_signed_in_user
from src.modules.requests.application.dtos.request_dto import (
    ConvertRequestCommand,
    DecideRequestCommand,
    FileRequestCommand,
    FillInRequestCommand,
)
from src.modules.requests.application.use_cases.convert_request import (
    ConvertRequestUseCase,
)
from src.modules.requests.application.use_cases.decide_request import (
    DecideRequestUseCase,
)
from src.modules.requests.application.use_cases.delete_request import (
    DeleteRequestUseCase,
)
from src.modules.requests.application.use_cases.file_request import FileRequestUseCase
from src.modules.requests.application.use_cases.fill_in_request import (
    FillInRequestUseCase,
)
from src.modules.requests.application.use_cases.read_requests import (
    GetRequestUseCase,
    ListMyRequestsUseCase,
    ListRequestsUseCase,
    ListSponsorsUseCase,
)
from src.modules.requests.application.use_cases.submit_request import (
    SubmitRequestUseCase,
)
from src.modules.requests.application.use_cases.withdraw_request import (
    WithdrawRequestUseCase,
)
from src.modules.requests.presentation.api.mappers.request_mapper import (
    to_request_response,
    to_sponsor_response,
)
from src.modules.requests.presentation.api.schemas.request_schemas import (
    ConvertRequestRequest,
    DecideRequestRequest,
    FileRequestRequest,
    FillInRequestRequest,
    RequestPersonResponse,
    RequestResponse,
)
from src.modules.requests.presentation.dependencies import (
    get_convert_request_use_case,
    get_decide_request_use_case,
    get_delete_request_use_case,
    get_file_request_use_case,
    get_fill_in_request_use_case,
    get_my_requests_use_case,
    get_request_use_case,
    get_requests_use_case,
    get_sponsors_use_case,
    get_submit_request_use_case,
    get_withdraw_request_use_case,
)
from src.modules.users.domain.entities.user import User

router = APIRouter(prefix="/requests", tags=["requests"])


@router.post(
    "",
    response_model=RequestResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="fileRequest",
)
async def file_request(
    payload: FileRequestRequest,
    current_user: User = Depends(get_signed_in_user),
    use_case: FileRequestUseCase = Depends(get_file_request_use_case),
    session: AsyncSession = Depends(get_db),
) -> RequestResponse:
    """Opens a need as a draft. Anyone signed in may express one."""
    assert current_user.id is not None
    detail = await use_case.execute(
        FileRequestCommand(
            requester_id=current_user.id,
            title=payload.title,
            departments=payload.departments,
            sponsor_ids=payload.sponsor_ids,
        )
    )
    await session.commit()
    return to_request_response(detail)


# Declared before `/{request_id}`: a path that reads as a word would otherwise
# be taken for an identifier and answered with a 422.
@router.get(
    "/mine", response_model=list[RequestResponse], operation_id="listMyRequests"
)
async def list_my_requests(
    current_user: User = Depends(get_signed_in_user),
    use_case: ListMyRequestsUseCase = Depends(get_my_requests_use_case),
) -> list[RequestResponse]:
    """Everything one filed, drafts included: they are all theirs."""
    assert current_user.id is not None
    return [
        to_request_response(detail)
        for detail in await use_case.execute(current_user.id)
    ]


@router.get("", response_model=list[RequestResponse], operation_id="listRequests")
async def list_requests(
    current_user: User = Depends(get_signed_in_user),
    use_case: ListRequestsUseCase = Depends(get_requests_use_case),
) -> list[RequestResponse]:
    """What the team reads: everything handed over, plus one's own drafts."""
    assert current_user.id is not None
    return [
        to_request_response(detail)
        for detail in await use_case.execute(current_user.id)
    ]


@router.get(
    "/sponsors",
    response_model=list[RequestPersonResponse],
    operation_id="listRequestSponsors",
)
async def list_sponsors(
    _: User = Depends(get_signed_in_user),
    use_case: ListSponsorsUseCase = Depends(get_sponsors_use_case),
) -> list[RequestPersonResponse]:
    """The members of the COMEX a need may be carried to."""
    return [to_sponsor_response(user) for user in await use_case.execute()]


@router.get("/{request_id}", response_model=RequestResponse, operation_id="getRequest")
async def get_request(
    request_id: int,
    current_user: User = Depends(get_signed_in_user),
    use_case: GetRequestUseCase = Depends(get_request_use_case),
) -> RequestResponse:
    """One request: its author's, or the team's once it has been handed over."""
    assert current_user.id is not None
    return to_request_response(await use_case.execute(request_id, current_user.id))


@router.patch(
    "/{request_id}", response_model=RequestResponse, operation_id="fillInRequest"
)
async def fill_in_request(
    request_id: int,
    payload: FillInRequestRequest,
    current_user: User = Depends(get_signed_in_user),
    use_case: FillInRequestUseCase = Depends(get_fill_in_request_use_case),
    session: AsyncSession = Depends(get_db),
) -> RequestResponse:
    """Writes the sheet whole. Its author, and only while it is a draft."""
    assert current_user.id is not None
    detail = await use_case.execute(
        FillInRequestCommand(
            actor_id=current_user.id,
            request_id=request_id,
            title=payload.title,
            departments=payload.departments,
            sponsor_ids=payload.sponsor_ids,
            problem=payload.problem,
            impact=payload.impact,
            expected_outcome=payload.expected_outcome,
            cost_of_inaction=payload.cost_of_inaction,
            desired_timing=payload.desired_timing,
            envisaged_solution=payload.envisaged_solution,
        )
    )
    await session.commit()
    return to_request_response(detail)


@router.post(
    "/{request_id}/submit",
    response_model=RequestResponse,
    operation_id="submitRequest",
)
async def submit_request(
    request_id: int,
    current_user: User = Depends(get_signed_in_user),
    use_case: SubmitRequestUseCase = Depends(get_submit_request_use_case),
    session: AsyncSession = Depends(get_db),
) -> RequestResponse:
    """Hands the need over to be weighed, and rings for the managers."""
    assert current_user.id is not None
    detail = await use_case.execute(request_id, current_user.id)
    await session.commit()
    return to_request_response(detail)


@router.post(
    "/{request_id}/withdraw",
    response_model=RequestResponse,
    operation_id="withdrawRequest",
)
async def withdraw_request(
    request_id: int,
    current_user: User = Depends(get_signed_in_user),
    use_case: WithdrawRequestUseCase = Depends(get_withdraw_request_use_case),
    session: AsyncSession = Depends(get_db),
) -> RequestResponse:
    """Takes the need back: it becomes a draft again, and nothing is lost."""
    assert current_user.id is not None
    detail = await use_case.execute(request_id, current_user.id)
    await session.commit()
    return to_request_response(detail)


@router.delete(
    "/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteRequest",
)
async def delete_request(
    request_id: int,
    current_user: User = Depends(get_signed_in_user),
    use_case: DeleteRequestUseCase = Depends(get_delete_request_use_case),
    session: AsyncSession = Depends(get_db),
) -> Response:
    """Erases a draft. Only a draft, and only its author."""
    assert current_user.id is not None
    await use_case.execute(request_id, current_user.id)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{request_id}/decision",
    response_model=RequestResponse,
    operation_id="decideRequest",
)
async def decide_request(
    request_id: int,
    payload: DecideRequestRequest,
    current_user: User = Depends(get_signed_in_user),
    use_case: DecideRequestUseCase = Depends(get_decide_request_use_case),
    session: AsyncSession = Depends(get_db),
) -> RequestResponse:
    """Weighs a need. Managers, bar the one who asked for it or carries it."""
    assert current_user.id is not None
    detail = await use_case.execute(
        DecideRequestCommand(
            actor_id=current_user.id,
            request_id=request_id,
            decision=payload.decision,
            note=payload.note,
        )
    )
    await session.commit()
    return to_request_response(detail)


@router.post(
    "/{request_id}/convert",
    response_model=RequestResponse,
    operation_id="convertRequest",
)
async def convert_request(
    request_id: int,
    payload: ConvertRequestRequest,
    current_user: User = Depends(get_signed_in_user),
    use_case: ConvertRequestUseCase = Depends(get_convert_request_use_case),
    session: AsyncSession = Depends(get_db),
) -> RequestResponse:
    """Makes a mission of an accepted need. Managers, and only once."""
    assert current_user.id is not None
    detail = await use_case.execute(
        ConvertRequestCommand(
            actor_id=current_user.id,
            request_id=request_id,
            kind=payload.kind,
            parent_id=payload.parent_id,
        )
    )
    await session.commit()
    return to_request_response(detail)
