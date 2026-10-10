"""An administrator's reading of an answer."""

from src.modules.assistant.application.dtos.assistant_dtos import AnnotateCommand
from src.modules.assistant.domain.entities.exchange import Exchange
from src.modules.assistant.domain.repositories.exchange_archive import ExchangeArchive
from src.shared.exceptions.domain_exceptions import EntityNotFoundError
from src.shared.utils import clock


class AnnotateExchangeUseCase:
    """Says why an answer came out as it did, whoever it was given to.

    Not traced in the log, as the verdict is not: an exchange is a reading,
    and saying what one thinks of a reading is no gesture on a project. The
    row carries who annotated and when, which is all a study needs.
    """

    def __init__(self, archive: ExchangeArchive) -> None:
        self._archive = archive

    async def execute(self, command: AnnotateCommand) -> Exchange:
        exchange = await self._archive.read_exchange(command.exchange_id)
        if exchange is None:
            raise EntityNotFoundError("This answer does not exist.")

        exchange.annotate(
            by=command.annotator_id,
            cause=command.cause,
            note=command.note,
            at=clock.now(),
        )
        await self._archive.save_annotation(exchange)
        return exchange
