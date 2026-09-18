"""A useful link attached to a mission."""

import pytest

from src.modules.projects.domain.entities.project_link import LinkIcon, ProjectLink
from src.shared.exceptions.domain_exceptions import ValidationError


def a_link(label: str = "Cahier des charges", url: str = "https://waat.fr/cdc"):
    return ProjectLink(id=None, project_id=1, label=label, url=url)


def test_a_link_keeps_its_label_and_address() -> None:
    link = a_link()

    assert (link.label, link.url) == ("Cahier des charges", "https://waat.fr/cdc")


def test_surrounding_spaces_are_trimmed() -> None:
    link = a_link(label="  Maquettes  ", url="  https://figma.com/x  ")

    assert (link.label, link.url) == ("Maquettes", "https://figma.com/x")


def test_a_link_without_label_takes_its_address() -> None:
    """Pasting an address is enough: naming it is not forced."""
    assert a_link(label="   ").label == "https://waat.fr/cdc"


def test_an_empty_address_is_refused() -> None:
    with pytest.raises(ValidationError):
        a_link(url="   ")


@pytest.mark.parametrize("url", ["javascript:alert(1)", "waat.fr", "ftp://waat.fr"])
def test_only_web_addresses_are_accepted(url: str) -> None:
    """A link opens with a click: it must not be able to run script."""
    with pytest.raises(ValidationError):
        a_link(url=url)


@pytest.mark.parametrize("url", ["https://waat.fr", "http://intranet/doc"])
def test_http_and_https_are_accepted(url: str) -> None:
    assert a_link(url=url).url == url


def test_a_link_carries_the_generic_icon_by_default() -> None:
    assert a_link().icon is LinkIcon.LINK


def test_a_link_keeps_the_icon_it_is_given() -> None:
    link = ProjectLink(
        id=None,
        project_id=1,
        label="Maquettes",
        url="https://figma.com/x",
        icon=LinkIcon.DESIGN,
    )

    assert link.icon is LinkIcon.DESIGN


def test_an_icon_outside_the_catalogue_is_refused() -> None:
    """The catalogue is closed: the screen must be able to draw what it gets."""
    with pytest.raises(ValidationError):
        ProjectLink(
            id=None, project_id=1, label="x", url="https://waat.fr", icon="licorne"
        )
