"""The month arranged as a chronicle: one chapter per mission."""

from datetime import datetime

from src.modules.gazette.domain.entities.movement import Movement, MovementKind
from src.modules.gazette.domain.services.chaptering import into_chapters


def a_movement(
    subject: str = "Ganesh",
    project_id: int | None = 7,
    day: int = 3,
    parent_id: int | None = None,
    parent_label: str | None = None,
    kind: MovementKind = MovementKind.PROJECT_CREATED,
) -> Movement:
    return Movement(
        kind=kind,
        at=datetime(2026, 9, day, 9),
        subject=subject,
        project_id=project_id,
        parent_id=parent_id,
        parent_label=parent_label,
    )


class TestIntoChapters:
    def test_a_month_nothing_happened_in_has_no_chapter(self) -> None:
        assert into_chapters([]) == []

    def test_one_mission_gathers_its_own_movements(self) -> None:
        chapters = into_chapters(
            [a_movement(day=3), a_movement(day=9), a_movement(day=20)]
        )

        assert len(chapters) == 1
        assert chapters[0].project_id == 7
        assert chapters[0].label == "Ganesh"
        assert [m.at.day for m in chapters[0].movements] == [3, 9, 20]

    def test_missions_are_told_apart(self) -> None:
        chapters = into_chapters(
            [
                a_movement("Ganesh", project_id=7),
                a_movement("NOMAD", project_id=8),
            ]
        )

        assert [chapter.label for chapter in chapters] == ["Ganesh", "NOMAD"]

    def test_a_mission_opens_its_chapter_where_it_first_appears(self) -> None:
        """The chronicle keeps its chronological spine, one step up."""
        chapters = into_chapters(
            [
                a_movement("NOMAD", project_id=8, day=2),
                a_movement("Ganesh", project_id=7, day=1),
                a_movement("NOMAD", project_id=8, day=25),
            ]
        )

        assert [chapter.label for chapter in chapters] == ["Ganesh", "NOMAD"]

    def test_a_package_is_told_inside_its_project(self) -> None:
        chapters = into_chapters(
            [
                a_movement("Ganesh", project_id=7, day=1),
                a_movement(
                    "Lot API", project_id=9, day=2, parent_id=7, parent_label="Ganesh"
                ),
            ]
        )

        assert len(chapters) == 1
        assert chapters[0].label == "Ganesh"
        assert [package.label for package in chapters[0].packages] == ["Lot API"]

    def test_a_project_untouched_but_whose_package_moved_still_opens(self) -> None:
        """A package on its own would be read as a project it is not."""
        chapters = into_chapters(
            [
                a_movement(
                    "Lot API", project_id=9, day=2, parent_id=7, parent_label="Ganesh"
                )
            ]
        )

        assert [chapter.label for chapter in chapters] == ["Ganesh"]
        assert chapters[0].movements == []
        assert [package.label for package in chapters[0].packages] == ["Lot API"]

    def test_a_package_carries_its_own_movements(self) -> None:
        chapters = into_chapters(
            [
                a_movement(
                    "Lot API", project_id=9, day=2, parent_id=7, parent_label="Ganesh"
                ),
                a_movement(
                    "Lot API", project_id=9, day=8, parent_id=7, parent_label="Ganesh"
                ),
            ]
        )

        assert [m.at.day for m in chapters[0].packages[0].movements] == [2, 8]

    def test_a_project_opens_on_the_earliest_of_its_own_and_its_packages(self) -> None:
        chapters = into_chapters(
            [
                a_movement("NOMAD", project_id=8, day=10),
                a_movement(
                    "Lot API", project_id=9, day=2, parent_id=7, parent_label="Ganesh"
                ),
            ]
        )

        assert [chapter.label for chapter in chapters] == ["Ganesh", "NOMAD"]

    def test_packages_of_one_project_read_in_the_order_they_appear(self) -> None:
        chapters = into_chapters(
            [
                a_movement(
                    "Lot B", project_id=9, day=20, parent_id=7, parent_label="Ganesh"
                ),
                a_movement(
                    "Lot A", project_id=10, day=4, parent_id=7, parent_label="Ganesh"
                ),
            ]
        )

        assert [package.label for package in chapters[0].packages] == ["Lot A", "Lot B"]

    def test_what_is_about_no_mission_gathers_on_its_own(self) -> None:
        chapters = into_chapters(
            [
                a_movement(
                    "Sam Okafor",
                    project_id=None,
                    day=1,
                    kind=MovementKind.TEAMMATE_JOINED,
                )
            ]
        )

        assert len(chapters) == 1
        assert chapters[0].project_id is None
        assert chapters[0].label is None

    def test_the_team_is_told_last_whenever_it_happened(self) -> None:
        """Who joined is context around the month's work, not work itself."""
        chapters = into_chapters(
            [
                a_movement(
                    "Sam Okafor",
                    project_id=None,
                    day=1,
                    kind=MovementKind.TEAMMATE_JOINED,
                ),
                a_movement("Ganesh", project_id=7, day=25),
            ]
        )

        assert [chapter.label for chapter in chapters] == ["Ganesh", None]
