"""The dates a mission reached its phases."""

from datetime import date

from src.modules.projects.domain.entities.project import ProjectStatus
from src.modules.projects.domain.services.phase_history import (
    previous_phases,
    transition_label,
)


def test_reaching_a_phase_implies_the_previous_ones() -> None:
    """A project imported in Deployment did go through the earlier phases."""
    assert previous_phases(ProjectStatus.DEPLOYMENT) == [
        ProjectStatus.EXPLORATION,
        ProjectStatus.SCOPING,
        ProjectStatus.DEVELOPMENT,
        ProjectStatus.VALIDATION,
    ]


def test_the_first_phase_has_nothing_before_it() -> None:
    assert previous_phases(ProjectStatus.EXPLORATION) == []


def test_a_passage_is_named_after_what_it_achieves() -> None:
    """\u00ab Valide le \u00bb reads better than \u00ab entre en deploiement le \u00bb."""
    assert transition_label(ProjectStatus.DEPLOYMENT) == "Validé"
    assert transition_label(ProjectStatus.OPERATIONS) == "Déployé"


def test_every_phase_can_be_named() -> None:
    assert all(transition_label(status) for status in ProjectStatus)


def test_a_phase_date_is_not_lost_when_a_project_goes_back() -> None:
    """Going back does not erase what happened: the service only states the
    order of the phases, it allows no deletion."""
    assert ProjectStatus.VALIDATION in previous_phases(ProjectStatus.OPERATIONS)


def test_phases_are_ordered_as_declared() -> None:
    assert previous_phases(ProjectStatus.SCOPING) == [ProjectStatus.EXPLORATION]


def test_a_date_marks_the_entry_into_a_phase() -> None:
    """The \u00ab Valide \u00bb date is the one of entering Deployment."""
    start = date(2026, 9, 17)
    assert (transition_label(ProjectStatus.DEPLOYMENT), start) == ("Validé", start)
