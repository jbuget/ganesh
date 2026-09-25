"""Translating requests into API schemas."""

from src.modules.requests.application.dtos.request_detail import (
    RequestDetail,
    RequestPerson,
)
from src.modules.requests.presentation.api.schemas.request_schemas import (
    RequestPersonResponse,
    RequestResponse,
)
from src.modules.users.domain.entities.user import User


def to_person_response(person: RequestPerson) -> RequestPersonResponse:
    return RequestPersonResponse(id=person.id, label=person.label)


def to_sponsor_response(user: User) -> RequestPersonResponse:
    """A sponsor the picker offers: a name and an identifier, nothing else.

    Deliberately not the teammate schema: the picker is read by people the
    team list is shut to, and an email address has no business travelling to
    them.
    """
    assert user.id is not None
    return RequestPersonResponse(id=user.id, label=user.label)


def to_request_response(detail: RequestDetail) -> RequestResponse:
    request = detail.request
    assert request.id is not None
    return RequestResponse(
        id=request.id,
        title=request.title,
        state=request.state,
        requester=to_person_response(detail.requester),
        sponsors=[to_person_response(sponsor) for sponsor in detail.sponsors],
        departments=request.departments,
        created_at=request.created_at,
        problem=request.problem,
        impact=request.impact,
        expected_outcome=request.expected_outcome,
        cost_of_inaction=request.cost_of_inaction,
        desired_timing=request.desired_timing,
        envisaged_solution=request.envisaged_solution,
        submitted_at=request.submitted_at,
        decided_by=(
            to_person_response(detail.decided_by)
            if detail.decided_by is not None
            else None
        ),
        decided_at=request.decided_at,
        decision_note=request.decision_note,
        converted_at=request.converted_at,
        converted_project_id=request.converted_project_id,
    )
