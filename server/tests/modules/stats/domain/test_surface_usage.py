"""What each function of the product saw over a window."""

from datetime import date

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.stats.domain.entities.surface_usage import (
    SURFACE_OF,
    Surface,
    Tally,
    Trace,
    WindowReading,
)
from src.modules.stats.domain.services.surface_reading import (
    read_surfaces,
    surfaces_last_used,
)

YESTERDAY = date(2026, 9, 16)
LONG_AGO = date(2026, 3, 2)


def reading(
    traces: list[Trace] | None = None,
    tallies: dict[Surface, Tally] | None = None,
) -> WindowReading:
    return WindowReading(traces=tuple(traces or []), tallies=tallies or {})


def trace(action: AuditAction, actor_id: int, gestures: int = 1) -> Trace:
    return Trace(action=action, actor_id=actor_id, gestures=gestures)


def activity(usage, surface: Surface):
    return next(one for one in usage.activities if one.surface is surface)


class TestTheMapOfGestures:
    def test_every_gesture_belongs_to_a_surface(self) -> None:
        # A gesture attached to nothing would drop out of the table in
        # silence, and the table would go on reading as if it were complete.
        assert set(AuditAction) == set(SURFACE_OF)

    def test_every_surface_is_reachable(self) -> None:
        # The other way round: a surface no source feeds is a line that can
        # only ever read zero, which says nothing about the product.
        fed_by_the_log = set(SURFACE_OF.values())
        assert set(Surface) == fed_by_the_log | set(Surface.unlogged())


class TestWhatOneSurfaceSaw:
    def test_a_person_acting_twice_on_one_surface_counts_once(self) -> None:
        usage = read_surfaces(
            reading(
                [
                    trace(AuditAction.PROJECT_CREATE, actor_id=1),
                    trace(AuditAction.PROJECT_UPDATE, actor_id=1),
                ]
            ),
            reading(),
            {},
        )

        assert activity(usage, Surface.PROJECT_REGISTRY).people == 1

    def test_the_gestures_of_a_surface_add_up_across_its_actions(self) -> None:
        usage = read_surfaces(
            reading(
                [
                    trace(AuditAction.PROJECT_CREATE, actor_id=1, gestures=2),
                    trace(AuditAction.PROJECT_DELETE, actor_id=2, gestures=3),
                ]
            ),
            reading(),
            {},
        )

        registry = activity(usage, Surface.PROJECT_REGISTRY)
        assert (registry.people, registry.gestures) == (2, 5)

    def test_a_surface_nobody_touched_still_has_a_line(self) -> None:
        # The zero is the reading: a function nobody used is what the table
        # exists to show.
        usage = read_surfaces(reading(), reading(), {})

        gazette = activity(usage, Surface.GAZETTE)
        assert (gazette.people, gazette.gestures, gazette.is_idle) == (0, 0, True)

    def test_the_surfaces_are_read_in_the_order_they_are_declared(self) -> None:
        # A fixed order makes two windows comparable at a glance, and keeps
        # the idle lines where they can be seen rather than at the bottom.
        usage = read_surfaces(reading(), reading(), {})

        assert [one.surface for one in usage.activities] == list(Surface)


class TestWhatTheLogDoesNotCarry:
    def test_a_surface_outside_the_log_is_read_from_its_own_tally(self) -> None:
        usage = read_surfaces(
            reading(tallies={Surface.MOOD: Tally(people=7, gestures=31)}),
            reading(),
            {},
        )

        mood = activity(usage, Surface.MOOD)
        assert (mood.people, mood.gestures) == (7, 31)


class TestMovement:
    def test_the_delta_counts_people_against_the_previous_window(self) -> None:
        usage = read_surfaces(
            reading(
                [trace(AuditAction.UPDATE_POST, actor_id=id_) for id_ in (1, 2, 3)]
            ),
            reading([trace(AuditAction.UPDATE_POST, actor_id=1)]),
            {},
        )

        assert activity(usage, Surface.PROJECT_UPDATES).delta_in_people == 2

    def test_a_surface_losing_its_people_moves_backwards(self) -> None:
        usage = read_surfaces(
            reading(),
            reading([trace(AuditAction.SIMULATION_CREATE, actor_id=1)]),
            {},
        )

        assert activity(usage, Surface.PLANNING).delta_in_people == -1

    def test_a_surface_outside_the_log_moves_on_its_own_tally(self) -> None:
        usage = read_surfaces(
            reading(tallies={Surface.NOTIFICATIONS: Tally(people=4, gestures=9)}),
            reading(tallies={Surface.NOTIFICATIONS: Tally(people=6, gestures=20)}),
            {},
        )

        assert activity(usage, Surface.NOTIFICATIONS).delta_in_people == -2


class TestTheLastTime:
    def test_the_last_use_is_read_beyond_the_window(self) -> None:
        # « Nothing this month » and « nothing since March » are not the same
        # statement, and only the second one calls for a decision.
        usage = read_surfaces(reading(), reading(), {Surface.GAZETTE: LONG_AGO})

        gazette = activity(usage, Surface.GAZETTE)
        assert (gazette.last_used_on, gazette.never_used) == (LONG_AGO, False)

    def test_a_surface_nobody_ever_touched_carries_no_date(self) -> None:
        usage = read_surfaces(reading(), reading(), {})

        assert activity(usage, Surface.GAZETTE).never_used is True

    def test_the_last_use_of_a_surface_is_the_latest_of_its_gestures(self) -> None:
        last_used = surfaces_last_used(
            gestures={
                AuditAction.PROJECT_CREATE: LONG_AGO,
                AuditAction.PROJECT_UPDATE: YESTERDAY,
            },
            others={},
        )

        assert last_used[Surface.PROJECT_REGISTRY] == YESTERDAY

    def test_the_surfaces_outside_the_log_carry_their_own_last_day(self) -> None:
        last_used = surfaces_last_used(gestures={}, others={Surface.MOOD: YESTERDAY})

        assert last_used[Surface.MOOD] == YESTERDAY


class TestWhatTheTableSaysAsAWhole:
    def test_it_counts_the_functions_nobody_used(self) -> None:
        usage = read_surfaces(
            reading([trace(AuditAction.ENTRY_SET, actor_id=1)]),
            reading(),
            {},
        )

        assert usage.idle_count == len(Surface) - 1
