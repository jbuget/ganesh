"""SQLAlchemy implementation of the UserRepository port."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.users.domain.entities.presence import WEEKDAYS, WeekPresence
from src.modules.users.domain.entities.user import User
from src.modules.users.domain.repositories.user_repository import UserRepository
from src.modules.users.infrastructure.database.models.user_model import UserModel


def _presence_of(model: UserModel) -> WeekPresence:
    """The week this teammate works, on site every day until they say so."""
    said = {day: getattr(model, f"presence_{day}") for day in WEEKDAYS}
    return WeekPresence(**{day: value for day, value in said.items() if value})


def _write_presence(model: UserModel, presence: WeekPresence) -> None:
    for day in WEEKDAYS:
        setattr(model, f"presence_{day}", getattr(presence, day))


def to_entity(model: UserModel) -> User:
    return User(
        id=model.id,
        entra_oid=model.entra_oid or "",
        email=model.email,
        display_name=model.display_name,
        role=model.role,
        is_active=model.is_active,
        last_login_at=model.last_login_at,
        first_name=model.first_name,
        last_name=model.last_name,
        department=model.department,
        github_username=model.github_username,
        presence=_presence_of(model),
    )


class SqlUserRepository(UserRepository):
    """Persists users in the database."""

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
            statement = statement.where(UserModel.is_active.is_(True))
        result = await self._session.execute(statement)
        return [to_entity(model) for model in result.scalars().all()]

    async def add(self, user: User) -> User:
        model = UserModel(
            entra_oid=user.entra_oid or None,
            email=user.email,
            display_name=user.display_name,
            role=user.role,
            is_active=user.is_active,
            last_login_at=user.last_login_at,
            first_name=user.first_name,
            last_name=user.last_name,
            department=user.department,
            github_username=user.github_username,
        )
        _write_presence(model, user.presence)
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
        model.is_active = user.is_active
        model.last_login_at = user.last_login_at
        model.first_name = user.first_name
        model.last_name = user.last_name
        model.department = user.department
        model.github_username = user.github_username
        _write_presence(model, user.presence)
        await self._session.flush()
        return user
