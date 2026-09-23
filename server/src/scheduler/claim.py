"""Who does the work when several processes wake up at once.

The API runs as one `uvicorn` process today, so an in-process task fires once.
`--workers 4` is one word away and is the obvious first thing to reach for the
day the host feels slow — and a naive clock would then send four letters to
everybody, silently, and only in production.

So the number of processes is made not to matter. Each tick tries to insert the
run it is about to do; the primary key refuses the second one. **The uniqueness
constraint is the lock**, and it buys idempotence with it: a deploy at 9 h does
not re-send the round of 8 h 30, and neither does a crash-restart.
"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, String
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class ScheduledRunModel(Base):
    """One scheduled thing, done once for one day.

    `job` rather than a table named after the single job there is: it is one
    column, and it makes a row mean « this run, on this day » instead of « the
    reminder, on this day ».
    """

    __tablename__ = "scheduled_run"

    job: Mapped[str] = mapped_column(String(64), primary_key=True)
    due_on: Mapped[date] = mapped_column(Date, primary_key=True)
    claimed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


async def claim(session: AsyncSession, job: str, due_on: date, at: datetime) -> bool:
    """Takes the run, or finds it already taken. Tells which.

    Committed on the spot, and deliberately: the claim has to be visible to
    every other process before the work starts, not once it has finished.
    """
    result = await session.execute(
        insert(ScheduledRunModel)
        .values(job=job, due_on=due_on, claimed_at=at)
        .on_conflict_do_nothing(index_elements=["job", "due_on"])
    )
    await session.commit()
    return bool(result.rowcount)
