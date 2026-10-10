"""The exchanges kept, to study the assistant somewhere else than on screen."""

from src.modules.assistant.application.dtos.assistant_dtos import ExchangeExport
from src.modules.assistant.domain.repositories.exchange_archive import (
    ExchangeArchive,
    ExchangeFilter,
)
from src.modules.users.domain.repositories.user_repository import UserRepository


class ExportExchangesUseCase:
    """Every exchange the filter keeps, oldest first, each with whoever asked it.

    Named rather than numbered: a file read outside the application has no
    list of users to look an identifier up in.
    """

    def __init__(self, archive: ExchangeArchive, users: UserRepository) -> None:
        self._archive = archive
        self._users = users

    async def execute(self, kept: ExchangeFilter) -> ExchangeExport:
        exchanges = await self._archive.list_exchanges(kept)
        everybody = await self._users.list_all(include_inactive=True)
        return ExchangeExport(
            exchanges=exchanges,
            askers={user.id: user for user in everybody if user.id is not None},
        )
