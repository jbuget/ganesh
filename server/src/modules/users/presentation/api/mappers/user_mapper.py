"""Traduction des collaborateurs en schemas d'API."""

from src.modules.users.domain.entities.user import User
from src.modules.users.presentation.api.schemas.user_schemas import UserResponse
from src.shared.utils.initials import initiales


def to_user_response(user: User) -> UserResponse:
    assert user.id is not None
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        initiales=initiales(user.display_name),
        role=user.role,
        actif=user.actif,
        derniere_connexion=user.derniere_connexion,
    )
