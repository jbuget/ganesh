"""Implementation SQLAlchemy du port UserRepository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.modules.users.infrastructure.database.models.user_model import UserModel


def to_entity(model: UserModel) -> User:
    return User(
        id=model.id,
        entra_oid=model.entra_oid or "",
        email=model.email,
        display_name=model.display_name,
        role=model.role,
        actif=model.actif,
    )


class SqlUserRepository(UserRepository):
    """Persiste les utilisateurs en base."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return to_entity(model) if model else None

    async def get_by_entra_oid(self, entra_oid: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.entra_oid == entra_oid)
        )
        model = result.scalar_one_or_none()
        return to_entity(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email.strip().lower())
        )
        model = result.scalar_one_or_none()
        return to_entity(model) if model else None

    async def list_all(self, include_inactive: bool = False) -> list[User]:
        statement = select(UserModel).order_by(UserModel.display_name)
        if not include_inactive:
            statement = statement.where(UserModel.actif.is_(True))
        result = await self._session.execute(statement)
        return [to_entity(model) for model in result.scalars().all()]

    async def add(self, user: User) -> User:
        model = UserModel(
            entra_oid=user.entra_oid or None,
            email=user.email,
            display_name=user.display_name,
            role=user.role,
            actif=user.actif,
        )
        self._session.add(model)
        await self._session.flush()
        user.id = model.id
        return user

    async def update(self, user: User) -> User:
        if user.id is None:
            return await self.add(user)
        model = await self._session.get(UserModel, user.id)
        if model is None:
            return user
        model.entra_oid = user.entra_oid or None
        model.email = user.email
        model.display_name = user.display_name
        model.role = user.role
        model.actif = user.actif
        await self._session.flush()
        return user
