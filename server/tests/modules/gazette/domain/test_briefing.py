"""What one month of the register says, read back as movements."""

from datetime import date, datetime

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.gazette.domain.entities.movement import MovementKind
from src.modules.gazette.domain.services.briefing import build_brief
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)

MONTH = date(2026, 9, 1)

PEOPLE = {1: "Léa Chen", 2: "Sam Okafor"}
#: The needs the register can name, as the gazette reads them back.
NEEDS = {4: "Relances de paiement à la main"}


def a_project(
    project_id: int,
    label: str = "WAATcher",
    status: ProjectStatus | None = ProjectStatus.DEVELOPMENT,
    is_active: bool = True,
    go_live_date: date | None = None,
) -> Project:
    return Project(
        id=project_id,
        label=label,
        kind=ProjectKind.PROJECT,
        status=status,
        is_active=is_active,
        go_live_date=go_live_date,
    )


def on(day: int, hour: int = 9) -> datetime:
    return datetime(2026, 9, day, hour)


class TestMovements:
    def test_a_month_nothing_happened_in_carries_no_movement(self) -> None:
        brief = build_brief(MONTH, logs=[], projects={}, people=PEOPLE, needs=NEEDS)

        assert brief.month == MONTH
        assert brief.movements == []

    def test_it_reads_a_project_that_joined_the_reference_list(self) -> None:
        logs = [
            AuditLog(
                action=AuditAction.PROJECT_CREATE,
                actor_id=1,
                project_id=7,
                at=on(3),
            )
        ]

        brief = build_brief(
            MONTH, logs, {7: a_project(7, "Ganesh")}, PEOPLE, needs=NEEDS
        )

        assert [(m.kind, m.subject) for m in brief.movements] == [
            (MovementKind.PROJECT_CREATED, "Ganesh")
        ]

    def test_it_reads_an_archiving_and_a_revival_apart(self) -> None:
        logs = [
            AuditLog(
                action=AuditAction.PROJECT_UPDATE,
                actor_id=1,
                project_id=7,
                old_value="True",
                new_value="False",
                payload={"field": "is_active"},
                at=on(3),
            ),
            AuditLog(
                action=AuditAction.PROJECT_UPDATE,
                actor_id=1,
                project_id=8,
                old_value="False",
                new_value="True",
                payload={"field": "is_active"},
                at=on(4),
            ),
        ]

        brief = build_brief(
            MONTH,
            logs,
            {7: a_project(7, "Ganesh"), 8: a_project(8, "NOMAD")},
            PEOPLE,
            needs=NEEDS,
        )

        assert [(m.kind, m.subject) for m in brief.movements] == [
            (MovementKind.PROJECT_ARCHIVED, "Ganesh"),
            (MovementKind.PROJECT_REVIVED, "NOMAD"),
        ]

    def test_a_change_on_another_field_is_not_a_movement(self) -> None:
        """Renaming a mission steers nothing: the numéro would drown in it."""
        logs = [
            AuditLog(
                action=AuditAction.PROJECT_UPDATE,
                actor_id=1,
                project_id=7,
                old_value="Ganesh",
                new_value="Ganesh v2",
                payload={"field": "label"},
                at=on(3),
            )
        ]

        assert (
            build_brief(MONTH, logs, {7: a_project(7)}, PEOPLE, needs=NEEDS).movements
            == []
        )

    def test_it_tells_a_phase_that_moved_on_from_one_that_went_back(self) -> None:
        logs = [
            AuditLog.project_status_change(
                actor_id=1,
                project_id=7,
                old_status=ProjectStatus.SCOPING,
                new_status=ProjectStatus.DEVELOPMENT,
                at=on(3),
            ),
            AuditLog.project_status_change(
                actor_id=1,
                project_id=8,
                old_status=ProjectStatus.VALIDATION,
                new_status=ProjectStatus.DEVELOPMENT,
                at=on(4),
            ),
        ]

        brief = build_brief(
            MONTH,
            logs,
            {7: a_project(7, "Ganesh"), 8: a_project(8, "NOMAD")},
            PEOPLE,
            needs=NEEDS,
        )

        assert [(m.kind, m.subject) for m in brief.movements] == [
            (MovementKind.PHASE_ADVANCED, "Ganesh"),
            (MovementKind.PHASE_STEPPED_BACK, "NOMAD"),
        ]

    def test_it_reads_a_phase_changed_from_the_mission_form(self) -> None:
        """The register holds a phase move in two shapes, not one.

        Dragging a card traces `project.status_change`; editing the mission
        traces a plain field change. A gazette reading only the first would
        quietly miss every move made from the form.
        """
        logs = [
            AuditLog(
                action=AuditAction.PROJECT_UPDATE,
                actor_id=1,
                project_id=7,
                old_value=ProjectStatus.SCOPING.value,
                new_value=ProjectStatus.DEVELOPMENT.value,
                payload={"field": "status"},
                at=on(3),
            )
        ]

        brief = build_brief(
            MONTH, logs, {7: a_project(7, "Ganesh")}, PEOPLE, needs=NEEDS
        )

        assert [(m.kind, m.subject) for m in brief.movements] == [
            (MovementKind.PHASE_ADVANCED, "Ganesh")
        ]

    def test_a_phase_that_moved_carries_where_it_came_from_and_went(self) -> None:
        logs = [
            AuditLog.project_status_change(
                actor_id=1,
                project_id=7,
                old_status=ProjectStatus.SCOPING,
                new_status=ProjectStatus.DEVELOPMENT,
                at=on(3),
            )
        ]

        movement = build_brief(
            MONTH, logs, {7: a_project(7)}, PEOPLE, needs=NEEDS
        ).movements[0]

        assert movement.from_status is ProjectStatus.SCOPING
        assert movement.to_status is ProjectStatus.DEVELOPMENT

    def test_reaching_operations_is_a_mise_en_service_of_its_own(self) -> None:
        """The one phase move steering reads before any other."""
        logs = [
            AuditLog.project_status_change(
                actor_id=1,
                project_id=7,
                old_status=ProjectStatus.DEPLOYMENT,
                new_status=ProjectStatus.OPERATIONS,
                at=on(3),
            )
        ]

        brief = build_brief(
            MONTH, logs, {7: a_project(7, "Ganesh")}, PEOPLE, needs=NEEDS
        )

        assert brief.movements[0].kind is MovementKind.WENT_LIVE

    def test_it_reads_the_news_the_team_posted(self) -> None:
        logs = [
            AuditLog(
                action=AuditAction.UPDATE_POST,
                actor_id=1,
                project_id=7,
                at=on(3),
            )
        ]

        brief = build_brief(
            MONTH, logs, {7: a_project(7, "Ganesh")}, PEOPLE, needs=NEEDS
        )

        assert [(m.kind, m.subject) for m in brief.movements] == [
            (MovementKind.NEWS_POSTED, "Ganesh")
        ]

    def test_it_reads_who_joined_and_who_left_the_team(self) -> None:
        logs = [
            AuditLog(
                action=AuditAction.USER_CREATE,
                actor_id=1,
                target_user_id=2,
                at=on(3),
            ),
            AuditLog(
                action=AuditAction.USER_DEACTIVATE,
                actor_id=1,
                target_user_id=1,
                at=on(4),
            ),
        ]

        brief = build_brief(MONTH, logs, {}, PEOPLE, needs=NEEDS)

        assert [(m.kind, m.subject) for m in brief.movements] == [
            (MovementKind.TEAMMATE_JOINED, "Sam Okafor"),
            (MovementKind.TEAMMATE_LEFT, "Léa Chen"),
        ]

    def test_a_movement_nobody_can_name_is_dropped(self) -> None:
        """A deleted project leaves its log lines behind, with no subject left.

        The gazette invents nothing: a line it cannot name is a line it does
        not print.
        """
        logs = [
            AuditLog(
                action=AuditAction.PROJECT_CREATE, actor_id=1, project_id=None, at=on(3)
            ),
            AuditLog(
                action=AuditAction.PROJECT_CREATE, actor_id=1, project_id=99, at=on(4)
            ),
        ]

        assert build_brief(MONTH, logs, {}, PEOPLE, needs=NEEDS).movements == []

    def test_movements_read_in_the_order_they_happened(self) -> None:
        logs = [
            AuditLog(
                action=AuditAction.PROJECT_CREATE, actor_id=1, project_id=8, at=on(9)
            ),
            AuditLog(
                action=AuditAction.PROJECT_CREATE, actor_id=1, project_id=7, at=on(2)
            ),
        ]

        brief = build_brief(
            MONTH,
            logs,
            {7: a_project(7, "Ganesh"), 8: a_project(8, "NOMAD")},
            PEOPLE,
            needs=NEEDS,
        )

        assert [m.subject for m in brief.movements] == ["Ganesh", "NOMAD"]

    def test_the_gazette_does_not_tell_its_own_story(self) -> None:
        """Publishing a numéro is traced like anything else, and left out.

        A gazette reporting that a gazette was published would fill up with
        itself, one line deeper every month.
        """
        logs = [
            AuditLog(
                action=AuditAction.GAZETTE_GENERATE, actor_id=1, day=MONTH, at=on(3)
            )
        ]

        assert build_brief(MONTH, logs, {}, PEOPLE, needs=NEEDS).movements == []


class TestTally:
    def test_it_counts_what_the_month_did_to_the_reference_list(self) -> None:
        logs = [
            AuditLog(
                action=AuditAction.PROJECT_CREATE, actor_id=1, project_id=7, at=on(2)
            ),
            AuditLog(
                action=AuditAction.PROJECT_UPDATE,
                actor_id=1,
                project_id=8,
                old_value="True",
                new_value="False",
                payload={"field": "is_active"},
                at=on(3),
            ),
            AuditLog.project_status_change(
                actor_id=1,
                project_id=7,
                old_status=ProjectStatus.SCOPING,
                new_status=ProjectStatus.DEVELOPMENT,
                at=on(4),
            ),
            AuditLog(
                action=AuditAction.UPDATE_POST, actor_id=1, project_id=7, at=on(5)
            ),
        ]

        tally = build_brief(
            MONTH,
            logs,
            {7: a_project(7, "Ganesh"), 8: a_project(8, "NOMAD")},
            PEOPLE,
            needs=NEEDS,
        ).tally

        assert tally.projects_created == 1
        assert tally.projects_archived == 1
        assert tally.phase_changes == 1
        assert tally.news_posted == 1

    def test_it_counts_the_months_that_were_closed(self) -> None:
        logs = [
            AuditLog.month_validate(
                actor_id=1, target_user_id=1, month=date(2026, 8, 1), at=on(2)
            ),
            AuditLog.month_validate(
                actor_id=2, target_user_id=2, month=date(2026, 8, 1), at=on(3)
            ),
        ]

        assert (
            build_brief(MONTH, logs, {}, PEOPLE, needs=NEEDS).tally.months_validated
            == 2
        )

    def test_a_month_closed_twice_is_closed_once(self) -> None:
        """Reopened then closed again is one month closed, not two."""
        logs = [
            AuditLog.month_validate(
                actor_id=1, target_user_id=1, month=date(2026, 8, 1), at=on(2)
            ),
            AuditLog.month_reopen(
                actor_id=2, target_user_id=1, month=date(2026, 8, 1), at=on(3)
            ),
            AuditLog.month_validate(
                actor_id=1, target_user_id=1, month=date(2026, 8, 1), at=on(4)
            ),
        ]

        assert (
            build_brief(MONTH, logs, {}, PEOPLE, needs=NEEDS).tally.months_validated
            == 1
        )

    def test_a_month_closed_is_counted_and_never_told(self) -> None:
        """Who closed their month, and who did not, is nobody's business here.

        A figure that singles a teammate out is not a figure, it is a
        reproach — and the month after, nobody fills anything in.
        """
        logs = [
            AuditLog.month_validate(
                actor_id=1, target_user_id=1, month=date(2026, 8, 1), at=on(2)
            )
        ]

        brief = build_brief(MONTH, logs, {}, PEOPLE, needs=NEEDS)

        assert brief.tally.months_validated == 1
        assert brief.movements == []


class TestWhatTheCompanyAskedFor:
    """A need is not a mission, and the gazette tells it as what it is."""

    def test_it_reads_a_need_the_month_was_handed(self) -> None:
        logs = [
            AuditLog(
                action=AuditAction.REQUEST_SUBMIT,
                actor_id=1,
                request_id=4,
                at=on(3),
                new_value="Relances de paiement à la main",
            )
        ]

        brief = build_brief(MONTH, logs, {}, PEOPLE, NEEDS)

        assert [(m.kind, m.subject) for m in brief.movements] == [
            (MovementKind.REQUEST_FILED, "Relances de paiement à la main")
        ]

    def test_a_need_still_being_written_is_nobody_s_month(self) -> None:
        """A draft has been asked of nobody: it is not a fact of the month."""
        logs = [
            AuditLog(
                action=AuditAction.REQUEST_CREATE,
                actor_id=1,
                request_id=4,
                at=on(3),
                new_value="Relances de paiement à la main",
            )
        ]

        assert build_brief(MONTH, logs, {}, PEOPLE, NEEDS).movements == []

    def test_it_tells_the_three_things_arbitrating_can_say(self) -> None:
        logs = [
            AuditLog(
                action=AuditAction.REQUEST_DECIDE,
                actor_id=1,
                request_id=4,
                at=on(day),
                new_value=said,
            )
            for day, said in ((4, "accepted"), (5, "rejected"), (6, "deferred"))
        ]

        brief = build_brief(MONTH, logs, {}, PEOPLE, NEEDS)

        assert [m.kind for m in brief.movements] == [
            MovementKind.REQUEST_ACCEPTED,
            MovementKind.REQUEST_REJECTED,
            MovementKind.REQUEST_DEFERRED,
        ]

    def test_a_decision_the_register_spells_otherwise_is_not_invented(self) -> None:
        logs = [
            AuditLog(
                action=AuditAction.REQUEST_DECIDE,
                actor_id=1,
                request_id=4,
                at=on(4),
                new_value="something-else",
            )
        ]

        assert build_brief(MONTH, logs, {}, PEOPLE, NEEDS).movements == []

    def test_a_need_that_became_a_mission_is_told_as_a_need(self) -> None:
        """It carries no project: a need is not a mission, even the day it is."""
        logs = [
            AuditLog(
                action=AuditAction.REQUEST_CONVERT,
                actor_id=1,
                request_id=4,
                project_id=7,
                at=on(7),
                new_value="Relances de paiement à la main",
            )
        ]

        brief = build_brief(MONTH, logs, {7: a_project(7, "Relances")}, PEOPLE, NEEDS)

        assert [(m.kind, m.project_id) for m in brief.movements] == [
            (MovementKind.REQUEST_CONVERTED, None)
        ]

    def test_a_need_nobody_can_name_is_not_printed(self) -> None:
        """The gazette invents nothing, here as everywhere else."""
        logs = [
            AuditLog(
                action=AuditAction.REQUEST_SUBMIT,
                actor_id=1,
                request_id=99,
                at=on(3),
                new_value="Disparue",
            )
        ]

        assert build_brief(MONTH, logs, {}, PEOPLE, NEEDS).movements == []

    def test_what_was_asked_and_what_was_built_are_counted_apart(self) -> None:
        """A month that filed six and built none says what either alone hides."""
        logs = [
            AuditLog(
                action=AuditAction.REQUEST_SUBMIT,
                actor_id=1,
                request_id=4,
                at=on(3),
            ),
            AuditLog(
                action=AuditAction.REQUEST_CONVERT,
                actor_id=1,
                request_id=4,
                project_id=7,
                at=on(8),
            ),
        ]

        tally = build_brief(MONTH, logs, {}, PEOPLE, NEEDS).tally

        assert tally.requests_filed == 1
        assert tally.requests_converted == 1
