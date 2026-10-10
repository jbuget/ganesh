"""The exchanges kept, written out as a file to study somewhere else.

JSON carries everything, the tools' readings word for word. CSV carries a line
per exchange and names the tools without what they read: a reading runs to
pages, and a spreadsheet cell holding one is a spreadsheet nobody reads.

The CSV is written for the spreadsheet the team opens it in: a semicolon
between fields and a byte-order mark, without which accents come out garbled.
"""

import csv
import io
from enum import StrEnum

from pydantic import TypeAdapter

from src.modules.assistant.presentation.api.schemas.study_schemas import (
    ExportedExchangeResponse,
)

CSV_COLUMNS = (
    "asked_at",
    "conversation_id",
    "rank",
    "asker_name",
    "asker_email",
    "project_id",
    "question",
    "answer",
    "tools",
    "model",
    "input_tokens",
    "output_tokens",
    "elapsed_ms",
    "verdict",
    "annotation_cause",
    "annotation_note",
)

_EXPORTED = TypeAdapter(list[ExportedExchangeResponse])


class ExportFormat(StrEnum):
    CSV = "csv"
    JSON = "json"


MEDIA_TYPES = {
    ExportFormat.CSV: "text/csv; charset=utf-8",
    ExportFormat.JSON: "application/json",
}


def as_json(exchanges: list[ExportedExchangeResponse]) -> bytes:
    return _EXPORTED.dump_json(exchanges, indent=2)


def as_csv(exchanges: list[ExportedExchangeResponse]) -> bytes:
    written = io.StringIO()
    writer = csv.writer(written, delimiter=";")
    writer.writerow(CSV_COLUMNS)
    for exchange in exchanges:
        annotation = exchange.annotation
        writer.writerow(
            (
                exchange.asked_at.isoformat(),
                exchange.conversation_id,
                exchange.rank,
                exchange.asker_name or "",
                exchange.asker_email or "",
                exchange.project_id or "",
                exchange.question,
                exchange.answer,
                ", ".join(held.tool for held in exchange.consultations),
                exchange.model,
                exchange.input_tokens,
                exchange.output_tokens,
                exchange.elapsed_ms,
                exchange.verdict or "",
                annotation.cause if annotation else "",
                (annotation.note or "") if annotation else "",
            )
        )
    return written.getvalue().encode("utf-8-sig")


def written_as(
    exchanges: list[ExportedExchangeResponse], format: ExportFormat
) -> bytes:
    return as_csv(exchanges) if format is ExportFormat.CSV else as_json(exchanges)
