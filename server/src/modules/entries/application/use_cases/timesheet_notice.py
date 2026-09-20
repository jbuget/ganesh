"""What every write on a month owes to whoever's month it is."""

from datetime import date

from src.modules.notifications.domain.entities.notification import NotificationKind
from src.modules.notifications.domain.services.delivery import NotificationDelivery
from src.modules.notifications.domain.services.fan_out import notify
from src.shared.utils import clock


async def tell_the_owner(
    notifications: NotificationDelivery,
    actor_id: int,
    owner_id: int,
    day: date,
) -> None:
    """Tells whoever's month it is that somebody else wrote in it.

    Shared by the four gestures that touch a month — an entry set, an entry
    cleared, a project lined up, a project taken off — because they are one
    thing to be told about: « quelqu'un a touché à ma feuille ».

    The line carries the month and never the day, which is what folds a whole
    month filled in cell by cell into a single notification with a count. Four
    use cases that each wrote their own would drift apart on exactly that.
    """
    await notifications.deliver(
        notify(
            NotificationKind.TIMESHEET_EDITED,
            actor_id=actor_id,
            recipients=[owner_id],
            at=clock.now(),
            day=day.replace(day=1),
        )
    )
