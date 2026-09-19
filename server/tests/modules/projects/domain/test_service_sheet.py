"""The catalogue side of a mission: slug, publication and named addresses."""

import pytest

from src.modules.projects.domain.entities.project import (
    SERVICE_LINK_FIELDS,
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.service_registry import clean_slug
from src.shared.exceptions.domain_exceptions import ValidationError


def make_project(**overrides: object) -> Project:
    fields: dict[str, object] = {
        "id": 1,
        "label": "Portail bailleurs",
        "kind": ProjectKind.PROJECT,
        "status": ProjectStatus.OPERATIONS,
    }
    fields.update(overrides)
    return Project(**fields)  # type: ignore[arg-type]


class TestSlug:
    def test_a_slug_is_kept_as_typed_when_it_reads_as_an_address(self) -> None:
        assert clean_slug("portail-bailleurs") == "portail-bailleurs"

    def test_a_slug_is_trimmed_and_lowered(self) -> None:
        assert clean_slug("  Portail-Bailleurs  ") == "portail-bailleurs"

    def test_an_empty_slug_is_no_slug(self) -> None:
        assert clean_slug("   ") is None

    @pytest.mark.parametrize(
        "slug",
        ["portail bailleurs", "portail_bailleurs", "-portail", "portail-", "a--b", "é"],
    )
    def test_what_would_not_make_a_readable_address_is_refused(self, slug: str) -> None:
        with pytest.raises(ValidationError):
            clean_slug(slug)

    def test_a_slug_longer_than_the_column_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            clean_slug("a" * 101)


class TestNamedAddresses:
    def test_an_address_is_trimmed(self) -> None:
        project = make_project(repository_link="  https://github.com/waat-fr/x  ")
        assert project.repository_link == "https://github.com/waat-fr/x"

    def test_an_empty_address_comes_back_absent(self) -> None:
        assert make_project(production_link="   ").production_link is None

    def test_an_address_that_does_not_open_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            make_project(documentation_link="javascript:alert(1)")

    def test_every_named_address_obeys_the_same_rule(self) -> None:
        for field in SERVICE_LINK_FIELDS:
            with pytest.raises(ValidationError):
                make_project(**{field: "ftp://example.com"})


class TestPublication:
    def test_a_mission_is_not_published_until_it_is_said_to_be(self) -> None:
        assert make_project().is_published is False

    def test_publishing_asks_for_a_slug_and_a_summary(self) -> None:
        project = make_project(
            is_published=True, slug="portail-bailleurs", summary="Un portail."
        )
        assert project.is_published is True

    def test_a_published_mission_without_a_slug_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            make_project(is_published=True, summary="Un portail.")

    def test_a_published_mission_without_a_summary_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            make_project(is_published=True, slug="portail-bailleurs")

    def test_off_project_work_cannot_be_published(self) -> None:
        with pytest.raises(ValidationError):
            make_project(
                kind=ProjectKind.OFF_PROJECT,
                status=None,
                is_published=True,
                slug="conges",
                summary="Absences.",
            )

    def test_an_unpublished_mission_may_leave_everything_blank(self) -> None:
        project = make_project()
        assert project.slug is None
        assert project.summary is None
        assert project.criticality is None
