"""What of the team's own words a model is handed."""

from src.modules.gazette.domain.services.excerpting import (
    MAX_CHARACTERS,
    MAX_PER_PROJECT,
    clean,
    excerpts_of,
)
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from tests.helpers.instants import paris


def an_update(body: str, day: int = 10, deleted: bool = False) -> ProjectUpdate:
    update = ProjectUpdate(
        id=day,
        project_id=1,
        author_id=1,
        body=body,
        published_at=paris(2026, 9, day, 10),
    )
    if deleted:
        update.remove(by=1, at=paris(2026, 9, day, 11))
    return update


class TestClean:
    def test_a_mention_becomes_a_colleague_and_names_nobody(self) -> None:
        text = clean("Merci @[Sam Okafor](mention://user/12) pour le retour.")

        assert text == "Merci un collègue pour le retour."
        assert "Sam" not in text

    def test_an_image_is_dropped(self) -> None:
        assert clean("Voici l'écran ![capture](/api/v1/x/content) livré.") == (
            "Voici l'écran livré."
        )

    def test_a_link_keeps_its_words_and_loses_its_address(self) -> None:
        assert clean("Voir [la fiche](https://example.com/x).") == "Voir la fiche."

    def test_whitespace_is_collapsed(self) -> None:
        assert clean("Un\n\nmot   de\tplus") == "Un mot de plus"

    def test_a_long_update_is_cut_on_a_word(self) -> None:
        text = clean("mot " * 500)

        assert len(text) <= MAX_CHARACTERS + 1
        assert text.endswith("…")
        assert not text.endswith(" …")


class TestExcerptsOf:
    def test_they_come_oldest_first(self) -> None:
        excerpts = excerpts_of([an_update("Second.", 12), an_update("Premier.", 3)])

        assert excerpts == ("Premier.", "Second.")

    def test_a_withdrawn_update_is_left_out(self) -> None:
        assert excerpts_of(
            [an_update("Gardé."), an_update("Retiré.", 11, deleted=True)]
        ) == ("Gardé.",)

    def test_only_the_most_recent_are_kept(self) -> None:
        updates = [an_update(f"Message {day}", day) for day in range(1, 29)]

        excerpts = excerpts_of(updates)

        assert len(excerpts) == MAX_PER_PROJECT
        assert excerpts[-1] == "Message 28"
        assert excerpts[0] == f"Message {28 - MAX_PER_PROJECT + 1}"
