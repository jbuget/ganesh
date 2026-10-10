"""« Que disent les dernières mises à jour de ce projet ? »

The brief says where a project stands; the thread says what happened on it,
in the words of the people on it. Somebody who is not on the project — the
reader the assistant exists for — has no other way to hear them.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI

from src.mcp.door import Machine, standing
from src.mcp.server import ToolServer
from src.mcp.tools.news import MOST, project_news
from src.mcp.wiring import Wiring
from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    MachineCaller,
)
from src.modules.api_keys.domain.entities.api_key import ApiKey, ApiKeyScope
from src.modules.projects.application.use_cases.project_updates import (
    SignedComment,
    SignedUpdate,
)
from src.modules.projects.domain.entities.project import Project, ProjectKind
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.projects.domain.entities.update_comment import UpdateComment
from src.modules.projects.presentation.dependencies import (
    get_list_updates_use_case,
    get_project_detail_use_case,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError

LEA = User(
    id=1,
    entra_oid="oid-1",
    email="l@waat.fr",
    display_name="Léa Chen",
    role=Role.TEAMMATE,
)
VALENTIN = User(
    id=2,
    entra_oid="oid-2",
    email="v@waat.fr",
    display_name="Valentin Le Strat",
    role=Role.TEAMMATE,
)

EDIT = Project(id=7, label="EDIT", kind=ProjectKind.PROJECT)
EDIT_V2 = Project(id=8, label="EDIT V2", kind=ProjectKind.WORK_PACKAGE, parent_id=7)


@dataclass
class Sheet:
    """What `project_news` reads of a mission: its name and its packages."""

    project: Project
    sub_projects: list[Project] = field(default_factory=list)


class ByProject:
    """A use case answering per project, as the real ones do."""

    def __init__(self, answers: dict[int, object]) -> None:
        self._answers = answers

    async def execute(self, project_id: int, *args: object) -> object:
        answer = self._answers.get(project_id, [])
        if isinstance(answer, Exception):
            raise answer
        return answer


def at(month: int, day: int) -> datetime:
    return datetime(2026, month, day, 9, 30, tzinfo=UTC)


def posted(
    project: Project,
    body: str,
    when: datetime,
    by: User = LEA,
    replies: int = 0,
    withdrawn: bool = False,
) -> SignedUpdate:
    assert project.id is not None and by.id is not None
    update = ProjectUpdate(
        id=None,
        project_id=project.id,
        author_id=by.id,
        body="" if withdrawn else body,
        published_at=when,
        deleted_at=when if withdrawn else None,
    )
    return SignedUpdate(
        update=update,
        author=by,
        comments=[
            SignedComment(
                comment=UpdateComment(
                    id=None, update_id=0, author_id=by.id, body="ok", published_at=when
                ),
                author=by,
            )
            for _ in range(replies)
        ],
    )


class Wired:
    def __init__(
        self,
        sheets: dict[int, object],
        threads: dict[int, object],
    ) -> None:
        app = FastAPI()
        ToolServer().attach(app)
        app.dependency_overrides[get_project_detail_use_case] = lambda: ByProject(
            sheets
        )
        app.dependency_overrides[get_list_updates_use_case] = lambda: ByProject(threads)
        key = ApiKey(
            id=1,
            name="clé",
            public_id="abcdefghijkl",
            secret_hash="x",
            owner_id=1,
            created_by=1,
            scopes=[ApiKeyScope.PROJECTS_READ],
        )
        self._standing = standing(
            Machine(
                caller=MachineCaller(key=key, owner=LEA),
                wiring=Wiring(session=None, overrides=app.dependency_overrides),  # type: ignore[arg-type]
            )
        )

    def __enter__(self) -> "Wired":
        self._standing.__enter__()
        return self

    def __exit__(self, *_: object) -> None:
        self._standing.__exit__(None, None, None)


def edit_with(*thread: SignedUpdate, package_thread: tuple[SignedUpdate, ...] = ()):
    return Wired(
        sheets={7: Sheet(EDIT, [EDIT_V2]), 8: Sheet(EDIT_V2)},
        threads={7: list(thread), 8: list(package_thread)},
    )


@pytest.mark.asyncio
class TestProjectNews:
    async def test_an_update_is_read_with_its_day_and_its_author(self) -> None:
        with edit_with(posted(EDIT, "La recette commence lundi.", at(10, 9))):
            said = await project_news(7)

        assert "Le 09/10/2026, Léa Chen : La recette commence lundi." in said

    async def test_the_most_recent_comes_first(self) -> None:
        with edit_with(
            posted(EDIT, "Cadrage terminé.", at(9, 1)),
            posted(EDIT, "Recette lancée.", at(10, 1)),
        ):
            said = await project_news(7)

        assert said.index("Recette lancée.") < said.index("Cadrage terminé.")

    async def test_an_update_on_a_package_says_which_one(self) -> None:
        """The project's month happens on its packages too."""
        with edit_with(
            package_thread=(
                posted(EDIT_V2, "Validation en cours.", at(10, 2), by=VALENTIN),
            )
        ):
            said = await project_news(7)

        assert (
            "Le 02/10/2026, Valentin Le Strat, sur EDIT V2 : Validation en cours."
            in said
        )

    async def test_a_withdrawn_update_is_left_out(self) -> None:
        with edit_with(
            posted(EDIT, "Retiré.", at(10, 3), withdrawn=True),
            posted(EDIT, "Toujours là.", at(10, 2)),
        ):
            said = await project_news(7)

        assert "Toujours là." in said
        assert said.count("Le ") == 1

    async def test_the_answers_an_update_drew_are_counted(self) -> None:
        with edit_with(posted(EDIT, "Mise en service demain.", at(10, 4), replies=2)):
            said = await project_news(7)

        assert "Mise en service demain. (2 réponses)" in said

    async def test_a_mention_reads_as_the_name_it_carries(self) -> None:
        with edit_with(
            posted(
                EDIT, "Cc. @[Sylvain-Pierre Do](mention://user/4) pour info.", at(10, 4)
            )
        ):
            said = await project_news(7)

        assert "Cc. @Sylvain-Pierre Do pour info." in said

    async def test_an_image_is_left_out_of_the_words(self) -> None:
        with edit_with(
            posted(
                EDIT,
                "Voici l'écran ![capture](/api/v1/projects/7/attachments/3/content) final.",
                at(10, 4),
            )
        ):
            said = await project_news(7)

        assert "Voici l'écran final." in said

    async def test_an_image_at_the_end_of_a_sentence_leaves_no_blank(self) -> None:
        with edit_with(
            posted(EDIT, "Voici l'écran ![capture](/a/b). Gain : net.", at(10, 4))
        ):
            said = await project_news(7)

        assert "Voici l'écran. Gain : net." in said

    async def test_the_breaks_and_entities_of_the_editor_are_undone(self) -> None:
        with edit_with(
            posted(EDIT, "Gain : 30 mn\\\n\\\néviter &gt; tensions", at(10, 4))
        ):
            said = await project_news(7)

        assert "Gain : 30 mn éviter > tensions" in said

    async def test_a_long_update_is_cut_and_says_so(self) -> None:
        with edit_with(posted(EDIT, "mot " * 400, at(10, 4))):
            said = await project_news(7)

        assert said.rstrip().endswith("…")
        assert len(said) < 1000

    async def test_past_the_most_recent_the_rest_is_counted(self) -> None:
        with edit_with(
            *(posted(EDIT, f"Point {n}.", at(9, n + 1)) for n in range(MOST + 3))
        ):
            said = await project_news(7)

        assert said.count("Léa Chen :") == MOST
        assert "3 mises à jour plus anciennes" in said

    async def test_a_date_reads_only_what_came_after_it(self) -> None:
        with edit_with(
            posted(EDIT, "Ancien.", at(8, 1)),
            posted(EDIT, "Récent.", at(10, 1)),
        ):
            said = await project_news(7, since="2026-09-01")

        assert "Récent." in said
        assert "Ancien." not in said

    async def test_nothing_since_the_date_is_said_with_the_last_one(self) -> None:
        with edit_with(posted(EDIT, "Ancien.", at(8, 1))):
            said = await project_news(7, since="2026-09-01")

        assert said == (
            "Aucune mise à jour sur EDIT ni sur ses lots depuis le 01/09/2026. "
            "La dernière date du 01/08/2026."
        )

    async def test_a_project_nobody_wrote_about_says_so(self) -> None:
        with edit_with():
            said = await project_news(7)

        assert said == "Aucune mise à jour n'a été postée sur EDIT ni sur ses lots."

    async def test_a_date_that_does_not_parse_is_said(self) -> None:
        with edit_with():
            said = await project_news(7, since="hier")

        assert "AAAA-MM-JJ" in said

    async def test_a_project_nobody_can_find_is_said(self) -> None:
        with Wired(sheets={7: EntityNotFoundError("…")}, threads={}):
            said = await project_news(7)

        assert said.startswith("Aucun projet ne porte l'identifiant 7.")
