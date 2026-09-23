"""The loop: wake up, see what is owed, take it if nobody else has.

A third way in, beside the routers and the tools — they answer a request and a
sentence, this one answers a clock. It holds no business rule: what is owed is
`due.cadences_due`, who gets a letter is a use case, and taking the run is the
ledger. What is left here is waking up, and not falling over.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime, time

from src.modules.users.domain.entities.reminder_cadence import ReminderCadence
from src.scheduler.due import JOB, PARIS, cadences_due

logger = logging.getLogger(__name__)

#: Takes the run named, for that day. Answers whether this process got it.
Claimer = Callable[[str, date, datetime], Awaitable[bool]]

#: Writes to everybody on one cadence. Answers how many letters went out.
Round = Callable[[ReminderCadence, datetime], Awaitable[int]]


class ReminderClock:
    """Wakes every so often and sends what is owed, once.

    Its collaborators are handed in rather than built: the loop is then tested
    without a database and without a mail server, and what touches either is
    one small function in `wiring`.
    """

    def __init__(
        self,
        send_at: time,
        tick_seconds: int,
        claim_run: Claimer,
        run_round: Round,
    ) -> None:
        self._send_at = send_at
        self._tick_seconds = tick_seconds
        self._claim_run = claim_run
        self._run_round = run_round

    async def tick(self, now: datetime) -> int:
        """One look at the clock. Answers how many letters went out.

        A round this process did not claim is a round somebody else is doing,
        which is the ordinary case behind several workers and not a failure.
        """
        sent = 0
        for cadence in cadences_due(now, self._send_at):
            # Paris, explicitly: `astimezone()` with no argument reads the
            # machine's own timezone, and a claim taken under the host's day
            # would not be the day the round was decided on.
            due_on = now.astimezone(PARIS).date()
            job = f"{JOB}:{cadence.value.lower()}"
            if not await self._claim_run(job, due_on, now):
                continue
            logger.info("Reminder round %s claimed for %s", cadence.value, due_on)
            sent += await self._run_round(cadence, now)
        return sent

    async def run_forever(self) -> None:
        """Ticks until cancelled.

        Nothing raised inside a tick is allowed out: a task that died on one
        bad morning would take every following morning with it, silently.
        """
        logger.info(
            "Reminder clock started: every %ss, letters at %s Paris time.",
            self._tick_seconds,
            self._send_at.isoformat(timespec="minutes"),
        )
        while True:
            try:
                await self.tick(datetime.now(UTC))
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Reminder tick failed; the clock carries on.")
            await asyncio.sleep(self._tick_seconds)
