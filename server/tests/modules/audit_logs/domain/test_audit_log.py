"""Tracabilite des actions significatives."""

from datetime import date, datetime

from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog


def test_an_entry_change_records_both_values() -> None:
    log = AuditLog.entry_set(
        actor_id=1,
        target_user_id=2,
        project_id=3,
        jour=date(2026, 9, 15),
        old_value=0.5,
        new_value=1.0,
    )

    assert log.action is AuditAction.ENTRY_SET
    assert log.old_value == "0.5"
    assert log.new_value == "1.0"


def test_an_entry_created_from_scratch_has_no_previous_value() -> None:
    log = AuditLog.entry_set(
        actor_id=1,
        target_user_id=1,
        project_id=3,
        jour=date(2026, 9, 15),
        old_value=None,
        new_value=0.5,
    )

    assert log.old_value is None


def test_editing_someone_else_is_visible_in_the_trace() -> None:
    log = AuditLog.entry_set(
        actor_id=1,
        target_user_id=2,
        project_id=3,
        jour=date(2026, 9, 15),
        old_value=None,
        new_value=1.0,
    )

    assert log.is_on_behalf_of_someone_else is True


def test_editing_ones_own_month_is_not_flagged() -> None:
    log = AuditLog.entry_set(
        actor_id=1,
        target_user_id=1,
        project_id=3,
        jour=date(2026, 9, 15),
        old_value=None,
        new_value=1.0,
    )

    assert log.is_on_behalf_of_someone_else is False


def test_a_status_change_records_the_transition() -> None:
    log = AuditLog.project_status_change(
        actor_id=1, project_id=3, old_status="cadrage", new_status="realisation"
    )

    assert log.action is AuditAction.PROJECT_STATUS_CHANGE
    assert (log.old_value, log.new_value) == ("cadrage", "realisation")


def test_a_month_reopening_is_traced() -> None:
    log = AuditLog.month_reopen(
        actor_id=2, target_user_id=1, mois=date(2026, 9, 1), at=datetime(2026, 10, 3)
    )

    assert log.action is AuditAction.MONTH_REOPEN
    assert log.at == datetime(2026, 10, 3)
