"""What a reader narrowed the register down to."""

from datetime import UTC, datetime

from src.modules.audit_logs.domain.entities.audit_log import (
    AuditAction,
    AuditLog,
    AuditLogFilter,
)


def log(
    action: AuditAction = AuditAction.PROJECT_CREATE,
    actor_id: int = 1,
    at: datetime = datetime(2026, 9, 15, 10, 0, tzinfo=UTC),
) -> AuditLog:
    return AuditLog(action=action, actor_id=actor_id, at=at)


def test_an_empty_filter_holds_everything() -> None:
    """What a screen opens on: the whole register, nothing stated."""
    assert AuditLogFilter().holds(log())


def test_a_line_before_the_period_is_left_out() -> None:
    since = datetime(2026, 9, 16, tzinfo=UTC)

    assert not AuditLogFilter(since=since).holds(log())


def test_a_line_after_the_period_is_left_out() -> None:
    until = datetime(2026, 9, 14, tzinfo=UTC)

    assert not AuditLogFilter(until=until).holds(log())


def test_both_ends_of_the_period_are_included() -> None:
    """« du 15 au 15 » reads the 15th, rather than nothing at all."""
    moment = datetime(2026, 9, 15, 10, 0, tzinfo=UTC)

    assert AuditLogFilter(since=moment, until=moment).holds(log(at=moment))


def test_a_gesture_that_was_not_asked_for_is_left_out() -> None:
    kept = AuditLogFilter(actions=[AuditAction.PROJECT_DELETE])

    assert not kept.holds(log(action=AuditAction.PROJECT_CREATE))
    assert kept.holds(log(action=AuditAction.PROJECT_DELETE))


def test_asking_for_no_gesture_at_all_answers_nothing() -> None:
    """A reader who cleared every box asked for nothing.

    Reading it as « everything » would hand back the whole register to
    somebody who had just said they wanted none of it.
    """
    assert not AuditLogFilter(actions=[]).holds(log())


def test_somebody_else_s_gesture_is_left_out() -> None:
    assert not AuditLogFilter(actor_id=2).holds(log(actor_id=1))


def test_the_criteria_narrow_together() -> None:
    """Three criteria stated is one question, not three."""
    asked = AuditLogFilter(
        since=datetime(2026, 9, 15, tzinfo=UTC),
        actions=[AuditAction.PROJECT_DELETE],
        actor_id=1,
    )

    assert asked.holds(log(action=AuditAction.PROJECT_DELETE, actor_id=1))
    # The right gesture, by the wrong person.
    assert not asked.holds(log(action=AuditAction.PROJECT_DELETE, actor_id=2))
