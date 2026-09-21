"""Persistence of the files a mission carries."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.projects.domain.entities.project_attachment import ProjectAttachment
from src.modules.projects.domain.repositories.project_attachment_repository import (
    ProjectAttachmentRepository,
)
from src.modules.projects.infrastructure.database.models.project_attachment_model import (
    ProjectAttachmentModel,
)


def _to_entity(model: ProjectAttachmentModel) -> ProjectAttachment:
    return ProjectAttachment(
        id=model.id,
        project_id=model.project_id,
        uploaded_by=model.uploaded_by,
        filename=model.filename,
        content_type=model.content_type,
        size_bytes=model.size_bytes,
        storage_key=model.storage_key,
        uploaded_at=model.uploaded_at,
    )


class SqlProjectAttachmentRepository(ProjectAttachmentRepository):
    """The register of files, in the database."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, attachment_id: int) -> ProjectAttachment | None:
        model = await self._session.get(ProjectAttachmentModel, attachment_id)
        return None if model is None else _to_entity(model)

    async def list_for_project(self, project_id: int) -> list[ProjectAttachment]:
        result = await self._session.execute(
            select(ProjectAttachmentModel)
            .where(ProjectAttachmentModel.project_id == project_id)
            .order_by(
                ProjectAttachmentModel.uploaded_at.desc(),
                ProjectAttachmentModel.id.desc(),
            )
        )
        return [_to_entity(model) for model in result.scalars().all()]

    async def keys_for_project(self, project_id: int) -> list[str]:
        result = await self._session.execute(
            select(ProjectAttachmentModel.storage_key).where(
                ProjectAttachmentModel.project_id == project_id
            )
        )
        return list(result.scalars().all())

    async def add(self, attachment: ProjectAttachment) -> ProjectAttachment:
        model = ProjectAttachmentModel(
            project_id=attachment.project_id,
            uploaded_by=attachment.uploaded_by,
            filename=attachment.filename,
            content_type=attachment.content_type,
            size_bytes=attachment.size_bytes,
            storage_key=attachment.storage_key,
            uploaded_at=attachment.uploaded_at,
        )
        self._session.add(model)
        await self._session.flush()
        attachment.id = model.id
        return attachment

    async def update(self, attachment: ProjectAttachment) -> ProjectAttachment:
        model = await self._session.get(ProjectAttachmentModel, attachment.id)
        if model is not None:
            # The name is the only thing a file ever changes: where its bytes
            # sit was drawn once and stays.
            model.filename = attachment.filename
        return attachment

    async def remove(self, attachment_id: int) -> None:
        await self._session.execute(
            delete(ProjectAttachmentModel).where(
                ProjectAttachmentModel.id == attachment_id
            )
        )
