"""How a numéro's facts are kept, and read back years later.

A published numéro is frozen, which makes this shape an archive format rather
than an implementation detail: what is written here has to open long after the
code that wrote it has moved. Hence a version stamped on the way out, and a
tolerant read on the way back — a field that did not exist yet reads as
nothing, never as an error. Renaming a key means migrating every row.
"""

from datetime import date, datetime
from typing import Any

from src.modules.gazette.domain.entities.brief import Brief, Tally
from src.modules.gazette.domain.entities.highlight import Highlight, HighlightKind
from src.modules.gazette.domain.entities.movement import Movement, MovementKind
from src.modules.projects.domain.entities.project import ProjectStatus

#: The shape below. Bumped when a key changes meaning, never when one is added.
VERSION = 1


def to_json(brief: Brief) -> dict[str, Any]:
    """The facts of a numéro, as they are stored."""
    return {
        "version": VERSION,
        "tally": {
            "projects_created": brief.tally.projects_created,
            "projects_archived": brief.tally.projects_archived,
            "phase_changes": brief.tally.phase_changes,
            "news_posted": brief.tally.news_posted,
            "months_validated": brief.tally.months_validated,
        },
        "movements": [
            {
                "kind": movement.kind.value,
                "at": movement.at.isoformat(),
                "subject": movement.subject,
                "project_id": movement.project_id,
                "parent_id": movement.parent_id,
                "parent_label": movement.parent_label,
                "from_status": _phase(movement.from_status),
                "to_status": _phase(movement.to_status),
            }
            for movement in brief.movements
        ],
        "highlights": [
            {
                "kind": highlight.kind.value,
                "project_id": highlight.project_id,
                "label": highlight.label,
            }
            for highlight in brief.highlights
        ],
    }


def from_json(month: date, payload: dict[str, Any]) -> Brief:
    """The facts back, whatever shape they were written in."""
    tally = payload.get("tally") or {}
    return Brief(
        month=month,
        tally=Tally(
            projects_created=tally.get("projects_created", 0),
            projects_archived=tally.get("projects_archived", 0),
            phase_changes=tally.get("phase_changes", 0),
            news_posted=tally.get("news_posted", 0),
            months_validated=tally.get("months_validated", 0),
        ),
        movements=[_movement(row) for row in payload.get("movements") or []],
        highlights=[_highlight(row) for row in payload.get("highlights") or []],
    )


def _phase(status: ProjectStatus | None) -> str | None:
    return status.value if status else None


def _movement(row: dict[str, Any]) -> Movement:
    return Movement(
        kind=MovementKind(row["kind"]),
        at=datetime.fromisoformat(row["at"]),
        subject=row["subject"],
        project_id=row.get("project_id"),
        parent_id=row.get("parent_id"),
        parent_label=row.get("parent_label"),
        from_status=_read_phase(row.get("from_status")),
        to_status=_read_phase(row.get("to_status")),
    )


def _read_phase(value: str | None) -> ProjectStatus | None:
    return ProjectStatus(value) if value else None


def _highlight(row: dict[str, Any]) -> Highlight:
    return Highlight(
        kind=HighlightKind(row["kind"]),
        project_id=row["project_id"],
        label=row["label"],
    )
