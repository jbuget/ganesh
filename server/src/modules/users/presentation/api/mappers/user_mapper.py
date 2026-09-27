"""Translating teammates into API schemas."""

from src.modules.users.domain.entities.user import User
from src.modules.users.presentation.api.schemas.user_schemas import (
    ImpersonatorResponse,
    SignedInUserResponse,
    UserResponse,
    to_presence_response,
)
from src.shared.utils.initials import initials


def to_user_response(user: User) -> UserResponse:
    assert user.id is not None
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.label,
        initials=initials(user.label),
        role=user.role,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        first_name=user.first_name,
        last_name=user.last_name,
        department=user.department,
        github_username=user.github_username,
        org_level=user.org_level,
        presence=to_presence_response(user.presence),
        reminder_cadence=user.reminder_cadence,
    )


def to_signed_in_user_response(user: User) -> SignedInUserResponse:
    """The account being read, saying so when somebody else is reading it."""
    borrower = user.impersonated_by
    return SignedInUserResponse(
        **to_user_response(user).model_dump(),
        impersonated_by=(
            None
            if borrower is None or borrower.id is None
            else ImpersonatorResponse(
                id=borrower.id,
                display_name=borrower.label,
                initials=initials(borrower.label),
            )
        ),
    )
