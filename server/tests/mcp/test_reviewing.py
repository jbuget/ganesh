"""« On sort de la revue de kanban, consigne-la. »

The second tool that writes, and the first that writes about a project rather
than about a month. Four properties this file exists for:

- **the note and the phase are one gesture.** A review says what happened and
  where the project now stands; two calls could land half of that and leave
  the register saying a project moved for no reason anybody wrote down;
- **nothing is written unless everything can be.** An unreadable phase is
  refused before the note is posted, and the session is committed once;
- **the phase is a second scope.** A key that may write the thread does not
  thereby move cards, and the refusal names what to ask for;
- **every refusal comes back as a sentence**, phases included: « construction »
  is what the screens say, and a tool that only answered to « development »
  would make a reader learn the database;
- **it convokes nobody.** A note carrying a mention notifies the person it
  names, and a model recopying a name out of a thread it has just read would
  summon them for nothing.
"""

import pytest
from fastapi import FastAPI

from mcp.server.mcpserver.exceptions import ToolError
from src.mcp.door import Machine, standing
from src.mcp.server import ToolServer
from src.mcp.tools.reviewing import record_review
from src.mcp.wiring import Wiring
from src.modules.api_keys.application.use_cases.authenticate_api_key import (
    MachineCaller,
)
from src.modules.api_keys.domain.entities.api_key import ApiKey, ApiKeyScope
from src.modules.projects.application.dtos.project_dto import ChangeProjectStatusCommand
from src.modules.projects.application.dtos.update_dto import PostUpdateCommand
from src.modules.projects.domain.entities.project import (
    Project,
    ProjectKind,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_update import ProjectUpdate
from src.modules.projects.presentation.dependencies import (
    get_change_status_use_case,
    get_post_update_use_case,
)
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError, ValidationError
from src.shared.utils import clock

OWNER = User(
    id=7, entra_oid="oid-7", email="a@waat.fr", display_name="A. Ba", role=Role.TEAMMATE
)

#: Both writes, which is what a review needs.
FULLY = [ApiKeyScope.UPDATES_WRITE, ApiKeyScope.PROJECTS_WRITE]


class Thread:
    """Stands in for `PostProjectUpdateUseCase`, and remembers what it was told."""

    def __init__(self, answer: Exception | None = None) -> None:
        self.asked: PostUpdateCommand | None = None
        self._answer = answer

    async def execute(self, command: PostUpdateCommand) -> ProjectUpdate:
        self.asked = command
        if self._answer is not None:
            raise self._answer
        return ProjectUpdate(
            id=1,
            project_id=command.project_id,
            author_id=command.actor_id,
            body=command.body,
            published_at=clock.now(),
        )


class Board:
    """Stands in for `ChangeProjectStatusUseCase`."""

    def __init__(self, answer: Exception | None = None) -> None:
        self.asked: ChangeProjectStatusCommand | None = None
        self._answer = answer

    async def execute(self, command: ChangeProjectStatusCommand) -> Project:
        self.asked = command
        if self._answer is not None:
            raise self._answer
        return Project(
            id=command.project_id,
            label="Sitetracker - GMAO",
            kind=ProjectKind.PROJECT,
            status=command.status,
        )


class Wired:
    def __init__(
        self,
        thread: Thread | None = None,
        board: Board | None = None,
        scopes: list[ApiKeyScope] | None = None,
    ) -> None:
        self.thread = thread or Thread()
        self.board = board or Board()
        self.app = FastAPI()
        ToolServer().attach(self.app)
        self.app.dependency_overrides[get_post_update_use_case] = lambda: self.thread
        self.app.dependency_overrides[get_change_status_use_case] = lambda: self.board
        self.committed = 0
        key = ApiKey(
            id=1,
            name="Claude Code de A. Ba",
            public_id="abcdefghijkl",
            secret_hash="x",
            owner_id=7,
            created_by=1,
            scopes=list(scopes or FULLY),
        )
        self._standing = standing(
            Machine(
                caller=MachineCaller(key=key, owner=OWNER),
                wiring=Wiring(
                    session=_Session(self),  # type: ignore[arg-type]
                    overrides=self.app.dependency_overrides,
                ),
            )
        )

    def __enter__(self) -> "Wired":
        self._standing.__enter__()
        return self

    def __exit__(self, *_: object) -> None:
        self._standing.__exit__(None, None, None)
        self.app.dependency_overrides.clear()


class _Session:
    """Counts commits: a write nobody commits is a write nobody keeps."""

    def __init__(self, wired: Wired) -> None:
        self._wired = wired

    async def commit(self) -> None:
        self._wired.committed += 1


class TestTheNoteAndThePhaseAreOneGesture:
    @pytest.mark.asyncio
    async def test_a_note_alone_is_posted_and_nothing_moves(self) -> None:
        with Wired() as wired:
            said = await record_review(project_id=13, note="La démo est mercredi.")

        assert wired.thread.asked is not None
        assert wired.thread.asked.body == "La démo est mercredi."
        assert wired.thread.asked.project_id == 13
        assert wired.board.asked is None
        assert "#13" in said
        assert wired.committed == 1

    @pytest.mark.asyncio
    async def test_a_phase_moves_in_the_same_breath(self) -> None:
        with Wired() as wired:
            said = await record_review(
                project_id=13, note="Nino démarre demain.", phase="construction"
            )

        assert wired.thread.asked is not None
        assert wired.board.asked is not None
        assert wired.board.asked.status is ProjectStatus.DEVELOPMENT
        assert wired.board.asked.project_id == 13
        assert "construction" in said
        # One gesture, one commit: the note and the phase land together or not
        # at all.
        assert wired.committed == 1

    @pytest.mark.asyncio
    async def test_it_writes_as_the_owner_of_the_key(self) -> None:
        """There is no author to pass: the key answers for its owner."""
        with Wired() as wired:
            await record_review(project_id=13, note="Rien à signaler.", phase="cadrage")

        assert wired.thread.asked is not None
        assert wired.thread.asked.actor_id == OWNER.id
        assert wired.board.asked is not None
        assert wired.board.asked.actor_id == OWNER.id

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("given", "read_back"),
        [("validation", "validation"), ("en service", "en service")],
    )
    async def test_the_phase_is_named_without_a_preposition_of_our_own(
        self, given: str, read_back: str
    ) -> None:
        """Both cases on purpose, and « en service » is the reason.

        One of the six phases carries its own preposition, so the sentence
        carries none: « désormais en {phase} » would read « désormais en en
        service ». Neither the type checker nor a test asserting on a phase
        name would catch that — only this one does.
        """
        with Wired():
            said = await record_review(
                project_id=56, note="Recette métier.", phase=given
            )

        assert f"Phase désormais : {read_back}." in said


class TestAPhaseIsSaidInTheLanguageOfTheScreens:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("given", "expected"),
        [
            ("exploration", ProjectStatus.EXPLORATION),
            ("cadrage", ProjectStatus.SCOPING),
            ("construction", ProjectStatus.DEVELOPMENT),
            ("validation", ProjectStatus.VALIDATION),
            ("déploiement", ProjectStatus.DEPLOYMENT),
            ("en service", ProjectStatus.OPERATIONS),
        ],
    )
    async def test_every_phase_the_screens_show_is_understood(
        self, given: str, expected: ProjectStatus
    ) -> None:
        with Wired() as wired:
            await record_review(project_id=13, note="Note.", phase=given)

        assert wired.board.asked is not None
        assert wired.board.asked.status is expected

    @pytest.mark.asyncio
    async def test_the_domain_s_own_word_is_understood_too(self) -> None:
        """A client reading the API has « development » in hand, not « construction »."""
        with Wired() as wired:
            await record_review(project_id=13, note="Note.", phase="development")

        assert wired.board.asked is not None
        assert wired.board.asked.status is ProjectStatus.DEVELOPMENT

    @pytest.mark.asyncio
    async def test_the_case_and_the_spaces_are_forgiven(self) -> None:
        with Wired() as wired:
            await record_review(project_id=13, note="Note.", phase="  En Service ")

        assert wired.board.asked is not None
        assert wired.board.asked.status is ProjectStatus.OPERATIONS


class TestEveryRefusalIsASentence:
    @pytest.mark.asyncio
    async def test_a_phase_nobody_recognises_lists_the_ones_there_are(self) -> None:
        wired = Wired()
        with wired, pytest.raises(ToolError) as raised:
            await record_review(project_id=13, note="Note.", phase="terminé")

        assert "terminé" in str(raised.value)
        assert "construction" in str(raised.value)
        assert "en service" in str(raised.value)
        # Refused before anything is written: a review is one gesture.
        assert wired.thread.asked is None
        assert wired.board.asked is None
        assert wired.committed == 0

    @pytest.mark.asyncio
    async def test_a_note_with_nothing_in_it_is_refused_before_the_domain(self) -> None:
        wired = Wired()
        with wired, pytest.raises(ToolError) as raised:
            await record_review(project_id=13, note="   ")

        assert "vide" in str(raised.value)
        assert wired.thread.asked is None
        assert wired.committed == 0

    @pytest.mark.asyncio
    async def test_an_unknown_project_says_where_to_find_the_identifier(self) -> None:
        wired = Wired(
            thread=Thread(EntityNotFoundError("The mission cannot be found."))
        )
        with wired, pytest.raises(ToolError) as raised:
            await record_review(project_id=999, note="Note.")

        assert "999" in str(raised.value)
        assert "find_project" in str(raised.value)
        assert wired.committed == 0

    @pytest.mark.asyncio
    async def test_off_project_work_carries_no_phase_and_is_told_so(self) -> None:
        """« Absences » is not a project one moves through phases."""
        wired = Wired(
            board=Board(ValidationError("An off-project activity carries no phase."))
        )
        with wired, pytest.raises(ToolError) as raised:
            await record_review(project_id=1, note="Note.", phase="construction")

        assert "hors-projet" in str(raised.value)
        assert wired.committed == 0

    @pytest.mark.asyncio
    async def test_a_refusal_is_raised_rather_than_answered(self) -> None:
        """A write that did not happen must not read like one that did."""
        with Wired(), pytest.raises(ToolError):
            await record_review(project_id=13, note="")


class TestItConvokesNobody:
    """A mention notifies the person it names. A review is not a summons."""

    @pytest.mark.asyncio
    async def test_a_mention_is_refused_rather_than_stripped(self) -> None:
        """Removing it quietly would consign something other than what was said."""
        with Wired() as wired, pytest.raises(ToolError) as raised:
            await record_review(
                13, "À relire, @[M. Ce](mention://user/2) prend la suite."
            )

        assert "mention" in str(raised.value)
        assert wired.thread.asked is None
        assert wired.committed == 0

    @pytest.mark.asyncio
    async def test_the_refusal_says_the_thread_is_told_anyway(self) -> None:
        """Somebody removing the mention has to know nobody is being cut out."""
        with Wired(), pytest.raises(ToolError) as raised:
            await record_review(13, "@[M. Ce](mention://user/2) peux-tu regarder ?")

        assert "averti" in str(raised.value)

    @pytest.mark.asyncio
    async def test_the_phase_does_not_move_either(self) -> None:
        """Half a review is what the whole tool exists to prevent."""
        with Wired() as wired, pytest.raises(ToolError):
            await record_review(
                13, "@[M. Ce](mention://user/2) reprend.", phase="construction"
            )

        assert wired.board.asked is None

    @pytest.mark.asyncio
    async def test_an_at_sign_that_names_nobody_goes_through(self) -> None:
        """A plain « @Marie » notifies no one: only the link form does."""
        with Wired() as wired:
            await record_review(13, "Vu avec @Marie ce matin, rien ne bouge.")

        assert wired.thread.asked is not None


class TestThePhaseIsASecondScope:
    @pytest.mark.asyncio
    async def test_a_key_that_may_only_write_the_thread_still_records_a_review(
        self,
    ) -> None:
        with Wired(scopes=[ApiKeyScope.UPDATES_WRITE]) as wired:
            said = await record_review(project_id=13, note="La démo est mercredi.")

        assert wired.thread.asked is not None
        assert "#13" in said

    @pytest.mark.asyncio
    async def test_moving_a_phase_without_the_scope_names_what_to_ask_for(self) -> None:
        wired = Wired(scopes=[ApiKeyScope.UPDATES_WRITE])
        with wired, pytest.raises(ToolError, match="projects:write"):
            await record_review(project_id=13, note="Note.", phase="construction")

        # Short of the scope, the note is not posted either: half a review is
        # worse than none, the register would say a project stood still.
        assert wired.thread.asked is None
        assert wired.committed == 0

    @pytest.mark.asyncio
    async def test_a_key_that_reads_everything_writes_nothing(self) -> None:
        wired = Wired(scopes=[ApiKeyScope.ALL_READ])
        with wired, pytest.raises(ToolError, match="updates:write"):
            await record_review(project_id=13, note="Note.")

        assert wired.thread.asked is None
