"""SQLAlchemy implementation of the NotificationRepository port."""

from datetime import date, datetime

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from src.modules.notifications.domain.entities.notification import (
    Notification,
    NotificationKind,
)
from src.modules.notifications.domain.repositories.notification_repository import (
    NotificationRepository,
)
from src.modules.notifications.infrastructure.database.models.notification_model import (
    NotificationModel,
)

#: A line whose actor's account has been removed keeps its place. Nobody is
#: named at the top of it, and the interface says so rather than dropping it.
DELETED_ACCOUNT = 0


def to_entity(model: NotificationModel) -> Notification:
    notification = Notification.__new__(Notification)
    # The entity refuses a recipient who is their own actor, which is right on
    # the way in and beside the point on the way out: what is already stored
    # is read back as it stands.
    notification.recipient_id = model.recipient_id
    notification.kind = model.kind
    notification.actor_id = (
        DELETED_ACCOUNT if model.actor_id is None else model.actor_id
    )
    notification.at = model.at
    notification.project_id = model.project_id
    notification.request_id = model.request_id
    notification.day = model.day
    notification.payload = model.payload
    notification.count = model.count
    notification.read_at = model.read_at
    notification.id = model.id
    return notification


class SqlNotificationRepository(NotificationRepository):
    """Persists what people are told."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, notification: Notification) -> Notification:
        model = NotificationModel(
            recipient_id=notification.recipient_id,
            kind=notification.kind,
            actor_id=notification.actor_id,
            at=notification.at,
            project_id=notification.project_id,
            request_id=notification.request_id,
            day=notification.day,
            payload=notification.payload,
            count=notification.count,
            read_at=notification.read_at,
        )
        self._session.add(model)
        await self._session.flush()
        notification.id = model.id
        return notification

    async def save(self, notification: Notification) -> None:
        await self._session.execute(
            update(NotificationModel)
            .where(NotificationModel.id == notification.id)
            .values(
                at=notification.at,
                count=notification.count,
                read_at=notification.read_at,
            )
        )
        await self._session.flush()

    async def find_open_twin(
        self,
        recipient_id: int,
        kind: NotificationKind,
        actor_id: int,
        day: date | None,
    ) -> Notification | None:
        result = await self._session.execute(
            select(NotificationModel)
            .where(
                and_(
                    NotificationModel.recipient_id == recipient_id,
                    NotificationModel.kind == kind,
                    NotificationModel.actor_id == actor_id,
                    NotificationModel.day == day,
                    NotificationModel.read_at.is_(None),
                )
            )
            .order_by(NotificationModel.at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return to_entity(model) if model else None

    def _mine(self, recipient_id: int, unread_only: bool) -> ColumnElement[bool]:
        clause = NotificationModel.recipient_id == recipient_id
        if unread_only:
            return and_(clause, NotificationModel.read_at.is_(None))
        return clause

    async def list_for(
        self, recipient_id: int, unread_only: bool, limit: int, offset: int
    ) -> list[Notification]:
        result = await self._session.execute(
            select(NotificationModel)
            .where(self._mine(recipient_id, unread_only))
            .order_by(NotificationModel.at.desc(), NotificationModel.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return [to_entity(model) for model in result.scalars().all()]

    async def list_waiting_since(
        self, recipient_id: int, since: datetime | None
    ) -> list[Notification]:
        statement = select(NotificationModel).where(
            self._mine(recipient_id, unread_only=True)
        )
        if since is not None:
            statement = statement.where(NotificationModel.at > since)
        result = await self._session.execute(
            statement.order_by(NotificationModel.at.asc(), NotificationModel.id.asc())
        )
        return [to_entity(model) for model in result.scalars().all()]

    async def count_for(self, recipient_id: int, unread_only: bool) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(NotificationModel)
            .where(self._mine(recipient_id, unread_only))
        )
        return int(result.scalar_one())

    async def set_read_state(
        self,
        recipient_id: int,
        ids: list[int] | None,
        read: bool,
        at: datetime,
    ) -> int:
        clauses = [
            NotificationModel.recipient_id == recipient_id,
            # Lines already in the asked-for state are left alone, so that the
            # count handed back is of what actually moved — and so that
            # marking everything read twice does not restamp yesterday's.
            (
                NotificationModel.read_at.is_(None)
                if read
                else NotificationModel.read_at.is_not(None)
            ),
        ]
        if ids is not None:
            if not ids:
                return 0
            clauses.append(NotificationModel.id.in_(ids))

        result = await self._session.execute(
            update(NotificationModel)
            .where(and_(*clauses))
            .values(read_at=at if read else None)
        )
        await self._session.flush()
        return int(result.rowcount or 0)
