"""How a file is handed to a browser."""

from src.modules.projects.presentation.api.attachment_serving import (
    disposition,
    may_be_shown,
)


class TestWhatMayBeShown:
    def test_an_image_is_shown(self) -> None:
        assert may_be_shown("image/png")
        assert may_be_shown("image/svg+xml") is True

    def test_a_pdf_and_plain_text_are_shown(self) -> None:
        assert may_be_shown("application/pdf")
        assert may_be_shown("text/plain")

    def test_a_page_is_never_shown(self) -> None:
        """Inline from our own domain, it would run in the reader's session."""
        assert not may_be_shown("text/html")

    def test_what_nobody_thought_of_is_not_shown(self) -> None:
        assert not may_be_shown("application/zip")
        assert not may_be_shown("application/octet-stream")


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
