"""How a file is handed to a browser."""

from src.modules.projects.presentation.api.attachment_serving import (
    DOWNLOAD_TYPE,
    disposition,
    served_as,
)


class TestWhatMayBeShown:
    def test_a_photograph_is_shown(self) -> None:
        assert served_as("image/png") == "image/png"
        assert served_as("image/jpeg") == "image/jpeg"

    def test_a_pdf_and_plain_text_are_shown(self) -> None:
        assert served_as("application/pdf") == "application/pdf"
        assert served_as("text/plain") == "text/plain"

    def test_a_drawing_that_runs_scripts_is_never_shown(self) -> None:
        """An SVG reads as an image and is a document: inline from our own
        domain it would run its scripts in the reader's session."""
        assert served_as("image/svg+xml") is None
        assert served_as("image/svg+xml; charset=utf-8") is None

    def test_a_page_is_never_shown(self) -> None:
        assert served_as("text/html") is None

    def test_what_nobody_thought_of_is_not_shown(self) -> None:
        assert served_as("application/zip") is None
        assert served_as(DOWNLOAD_TYPE) is None

    def test_a_type_is_read_whatever_it_was_dressed_in(self) -> None:
        """The parameters and the case are the sender's; the type is ours."""
        assert served_as("  IMAGE/PNG ; charset=binary ") == "image/png"

    def test_what_is_shown_is_named_by_the_list_and_not_by_the_sender(self) -> None:
        """What goes on the wire is a member of the list, never the stored
        string: a type nobody checked has no business in a header."""
        assert served_as("image/png; boundary=--\r\nX-Injected: 1") == "image/png"


class TestTellingTheBrowser:
    def test_a_file_to_show_is_announced_inline(self) -> None:
        assert disposition("capture.png", as_download=False).startswith("inline;")

    def test_a_file_to_save_is_announced_as_an_attachment(self) -> None:
        assert disposition("capture.png", as_download=True).startswith("attachment;")

    def test_the_name_travels_twice(self) -> None:
        said = disposition("capture.png", as_download=True)

        assert 'filename="capture.png"' in said
        assert "filename*=utf-8''capture.png" in said

    def test_an_accent_survives_a_header_that_cannot_carry_it(self) -> None:
        said = disposition("cahier de recette é.pdf", as_download=True)

        # A header is latin-1: the plain form gives up the accent so that the
        # encoded one, which keeps it, can be read by whoever understands it.
        assert said.isascii()
        assert "filename*=utf-8''cahier%20de%20recette%20%C3%A9.pdf" in said

    def test_a_quote_in_a_name_cannot_close_the_header(self) -> None:
        """Otherwise a name could write a header of its own."""
        said = disposition('re"nommé.png', as_download=True)

        assert 'filename="renommé.png"' not in said
        assert said.count('"') == 2
