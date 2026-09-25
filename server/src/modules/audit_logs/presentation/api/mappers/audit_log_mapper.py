"""From the audit log to what a screen reads."""

from src.modules.audit_logs.application.dtos.audit_log_dto import (
    AuditLogPage,
    SignedAuditLog,
)
from src.modules.audit_logs.presentation.api.schemas.audit_log_schemas import (
    AuditLogEntryResponse,
    AuditLogPageResponse,
    AuditPersonResponse,
    AuditProjectResponse,
)
from src.modules.projects.domain.entities.project import Project
from src.modules.users.domain.entities.user import User
from src.shared.utils.initials import initials


def to_audit_person_response(person: User | None) -> AuditPersonResponse | None:
    if person is None or person.id is None:
        return None
    return AuditPersonResponse(
        id=person.id,
        display_name=person.label,
        initials=initials(person.label),
    )


def to_audit_project_response(mission: Project | None) -> AuditProjectResponse | None:
    if mission is None or mission.id is None:
        return None
    return AuditProjectResponse(id=mission.id, label=mission.label)


def to_audit_log_entry_response(signed: SignedAuditLog) -> AuditLogEntryResponse:
    log = signed.log
    assert log.id is not None
    # Two things are pulled out of the payload, and no more: which field moved,
    # and why a need was arbitrated so. The rest of what a gesture stores there
    # is its own business, and a screen reading it would end up depending on
    # the shape of every use case's bookkeeping.
    field = (log.payload or {}).get("field")
    note = (log.payload or {}).get("note")
    return AuditLogEntryResponse(
        id=log.id,
        at=log.at,
        action=log.action,
        actor=to_audit_person_response(signed.actor),
        target_user=to_audit_person_response(signed.target_user),
        project=to_audit_project_response(signed.project),
        day=log.day,
        field=None if field is None else str(field),
        note=None if note is None else str(note),
        old_value=log.old_value,
        new_value=log.new_value,
    )


def to_audit_log_page_response(page: AuditLogPage) -> AuditLogPageResponse:
    return AuditLogPageResponse(
        total=page.total,
        entries=[to_audit_log_entry_response(signed) for signed in page.entries],
    )
