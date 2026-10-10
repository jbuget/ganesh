"""Whose coming and going the gazette tells.

The gazette is read across the company, and the people it names arriving,
returning or leaving are the engineering team's: that is the team the digest
speaks for. A newcomer in another team of the information systems, or in
another department altogether, is not the gazette's to announce — and one whose
team nobody has said is not announced either, since nothing is supposed of
somebody the register knows nothing about.

Read off the team as it stands the day the digest is read: an account is
created the first time somebody signs in, long before anybody says where they
work, so the team at the day of the gesture would almost never be known.
"""

from src.modules.users.domain.entities.user import User
from src.shared.enums.team import Team

#: The one team whose arrivals and departures are told. Written as a team and
#: not as a department: the information systems also hold the data and the
#: network teams, which the gazette does not speak for.
TOLD_TEAM = Team.ENGINEERING


def is_told(user: User) -> bool:
    """Whether this teammate's arrival or departure belongs in the gazette."""
    return user.team is TOLD_TEAM
