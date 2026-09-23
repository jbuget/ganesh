"""The loop: what it takes, what it leaves, and what it survives."""

import asyncio
import contextlib
from datetime import date, datetime, time

from src.modules.users.domain.entities.reminder_cadence import ReminderCadence
from src.scheduler.clock import ReminderClock
from src.scheduler.due import PARIS

AT = time(8, 30)
WEDNESDAY = datetime(2026, 9, 23, 8, 45, tzinfo=PARIS)
SATURDAY = datetime(2026, 9, 26, 9, 0, tzinfo=PARIS)
MONDAY = datetime(2026, 9, 21, 9, 0, tzinfo=PARIS)


def build(claims: bool = True, sent: int = 1, fails: bool = False):
    taken: list[tuple[str, date]] = []
    rounds: list[ReminderCadence] = []

    async def claim_run(job: str, due_on: date, at: datetime) -> bool:
        taken.append((job, due_on))
        return claims

    async def run_round(cadence: ReminderCadence, now: datetime) -> int:
        if fails:
            raise RuntimeError("the mail server fell over")
        rounds.append(cadence)
        return sent

    clock = ReminderClock(
        send_at=AT, tick_seconds=1, claim_run=claim_run, run_round=run_round
    )
    return clock, taken, rounds


class TestWhatOneTickDoes:
    async def test_it_runs_the_daily_round_on_a_working_day(self) -> None:
        clock, taken, rounds = build()

        assert await clock.tick(WEDNESDAY) == 1
        assert rounds == [ReminderCadence.DAILY]
        assert taken == [("reminder:daily", date(2026, 9, 23))]

    async def test_it_runs_both_rounds_on_the_first_working_day(self) -> None:
        clock, _, rounds = build()

        await clock.tick(MONDAY)

        assert rounds == [ReminderCadence.DAILY, ReminderCadence.WEEKLY]

    async def test_a_day_nobody_works_claims_nothing_at_all(self) -> None:
        clock, taken, rounds = build()

        assert await clock.tick(SATURDAY) == 0
        assert taken == [] and rounds == []


class TestWhenSomebodyElseGotThere:
    async def test_a_round_it_did_not_claim_is_not_run(self) -> None:
        # The ordinary case behind several workers, not a failure.
        clock, taken, rounds = build(claims=False)

        assert await clock.tick(WEDNESDAY) == 0
        assert taken != [] and rounds == []


class TestTheClockSurvivesABadMorning:
    async def test_a_failed_tick_does_not_stop_the_loop(self) -> None:
        clock, _, _ = build(fails=True)

        task = asyncio.create_task(clock.run_forever())
        await asyncio.sleep(0.05)
        still_running = not task.done()
        task.cancel()

        assert still_running

    async def test_cancelling_stops_it(self) -> None:
        clock, _, _ = build()

        task = asyncio.create_task(clock.run_forever())
        await asyncio.sleep(0.01)
        task.cancel()

        with contextlib.suppress(asyncio.CancelledError):
            await task
        assert task.cancelled() or task.done()
