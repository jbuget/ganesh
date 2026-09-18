"""The link icon catalogue, and what an address lets one guess."""

import pytest

from src.modules.projects.domain.entities.project_link import LinkIcon
from src.modules.projects.domain.services.link_icons import guess_icon


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://github.com/waat/timesheet", "repository"),
        ("https://gitlab.com/waat/timesheet", "repository"),
        ("https://www.figma.com/file/abc/Maquettes", "design"),
        ("https://waat.slack.com/archives/C123", "discussion"),
        ("https://waat.monday.com/boards/42", "ticket"),
        ("https://drive.google.com/drive/folders/abc", "folder"),
        ("https://waat.sharepoint.com/sites/projets", "folder"),
        ("https://meet.google.com/abc-defg-hij", "video"),
        ("https://www.notion.so/waat/Cadrage", "document"),
    ],
)
def test_a_known_service_is_recognised(url: str, expected: str) -> None:
    assert guess_icon(url) == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://docs.google.com/document/d/abc/edit", "document"),
        ("https://docs.google.com/spreadsheets/d/abc/edit", "spreadsheet"),
        ("https://docs.google.com/presentation/d/abc/edit", "presentation"),
    ],
)
def test_google_documents_are_told_apart_by_their_path(url: str, expected: str) -> None:
    """One domain serves three tools: the path is what tells them apart."""
    assert guess_icon(url) == expected


def test_a_subdomain_is_recognised_like_its_domain() -> None:
    assert guess_icon("https://pages.github.com/waat") == "repository"


def test_the_host_is_read_without_regard_to_case() -> None:
    assert guess_icon("https://GitHub.com/waat") == "repository"


@pytest.mark.parametrize(
    "url",
    ["https://waat.fr/cdc", "http://intranet/doc", "https://exemple.test"],
)
def test_an_unknown_address_falls_back_on_the_generic_icon(url: str) -> None:
    assert guess_icon(url) == LinkIcon.LINK


def test_an_address_that_only_resembles_a_known_service_is_not_matched() -> None:
    """`myfigma.com` is not Figma: the suffix hinges on a dot."""
    assert guess_icon("https://monfigma.com/x") == LinkIcon.LINK
