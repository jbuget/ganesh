"""Who the company lets carry a need to the COMEX."""

import pytest

from src.modules.requests.domain.services.sponsorship import ensure_they_may_sponsor
from src.modules.users.domain.entities.user import Role, User
from src.shared.enums.org_level import OrgLevel
from src.shared.exceptions.domain_exceptions import ValidationError


def make_user(level: OrgLevel | None = OrgLevel.COMEX, is_active: bool = True) -> User:
    return User(
        id=3,
        entra_oid="oid-3",
        email="c.direction@waat.fr",
        display_name="C. Direction",
        role=Role.GUEST,
        is_active=is_active,
        org_level=level,
    )


def test_a_member_of_the_comex_carries_a_need() -> None:
    ensure_they_may_sponsor([make_user()])


def test_the_role_has_nothing_to_do_with_it() -> None:
    """Sponsoring is a place in the company, not a right in the application."""
    sponsor = make_user()
    sponsor.role = Role.MANAGER

    ensure_they_may_sponsor([sponsor])


@pytest.mark.parametrize("level", [OrgLevel.COMOP, OrgLevel.COLLABORATOR, None])
def test_anybody_else_is_refused(level: OrgLevel | None) -> None:
    with pytest.raises(ValidationError):
        ensure_they_may_sponsor([make_user(level)])


def test_a_deactivated_account_carries_nothing() -> None:
    with pytest.raises(ValidationError):
        ensure_they_may_sponsor([make_user(is_active=False)])
