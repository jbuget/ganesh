"""Un lien utile attache a une mission."""

import pytest

from src.modules.projects.domain.entities.project_link import ProjectLink
from src.shared.exceptions.domain_exceptions import ValidationError


def a_link(label: str = "Cahier des charges", url: str = "https://waat.fr/cdc"):
    return ProjectLink(id=None, project_id=1, label=label, url=url)


def test_a_link_keeps_its_label_and_address() -> None:
    lien = a_link()

    assert (lien.label, lien.url) == ("Cahier des charges", "https://waat.fr/cdc")


def test_surrounding_spaces_are_trimmed() -> None:
    lien = a_link(label="  Maquettes  ", url="  https://figma.com/x  ")

    assert (lien.label, lien.url) == ("Maquettes", "https://figma.com/x")


def test_a_link_without_label_takes_its_address() -> None:
    """Coller une adresse suffit : on ne force pas a la nommer."""
    assert a_link(label="   ").label == "https://waat.fr/cdc"


def test_an_empty_address_is_refused() -> None:
    with pytest.raises(ValidationError):
        a_link(url="   ")


@pytest.mark.parametrize("url", ["javascript:alert(1)", "waat.fr", "ftp://waat.fr"])
def test_only_web_addresses_are_accepted(url: str) -> None:
    """Un lien s'ouvre d'un clic : il ne doit pas pouvoir executer du script."""
    with pytest.raises(ValidationError):
        a_link(url=url)


@pytest.mark.parametrize("url", ["https://waat.fr", "http://intranet/doc"])
def test_http_and_https_are_accepted(url: str) -> None:
    assert a_link(url=url).url == url
