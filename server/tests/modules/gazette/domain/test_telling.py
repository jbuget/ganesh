"""Whose coming and going the gazette tells."""

from src.modules.gazette.domain.services.telling import is_told
from src.modules.users.domain.entities.user import Role, User
from src.shared.enums.department import Department
from src.shared.enums.team import Team


def a_user(team: Team | None, department: Department | None = None) -> User:
    return User(
        id=1,
        entra_oid="oid-1",
        email="a@waat.fr",
        display_name="Ada",
        role=Role.TEAMMATE,
        department=department or (team.department if team else None),
        team=team,
    )


def test_an_engineer_is_told() -> None:
    assert is_told(a_user(Team.ENGINEERING))


def test_another_team_of_the_information_systems_is_not() -> None:
    """The data and network teams share the department, not the gazette."""
    assert not is_told(a_user(Team.DATA))
    assert not is_told(a_user(Team.SYSNET))


def test_somebody_whose_team_nobody_has_said_is_not() -> None:
    """Nothing is supposed of somebody the register knows nothing about."""
    assert not is_told(a_user(None))


def test_somebody_in_another_department_is_not() -> None:
    assert not is_told(a_user(None, Department.INFORMATION_SYSTEMS))
