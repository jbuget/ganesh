"""SQLAlchemy implementation of the RequestRepository port."""

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.requests.domain.entities.request import Request, RequestState
from src.modules.requests.domain.repositories.request_repository import (
    RequestRepository,
)
from src.modules.requests.infrastructure.database.models.request_model import (
    RequestDepartmentModel,
    RequestModel,
    RequestSponsorModel,
)
from src.shared.enums.department import Department


def to_entity(
    model: RequestModel, departments: list[Department], sponsor_ids: list[int]
) -> Request:
    return Request(
        id=model.id,
        title=model.title,
        requester_id=model.requester_id,
        departments=departments,
        sponsor_ids=sponsor_ids,
        created_at=model.created_at,
        state=model.state,
        problem=model.problem,
        impact=model.impact,
        expected_outcome=model.expected_outcome,
        cost_of_inaction=model.cost_of_inaction,
        desired_by=model.desired_by,
        envisaged_solution=model.envisaged_solution,
        submitted_at=model.submitted_at,
        decided_at=model.decided_at,
        decided_by_id=model.decided_by_id,
        decision_note=model.decision_note,
        converted_at=model.converted_at,
        converted_project_id=model.converted_project_id,
    )


class SqlRequestRepository(RequestRepository):
    """Persists the needs the company expresses."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, request_id: int) -> Request | None:
        model = await self._session.get(RequestModel, request_id)
        if model is None:
            return None
        return (await self._all([model]))[0]

    async def list_for_requester(self, requester_id: int) -> list[Request]:
        models = (
            (
                await self._session.execute(
                    select(RequestModel)
                    .where(RequestModel.requester_id == requester_id)
                    .order_by(RequestModel.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return await self._all(list(models))

    async def list_readable_by(self, viewer_id: int) -> list[Request]:
        query = (
            select(RequestModel)
            .where(
                or_(
                    RequestModel.state != RequestState.DRAFT,
                    RequestModel.requester_id == viewer_id,
                )
            )
            .order_by(RequestModel.created_at.desc())
        )
        models = (await self._session.execute(query)).scalars().all()
        return await self._all(list(models))

    async def add(self, request: Request) -> Request:
        model = RequestModel(
            title=request.title,
            requester_id=request.requester_id,
            state=request.state,
            created_at=request.created_at,
            problem=request.problem,
            impact=request.impact,
            expected_outcome=request.expected_outcome,
            cost_of_inaction=request.cost_of_inaction,
            desired_by=request.desired_by,
            envisaged_solution=request.envisaged_solution,
            submitted_at=request.submitted_at,
        )
        self._session.add(model)
        await self._session.flush()
        request.id = model.id
        await self._write_the_lists(request)
        return request

    async def update(self, request: Request) -> Request:
        if request.id is None:
            return await self.add(request)
        model = await self._session.get(RequestModel, request.id)
        if model is None:
            return request

        model.title = request.title
        model.state = request.state
        model.problem = request.problem
        model.impact = request.impact
        model.expected_outcome = request.expected_outcome
        model.cost_of_inaction = request.cost_of_inaction
        model.desired_by = request.desired_by
        model.envisaged_solution = request.envisaged_solution
        model.submitted_at = request.submitted_at
        model.decided_at = request.decided_at
        model.decided_by_id = request.decided_by_id
        model.decision_note = request.decision_note
        model.converted_at = request.converted_at
        model.converted_project_id = request.converted_project_id
        await self._write_the_lists(request)
        await self._session.flush()
        return request

    async def delete(self, request_id: int) -> None:
        model = await self._session.get(RequestModel, request_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()

    async def _write_the_lists(self, request: Request) -> None:
        """Rewrites the departments and the sponsors as the sheet holds them.

        Cleared and written again rather than compared: both lists are short,
        and the order they are read back in is the entity's business.
        """
        assert request.id is not None
        await self._session.execute(
            delete(RequestDepartmentModel).where(
                RequestDepartmentModel.request_id == request.id
            )
        )
        await self._session.execute(
            delete(RequestSponsorModel).where(
                RequestSponsorModel.request_id == request.id
            )
        )
        for department in request.departments:
            self._session.add(
                RequestDepartmentModel(request_id=request.id, department=department)
            )
        for sponsor_id in request.sponsor_ids:
            self._session.add(
                RequestSponsorModel(request_id=request.id, sponsor_id=sponsor_id)
            )
        await self._session.flush()

    async def _all(self, models: list[RequestModel]) -> list[Request]:
        """Reads the two lists of every request in one query each."""
        if not models:
            return []
        ids = [model.id for model in models]

        departments: dict[int, list[Department]] = {model_id: [] for model_id in ids}
        rows = await self._session.execute(
            select(RequestDepartmentModel).where(
                RequestDepartmentModel.request_id.in_(ids)
            )
        )
        for row in rows.scalars().all():
            departments[row.request_id].append(row.department)

        sponsors: dict[int, list[int]] = {model_id: [] for model_id in ids}
        carried = await self._session.execute(
            select(RequestSponsorModel).where(RequestSponsorModel.request_id.in_(ids))
        )
        for sponsor in carried.scalars().all():
            sponsors[sponsor.request_id].append(sponsor.sponsor_id)

        return [
            to_entity(model, departments[model.id], sponsors[model.id])
            for model in models
        ]
