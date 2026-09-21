"""Schemas of the audit log."""

from datetime import date, datetime

from pydantic import BaseModel

from src.modules.audit_logs.domain.entities.audit_log import AuditAction


class AuditPersonResponse(BaseModel):
    """Someone a line of the log names."""

    id: int
    display_name: str
    initials: str


class AuditProjectResponse(BaseModel):
    """The mission a line of the log is about."""

    id: int
    label: str


class AuditLogEntryResponse(BaseModel):
    """One line of the log, as a screen reads it.

    The wording is left to the client: the API says what happened, in the
    vocabulary the domain already writes it in, and the interface says it in
    French.
    """

    id: int
    at: datetime
    action: AuditAction
    #: Absent once the account that acted has been removed. The line stays.
    actor: AuditPersonResponse | None
    #: Whose month, or which contributor, the gesture was about.
    target_user: AuditPersonResponse | None
    #: The mission the gesture was about, named only where the reader is not
    #: already inside it. A mission's own log leaves it out on purpose: the
    #: page is the mission, and its name on every line would say nothing.
    project: AuditProjectResponse | None
    day: date | None
    #: Which field moved, for the gestures that change a mission field by field.
    field: str | None
    old_value: str | None
    new_value: str | None


class AuditLogPageResponse(BaseModel):
    """One page of the log, and how long the log is."""

    total: int
    entries: list[AuditLogEntryResponse]
