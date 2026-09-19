"""Translating projects into API schemas."""

from datetime import date

from src.modules.projects.application.dtos.last_update import LastUpdate
from src.modules.projects.application.use_cases.get_board import Board
from src.modules.projects.application.use_cases.get_project_detail import ProjectDetail
from src.modules.projects.application.use_cases.list_projects import ListedProject
from src.modules.projects.application.use_cases.project_updates import SignedUpdate
from src.modules.projects.domain.entities.project import Project, ProjectStatus
from src.modules.projects.domain.entities.project_link import ProjectLink
from src.modules.projects.domain.services.phase_history import transition_label
from src.modules.projects.domain.services.project_cost import ProjectCost
from src.modules.projects.presentation.api.schemas.project_schemas import (
    BoardCardResponse,
    BoardColumnResponse,
    BoardMemberResponse,
    BoardParentResponse,
    BoardResponse,
    LastUpdateResponse,
    MonthlyShareResponse,
    PhaseReachedResponse,
    ProjectContributionResponse,
    ProjectCostResponse,
    ProjectDetailResponse,
    ProjectLinkResponse,
    ProjectListItemResponse,
    ProjectResponse,
    ProjectUpdateResponse,
)
from src.modules.users.domain.entities.user import User
from src.shared.utils.initials import initials


def to_project_response(
    project: Project, is_deletable: bool = False
) -> ProjectResponse:
    assert project.id is not None
    return ProjectResponse(
        id=project.id,
        label=project.label,
        kind=project.kind,
        status=project.status,
        parent_id=project.parent_id,
        is_active=project.is_active,
        archived_at=project.archived_at,
        estimated_days=project.estimated_days,
        category=project.category,
        priority=project.priority,
        go_live_date=project.go_live_date,
        position=project.position,
        monday_item_id=project.monday_item_id,
        monday_subitem_id=project.monday_subitem_id,
        business_contacts=project.business_contacts,
        description=project.description,
        is_syncable_to_monday=project.is_syncable_to_monday,
        is_deletable=is_deletable,
    )


def to_member(user: User) -> BoardMemberResponse:
    """A teammate reduced to what an avatar shows."""
    assert user.id is not None
    return BoardMemberResponse(
        id=user.id,
        display_name=user.display_name,
        initials=initials(user.display_name),
    )


def to_latest_update(latest: LastUpdate | None) -> LastUpdateResponse | None:
    """The latest message of a thread, as a row or a card announces it."""
    if latest is None:
        return None
    return LastUpdateResponse(
        author=to_member(latest.author),
        body=latest.update.body,
        published_at=latest.update.published_at,
    )


def to_link_response(link: ProjectLink) -> ProjectLinkResponse:
    """A useful address, as the sheet and the reference list both show it."""
    assert link.id is not None
    return ProjectLinkResponse(
        id=link.id, label=link.label, url=link.url, icon=link.icon
    )


def to_cost_response(cost: ProjectCost, today: date) -> ProjectCostResponse:
    return ProjectCostResponse(
        build_days=cost.build_days,
        run_days=cost.run_days,
        estimated_days=cost.estimated_days,
        monthly_run_rate=cost.monthly_run_rate(today),
        has_overrun=cost.has_overrun,
    )


def to_listed_project_response(
    listed: ListedProject, today: date | None = None
) -> ProjectListItemResponse:
    day = today or date.today()
    return ProjectListItemResponse(
        project=to_project_response(listed.project, is_deletable=listed.is_deletable),
        leads=[to_member(u) for u in listed.leads],
        contributors=[to_member(u) for u in listed.contributors],
        delivered_days=listed.delivered_days,
        cost=to_cost_response(listed.cost, day),
        tree_cost=to_cost_response(listed.tree_cost, day),
        links=[to_link_response(link) for link in listed.links if link.id is not None],
        comments=listed.comments,
        latest_update=to_latest_update(listed.latest_update),
    )


def to_board_response(board: Board) -> BoardResponse:
    return BoardResponse(
        columns=[
            BoardColumnResponse(
                status=column.status,
                cards=[
                    BoardCardResponse(
                        project=to_project_response(card.project),
                        consumed_days=card.consumed_days,
                        build_days=card.build_days,
                        contributors=[
                            BoardMemberResponse(
                                id=membre.id or 0,
                                display_name=membre.display_name,
                                initials=initials(membre.display_name),
                            )
                            for membre in card.contributors
                        ],
                        comments=card.comments,
                        latest_update=to_latest_update(card.latest_update),
                        sub_projects=card.sub_projects,
                        parent=(
                            BoardParentResponse(
                                id=card.parent.id or 0, label=card.parent.label
                            )
                            if card.parent is not None
                            else None
                        ),
                    )
                    for card in column.cards
                ],
            )
            for column in board.columns
        ]
    )


def to_project_detail_response(detail: ProjectDetail) -> ProjectDetailResponse:
    return ProjectDetailResponse(
        project=to_project_response(detail.project),
        departments=detail.departments,
        links=[to_link_response(link) for link in detail.links if link.id is not None],
        # Phases read in nominal order, not the order the database returns
        # them: a timeline is followed from start to finish.
        phases=[
            PhaseReachedResponse(
                status=status,
                label=transition_label(status),
                reached_at=detail.phases_reached[status],
            )
            for status in ProjectStatus
            if status in detail.phases_reached
        ],
        leads=[to_member(u) for u in detail.leads],
        contributors=[to_member(u) for u in detail.contributors],
        consumed_days=detail.consumed_days,
        contributions=[
            ProjectContributionResponse(
                member=to_member(contribution.user),
                days=contribution.days,
                by_month=[
                    MonthlyShareResponse(month=month, days=days)
                    for month, days in contribution.by_month
                ],
            )
            for contribution in detail.contributions
        ],
        sub_projects=[
            to_project_response(work_package) for work_package in detail.sub_projects
        ],
    )


def to_project_update_response(
    signed: SignedUpdate, reader_id: int
) -> ProjectUpdateResponse:
    assert signed.update.id is not None and signed.author.id is not None
    return ProjectUpdateResponse(
        id=signed.update.id,
        author=BoardMemberResponse(
            id=signed.author.id,
            display_name=signed.author.display_name,
            initials=initials(signed.author.display_name),
        ),
        body=signed.update.body,
        published_at=signed.update.published_at,
        edited_at=signed.update.edited_at,
        is_deleted=signed.update.is_deleted,
        is_mine=signed.update.author_id == reader_id,
    )
