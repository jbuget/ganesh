"""The teams a department is cut into."""

from src.shared.enums.department import Department
from src.shared.enums.team import Team, teams_of


def test_information_systems_is_cut_into_three_teams_read_alphabetically() -> None:
    assert teams_of(Department.INFORMATION_SYSTEMS) == [
        Team.DATA,
        Team.ENGINEERING,
        Team.SYSNET,
    ]


def test_a_department_nobody_has_cut_into_teams_offers_none() -> None:
    """Nothing is supposed: a department says its teams, or has none."""
    assert teams_of(Department.CUSTOMER_SERVICE) == []


def test_every_team_hangs_from_a_department() -> None:
    """A team added without its department would be offered nowhere."""
    for team in Team:
        assert team in teams_of(team.department)
