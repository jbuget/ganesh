"""Whose time the coverage of the entry is read over."""

from src.modules.stats.domain.entities.statistics import CoverageScope
from src.modules.users.domain.entities.user import User
from src.shared.enums.team import Team

#: The one team the coverage is measured on. The others are left out of both
#: sides of the ratio — what they declare and what they would owe — rather
#: than out of one, which would only move the figure without saying why.
MEASURED_TEAM = Team.ENGINEERING


def measured_by_coverage(team: list[User]) -> list[User]:
    """The teammates the coverage counts, out of the whole team."""
    return [user for user in team if user.team is MEASURED_TEAM]


def coverage_scope(measured: list[User]) -> CoverageScope:
    return CoverageScope(team=MEASURED_TEAM, people=len(measured))
