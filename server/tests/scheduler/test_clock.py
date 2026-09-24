"""The loop: what it takes, what it leaves, and what it survives."""

import asyncio
import contextlib
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from src.modules.notifications.domain.repositories.mailer import MailerUnavailableError
from src.modules.users.domain.entities.reminder_cadence import ReminderCadence
from src.scheduler.clock import ReminderClock
from src.scheduler.due import PARIS

AT = time(8, 30)
WEDNESDAY = datetime(2026, 9, 23, 8, 45, tzinfo=PARIS)
SATURDAY = datetime(2026, 9, 26, 9, 0, tzinfo=PARIS)
MONDAY = datetime(2026, 9, 21, 9, 0, tzinfo=PARIS)


def build(
    claims: bool = True,
    sent: int = 1,
    fails: bool = False,
    send_at: time = AT,
    nowhere_to_post: bool = False,
):
    taken: list[tuple[str, date]] = []
    rounds: list[ReminderCadence] = []
    given_back: list[tuple[str, date]] = []

    async def claim_run(job: str, due_on: date, at: datetime) -> bool:
        taken.append((job, due_on))
        return claims

    async def run_round(cadence: ReminderCadence, now: datetime) -> int:
        if nowhere_to_post:
            raise MailerUnavailableError("the mail server refused our credentials")
        if fails:
            raise RuntimeError("the mail server fell over")
        rounds.append(cadence)
        return sent

    async def release_run(job: str, due_on: date) -> None:
        given_back.append((job, due_on))

    clock = ReminderClock(
        send_at=send_at,
        tick_seconds=1,
        claim_run=claim_run,
        run_round=run_round,
        release_run=release_run,
    )
    return clock, taken, rounds, given_back


class TestWhatOneTickDoes:
    async def test_it_runs_the_daily_round_on_a_working_day(self) -> None:
        clock, taken, rounds, given_back = build()

        assert await clock.tick(WEDNESDAY) == 1
        assert rounds == [ReminderCadence.DAILY]
        assert taken == [("reminder:daily", date(2026, 9, 23))]

    async def test_it_runs_both_rounds_on_the_first_working_day(self) -> None:
        clock, _, rounds, _ = build()

        await clock.tick(MONDAY)

        assert rounds == [ReminderCadence.DAILY, ReminderCadence.WEEKLY]

    async def test_a_day_nobody_works_claims_nothing_at_all(self) -> None:
        clock, taken, rounds, given_back = build()

        assert await clock.tick(SATURDAY) == 0
        assert taken == [] and rounds == []

    async def test_a_run_is_claimed_under_the_paris_day(self) -> None:
        # 22:30 UTC on 22 September is 00:30 Paris on the 23rd — a Wednesday.
        # The round is decided on the Paris day, so the claim has to be taken
        # under it: `astimezone()` with no argument reads the machine's own
        # zone, and on a host in UTC that is the 22nd.
        clock, taken, _, _ = build(send_at=time(0, 0))
        late = datetime(2026, 9, 22, 22, 30, tzinfo=ZoneInfo("UTC"))

        await clock.tick(late)

        assert taken == [("reminder:daily", date(2026, 9, 23))]


class TestWhenSomebodyElseGotThere:
    async def test_a_round_it_did_not_claim_is_not_run(self) -> None:
        # The ordinary case behind several workers, not a failure.
        clock, taken, rounds, given_back = build(claims=False)

        assert await clock.tick(WEDNESDAY) == 0
        assert taken != [] and rounds == []


class TestTheClockSurvivesABadMorning:
    async def test_a_failed_tick_does_not_stop_the_loop(self) -> None:
        clock, _, _, _ = build(fails=True)

        task = asyncio.create_task(clock.run_forever())
        await asyncio.sleep(0.05)
        still_running = not task.done()
        task.cancel()

        assert still_running

    async def test_cancelling_stops_it(self) -> None:
        clock, _, _, _ = build()

        task = asyncio.create_task(clock.run_forever())
        await asyncio.sleep(0.01)
        task.cancel()

        with contextlib.suppress(asyncio.CancelledError):
            await task
        assert task.cancelled() or task.done()


class TestWhenThereIsNowhereToPost:
    async def test_the_run_is_given_back_so_the_next_tick_retries(self) -> None:
        # The claim is taken before the work — it has to be — so without
        # giving it back, a key refused at 8 h 30 costs the whole day.
        clock, taken, _, given_back = build(nowhere_to_post=True)

        assert await clock.tick(WEDNESDAY) == 0
        assert taken == [("reminder:daily", date(2026, 9, 23))]
        assert given_back == [("reminder:daily", date(2026, 9, 23))]

    async def test_the_tick_stops_rather_than_trying_the_next_cadence(self) -> None:
        # Monday owes both rounds, and the second would meet the same wall.
        clock, _, _, given_back = build(nowhere_to_post=True)

        await clock.tick(MONDAY)

        assert given_back == [("reminder:daily", date(2026, 9, 21))]

    async def test_it_does_not_take_the_loop_down_with_it(self) -> None:
        clock, _, _, _ = build(nowhere_to_post=True)

        task = asyncio.create_task(clock.run_forever())
        await asyncio.sleep(0.05)
        still_running = not task.done()
        task.cancel()

        assert still_running


class TestAnOrdinaryFailureIsNotGivenBack:
    async def test_a_round_that_blew_up_keeps_its_claim(self) -> None:
        # Only « nowhere to post » is worth retrying within the day. Anything
        # else would spin every five minutes until midnight.
        clock, _, _, given_back = build(fails=True)

        with contextlib.suppress(RuntimeError):
            await clock.tick(WEDNESDAY)

        assert given_back == []
