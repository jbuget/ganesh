"""Who may carry a need to the COMEX.

The company works by one rule here: a need reaches the COMEX through one of
its members. Ganesh holds that rule rather than trusting the picker to only
ever offer the right names — a request arriving by any other door is refused
the same way.
"""

from src.modules.users.domain.entities.user import User
from src.shared.enums.org_level import OrgLevel
from src.shared.exceptions.domain_exceptions import ValidationError


def ensure_they_may_sponsor(sponsors: list[User]) -> None:
    """Refuses anybody who does not sit in the COMEX, or no longer comes in."""
    for sponsor in sponsors:
        if sponsor.org_level is not OrgLevel.COMEX:
            raise ValidationError(
                "A request is carried to the COMEX by one of its members."
            )
        if not sponsor.is_active:
            raise ValidationError("A deactivated account carries nothing.")
