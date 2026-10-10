"""Opening, listing, closing and reading the links of a digest."""

from datetime import date

import pytest

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.gazette.application.dtos.gazette_dtos import (
    ListShareLinksQuery,
    ReadSharedDigestQuery,
    RevokeShareLinkCommand,
    ShareDigestCommand,
)
from src.modules.gazette.application.use_cases.list_share_links import (
    ListShareLinksUseCase,
)
from src.modules.gazette.application.use_cases.read_shared_digest import (
    ReadSharedDigestUseCase,
)
from src.modules.gazette.application.use_cases.revoke_share_link import (
    RevokeShareLinkUseCase,
)
from src.modules.gazette.application.use_cases.share_digest import ShareDigestUseCase
from src.modules.gazette.domain.entities.brief import Brief, Tally
from src.modules.gazette.domain.entities.digest import Digest
from src.modules.gazette.domain.entities.highlight import Highlight, HighlightKind
from src.modules.gazette.domain.entities.prose import Prose
from src.modules.users.domain.entities.user import Role, User
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from tests.helpers.in_memory_repositories import (
    InMemoryAuditLogRepository,
    InMemoryDigestRepository,
    InMemoryShareLinkRepository,
    InMemoryUserRepository,
)
from tests.helpers.instants import paris

MONTH = date(2026, 9, 1)
AT = paris(2026, 10, 11, 9)


def a_teammate(user_id: int, name: str) -> User:
    return User(
        id=user_id,
        entra_oid=f"oid-{user_id}",
        email=f"user{user_id}@waat.fr",
        display_name=name,
        role=Role.TEAMMATE,
    )


class Desk:
    """Everything the four use cases share: a team, a digest, its links."""

    def __init__(self) -> None:
        self.users = InMemoryUserRepository(
            [a_teammate(1, "Léa Chen"), a_teammate(2, "Sam Okafor")]
        )
        self.digests = InMemoryDigestRepository()
        self.links = InMemoryShareLinkRepository()
        self.audit_logs = InMemoryAuditLogRepository()
        self.share = ShareDigestUseCase(
            self.users, self.digests, self.links, self.audit_logs
        )
        self.revoke = RevokeShareLinkUseCase(self.digests, self.links, self.audit_logs)
        self.list = ListShareLinksUseCase(self.users, self.digests, self.links)
        self.read = ReadSharedDigestUseCase(self.digests, self.links)

    async def with_a_digest(self, version: int = 1) -> None:
        await self.digests.add(
            Digest(
                month=MONTH,
                version=version,
                brief=Brief(
                    month=MONTH,
                    tally=Tally(projects_created=2),
                    highlights=[
                        Highlight(
                            kind=HighlightKind.GO_LIVE_OVERDUE,
                            project_id=8,
                            label="NOMAD",
                        )
                    ],
                ),
                generated_at=paris(2026, 10, 9, 11),
                requested_by="Léa Chen",
                prose=Prose(text="Un mois de cadrage.", model="m"),
            )
        )


class TestShare:
    @pytest.mark.asyncio
    async def test_a_link_opens_on_the_version_asked_for(self) -> None:
        desk = Desk()
        await desk.with_a_digest(1)
        await desk.with_a_digest(2)

        view = await desk.share.execute(
            ShareDigestCommand(month=MONTH, version=1, actor_id=1), at=AT
        )

        digest = await desk.digests.get_version(MONTH, 1)
        assert digest is not None
        assert view.link.digest_id == digest.id
        assert view.created_by == "Léa Chen"
        assert view.link.created_at == AT

    @pytest.mark.asyncio
    async def test_any_day_of_the_month_names_it(self) -> None:
        desk = Desk()
        await desk.with_a_digest()

        view = await desk.share.execute(
            ShareDigestCommand(month=date(2026, 9, 17), version=1, actor_id=1), at=AT
        )

        assert view.link.id is not None

    @pytest.mark.asyncio
    async def test_a_version_nobody_generated_has_nothing_to_hand_out(self) -> None:
        desk = Desk()

        with pytest.raises(EntityNotFoundError):
            await desk.share.execute(
                ShareDigestCommand(month=MONTH, version=1, actor_id=1), at=AT
            )

    @pytest.mark.asyncio
    async def test_an_actor_it_cannot_find_is_refused(self) -> None:
        desk = Desk()
        await desk.with_a_digest()

        with pytest.raises(EntityNotFoundError):
            await desk.share.execute(
                ShareDigestCommand(month=MONTH, version=1, actor_id=99), at=AT
            )

    @pytest.mark.asyncio
    async def test_it_traces_the_gesture_and_the_version_shared(self) -> None:
        desk = Desk()
        await desk.with_a_digest()

        await desk.share.execute(
            ShareDigestCommand(month=MONTH, version=1, actor_id=1), at=AT
        )

        traced = [
            log
            for log in desk.audit_logs.logs
            if log.action is AuditAction.GAZETTE_SHARE
        ]
        assert [(log.actor_id, log.day, log.new_value) for log in traced] == [
            (1, MONTH, "1")
        ]


class TestList:
    @pytest.mark.asyncio
    async def test_it_lists_the_open_links_with_who_opened_them(self) -> None:
        desk = Desk()
        await desk.with_a_digest()
        await desk.share.execute(
            ShareDigestCommand(month=MONTH, version=1, actor_id=2), at=AT
        )

        views = await desk.list.execute(ListShareLinksQuery(month=MONTH, version=1))

        assert [view.created_by for view in views] == ["Sam Okafor"]

    @pytest.mark.asyncio
    async def test_a_closed_link_is_no_longer_listed(self) -> None:
        desk = Desk()
        await desk.with_a_digest()
        view = await desk.share.execute(
            ShareDigestCommand(month=MONTH, version=1, actor_id=1), at=AT
        )
        await desk.revoke.execute(
            RevokeShareLinkCommand(link_id=view.link.id or 0, actor_id=2), at=AT
        )

        assert (
            await desk.list.execute(ListShareLinksQuery(month=MONTH, version=1)) == []
        )

    @pytest.mark.asyncio
    async def test_a_version_nobody_generated_lists_nothing(self) -> None:
        desk = Desk()

        assert (
            await desk.list.execute(ListShareLinksQuery(month=MONTH, version=3)) == []
        )


class TestRevoke:
    @pytest.mark.asyncio
    async def test_anyone_on_the_team_may_close_a_link_whoever_opened_it(self) -> None:
        desk = Desk()
        await desk.with_a_digest()
        view = await desk.share.execute(
            ShareDigestCommand(month=MONTH, version=1, actor_id=1), at=AT
        )

        await desk.revoke.execute(
            RevokeShareLinkCommand(link_id=view.link.id or 0, actor_id=2), at=AT
        )

        link = await desk.links.get(view.link.id or 0)
        assert link is not None
        assert not link.is_open

    @pytest.mark.asyncio
    async def test_it_traces_the_closing(self) -> None:
        desk = Desk()
        await desk.with_a_digest()
        view = await desk.share.execute(
            ShareDigestCommand(month=MONTH, version=1, actor_id=1), at=AT
        )

        await desk.revoke.execute(
            RevokeShareLinkCommand(link_id=view.link.id or 0, actor_id=2), at=AT
        )

        traced = [
            log
            for log in desk.audit_logs.logs
            if log.action is AuditAction.GAZETTE_UNSHARE
        ]
        assert [(log.actor_id, log.day, log.new_value) for log in traced] == [
            (2, MONTH, "1")
        ]

    @pytest.mark.asyncio
    async def test_closing_a_closed_link_traces_nothing_more(self) -> None:
        desk = Desk()
        await desk.with_a_digest()
        view = await desk.share.execute(
            ShareDigestCommand(month=MONTH, version=1, actor_id=1), at=AT
        )
        command = RevokeShareLinkCommand(link_id=view.link.id or 0, actor_id=2)
        await desk.revoke.execute(command, at=AT)

        await desk.revoke.execute(command, at=AT)

        assert (
            len(
                [
                    log
                    for log in desk.audit_logs.logs
                    if log.action is AuditAction.GAZETTE_UNSHARE
                ]
            )
            == 1
        )

    @pytest.mark.asyncio
    async def test_a_link_that_does_not_exist_is_not_found(self) -> None:
        desk = Desk()

        with pytest.raises(EntityNotFoundError):
            await desk.revoke.execute(RevokeShareLinkCommand(link_id=99, actor_id=1))


class TestRead:
    async def opened(self, desk: Desk) -> str:
        await desk.with_a_digest()
        view = await desk.share.execute(
            ShareDigestCommand(month=MONTH, version=1, actor_id=1), at=AT
        )
        return view.link.token

    @pytest.mark.asyncio
    async def test_a_token_opens_the_narrative_of_its_version(self) -> None:
        desk = Desk()
        token = await self.opened(desk)

        public = await desk.read.execute(ReadSharedDigestQuery(token=token))

        assert public.prose is not None
        assert public.prose.text == "Un mois de cadrage."
        assert (public.month, public.version) == (MONTH, 1)

    @pytest.mark.asyncio
    async def test_what_it_opens_carries_no_point_d_attention(self) -> None:
        desk = Desk()
        token = await self.opened(desk)

        public = await desk.read.execute(ReadSharedDigestQuery(token=token))

        assert public.went_live == ()

    @pytest.mark.asyncio
    async def test_an_unknown_token_opens_nothing(self) -> None:
        desk = Desk()
        await self.opened(desk)

        with pytest.raises(EntityNotFoundError):
            await desk.read.execute(ReadSharedDigestQuery(token="x" * 43))

    @pytest.mark.asyncio
    async def test_a_closed_token_opens_nothing(self) -> None:
        desk = Desk()
        token = await self.opened(desk)
        link = await desk.links.get_by_token(token)
        assert link is not None
        await desk.revoke.execute(
            RevokeShareLinkCommand(link_id=link.id or 0, actor_id=2), at=AT
        )

        with pytest.raises(EntityNotFoundError):
            await desk.read.execute(ReadSharedDigestQuery(token=token))

    @pytest.mark.asyncio
    async def test_unknown_and_closed_answer_in_the_same_words(self) -> None:
        """Telling them apart would teach a guesser which guesses were real."""
        desk = Desk()
        token = await self.opened(desk)
        link = await desk.links.get_by_token(token)
        assert link is not None
        await desk.revoke.execute(
            RevokeShareLinkCommand(link_id=link.id or 0, actor_id=2), at=AT
        )

        with pytest.raises(EntityNotFoundError) as closed:
            await desk.read.execute(ReadSharedDigestQuery(token=token))
        with pytest.raises(EntityNotFoundError) as unknown:
            await desk.read.execute(ReadSharedDigestQuery(token="x" * 43))

        assert str(closed.value) == str(unknown.value)
