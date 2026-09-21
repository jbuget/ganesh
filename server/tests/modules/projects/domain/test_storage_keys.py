"""Where a file is put down in the store."""

from src.modules.projects.domain.services.storage_keys import key_for


def test_a_key_is_filed_under_the_mission_it_belongs_to() -> None:
    assert key_for(42, "capture.png").startswith("projects/42/")


def test_a_key_keeps_the_suffix_so_the_store_can_be_read_by_a_human() -> None:
    assert key_for(42, "capture.PNG").endswith(".png")


def test_a_file_with_no_suffix_gets_a_key_with_none() -> None:
    key = key_for(42, "notes")

    assert key.startswith("projects/42/")
    assert "." not in key.rsplit("/", 1)[1]


def test_two_files_of_the_same_name_never_share_a_key() -> None:
    """Otherwise the second drop would silently erase the first."""
    assert key_for(42, "capture.png") != key_for(42, "capture.png")


def test_the_name_given_by_the_user_never_reaches_the_key() -> None:
    """A name is not a path: it carries slashes, dots and anything else."""
    key = key_for(42, "../../etc/passwd")

    assert key.startswith("projects/42/")
    assert ".." not in key
    assert key.count("/") == 2
