"""Translating teammates into API schemas."""

from src.modules.users.domain.entities.user import User
from src.modules.users.presentation.api.schemas.user_schemas import (
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
        presence=to_presence_response(user.presence) if user.presence else None,
    )
