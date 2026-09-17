"""Les dates auxquelles une mission a atteint ses phases."""

from datetime import date

from src.modules.projects.domain.entities.project import ProjectStatus
from src.modules.projects.domain.services.phase_history import (
    previous_phases,
    transition_label,
)


def test_reaching_a_phase_implies_the_previous_ones() -> None:
    """Un projet importe en Deploiement a bien traverse les phases d'avant."""
    assert previous_phases(ProjectStatus.DEPLOYMENT) == [
        ProjectStatus.EXPLORATION,
        ProjectStatus.SCOPING,
        ProjectStatus.BUILD,
        ProjectStatus.VALIDATION,
    ]


def test_the_first_phase_has_nothing_before_it() -> None:
    assert previous_phases(ProjectStatus.EXPLORATION) == []


def test_a_passage_is_named_after_what_it_achieves() -> None:
    """« Validé le » se lit mieux que « entré en déploiement le »."""
    assert transition_label(ProjectStatus.DEPLOYMENT) == "Validé"
    assert transition_label(ProjectStatus.OPERATIONS) == "Déployé"


def test_every_phase_can_be_named() -> None:
    assert all(transition_label(status) for status in ProjectStatus)


def test_a_phase_date_is_not_lost_when_a_project_goes_back() -> None:
    """Revenir en arriere n'efface pas ce qui a eu lieu : le service ne dit
    que l'ordre des phases, il n'autorise aucune suppression."""
    assert ProjectStatus.VALIDATION in previous_phases(ProjectStatus.OPERATIONS)


def test_phases_are_ordered_as_declared() -> None:
    assert previous_phases(ProjectStatus.SCOPING) == [ProjectStatus.EXPLORATION]


def test_a_date_marks_the_entry_into_a_phase() -> None:
    """La date de « Valide » est celle de l'entree en Deploiement."""
    start = date(2026, 9, 17)
    assert (transition_label(ProjectStatus.DEPLOYMENT), start) == ("Validé", start)
