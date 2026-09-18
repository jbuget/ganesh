"""Translating teammates into API schemas."""

from src.modules.users.domain.entities.user import User
from src.modules.users.presentation.api.schemas.user_schemas import UserResponse
from src.shared.utils.initials import initials


def to_user_response(user: User) -> UserResponse:
    assert user.id is not None
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        initials=initials(user.display_name),
        role=user.role,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
    )
