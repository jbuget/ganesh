"""A file dropped on a mission."""

from datetime import UTC, datetime

import pytest

from src.modules.projects.domain.entities.project_attachment import (
    MAX_ATTACHMENT_BYTES,
    ProjectAttachment,
)
from src.shared.exceptions.domain_exceptions import ValidationError

NOW = datetime(2026, 5, 20, 11, 35, tzinfo=UTC)


def build(**changes: object) -> ProjectAttachment:
    fields: dict[str, object] = {
        "id": None,
        "project_id": 1,
        "uploaded_by": 7,
        "filename": "capture.png",
        "content_type": "image/png",
        "size_bytes": 2048,
        "storage_key": "projects/1/2f0c.png",
        "uploaded_at": NOW,
    }
    fields.update(changes)
    return ProjectAttachment(**fields)  # type: ignore[arg-type]


def test_a_file_keeps_the_name_it_was_dropped_under() -> None:
    assert build().filename == "capture.png"


def test_a_name_is_trimmed_of_what_the_browser_left_around_it() -> None:
    assert build(filename="  capture.png  ").filename == "capture.png"


def test_a_file_without_a_name_is_refused() -> None:
    with pytest.raises(ValidationError):
        build(filename="   ")


def test_a_name_is_read_without_the_path_it_was_sent_with() -> None:
    """Some browsers send a whole path. Only the last part names the file."""
    assert build(filename="C:\\Users\\lea\\Bureau\\note.pdf").filename == "note.pdf"
    assert build(filename="captures/écran.png").filename == "écran.png"


def test_an_empty_file_is_refused() -> None:
    with pytest.raises(ValidationError):
        build(size_bytes=0)


def test_a_file_at_the_limit_goes_through() -> None:
    assert build(size_bytes=MAX_ATTACHMENT_BYTES).size_bytes == MAX_ATTACHMENT_BYTES


def test_a_file_over_the_limit_is_refused() -> None:
    with pytest.raises(ValidationError):
        build(size_bytes=MAX_ATTACHMENT_BYTES + 1)


def test_an_image_says_so_and_the_rest_does_not() -> None:
    assert build(content_type="image/jpeg").is_image
    assert not build(content_type="application/pdf").is_image


def test_a_drawing_that_runs_scripts_is_not_an_image_a_screen_may_show() -> None:
    """`is_image` is what a screen draws an `<img>` on, and an SVG is never
    served inline: saying yes here would draw a square that cannot load."""
    assert not build(content_type="image/svg+xml").is_image


def test_a_type_is_read_whatever_it_was_dressed_in() -> None:
    assert build(content_type="IMAGE/PNG; charset=binary").is_image


def test_a_name_cannot_write_a_header_of_its_own() -> None:
    """The name travels in `Content-Disposition`, and a header is one line.

    A « \r\n » in it is not something anybody typed: it is a paste gone wrong
    or an attempt to write a second header, and both end the same way — the
    HTTP layer refuses to send the answer, and every download of that file is
    a 500.
    """
    dressed = build(filename="note\r\nX-Injected: 1.pdf")

    assert dressed.filename == "noteX-Injected: 1.pdf"


def test_a_name_keeps_its_accents_and_its_spaces() -> None:
    """Only what cannot be written down is dropped, never what was typed."""
    assert build(filename="cahier de recette é.pdf").filename == (
        "cahier de recette é.pdf"
    )


def test_a_name_made_only_of_what_cannot_be_written_is_no_name() -> None:
    with pytest.raises(ValidationError):
        build(filename="\r\n\t")


def test_a_file_arriving_with_no_type_is_taken_for_a_stream_of_bytes() -> None:
    """A browser that says nothing must not make the entity guess."""
    assert build(content_type="").content_type == "application/octet-stream"


class TestRenaming:
    """A file may be called something else. Where its bytes sit does not move."""

    def test_a_file_takes_the_name_it_is_given(self) -> None:
        file = build()

        file.rename("cahier de recette.pdf")

        assert file.filename == "cahier de recette.pdf"

    def test_renaming_does_not_move_the_bytes(self) -> None:
        """The key is drawn once and kept: it is not derived from the name."""
        file = build()
        key = file.storage_key

        file.rename("autre chose.png")

        assert file.storage_key == key

    def test_a_new_name_is_read_the_way_the_first_one_was(self) -> None:
        file = build()

        file.rename("  dossiers/capture finale.png  ")

        assert file.filename == "capture finale.png"

    def test_a_file_cannot_be_renamed_to_nothing(self) -> None:
        file = build()

        with pytest.raises(ValidationError):
            file.rename("   ")

        assert file.filename == "capture.png"
