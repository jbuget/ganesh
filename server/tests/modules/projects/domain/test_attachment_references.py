"""Which files a message shows."""

from src.modules.projects.domain.services.attachment_references import referenced_ids


def test_a_message_showing_nothing_references_nothing() -> None:
    assert referenced_ids("Revue faite, rien à signaler.") == set()


def test_an_image_pasted_in_a_message_is_read_by_its_id() -> None:
    body = "Le bug : ![capture](/api/v1/projects/4/attachments/12/content)"

    assert referenced_ids(body) == {12}


def test_a_plain_link_to_a_file_counts_as_showing_it() -> None:
    """Withdrawing the file would break the link just as surely."""
    body = "Le compte rendu : [note.pdf](/api/v1/projects/4/attachments/9/content)"

    assert referenced_ids(body) == {9}


def test_the_same_file_shown_twice_is_counted_once() -> None:
    body = (
        "![a](/api/v1/projects/4/attachments/12/content) "
        "![encore](/api/v1/projects/4/attachments/12/content)"
    )

    assert referenced_ids(body) == {12}


def test_a_link_that_only_looks_like_one_is_not_one() -> None:
    assert (
        referenced_ids("[ailleurs](https://waat.tools/attachments/12/content)") == set()
    )
