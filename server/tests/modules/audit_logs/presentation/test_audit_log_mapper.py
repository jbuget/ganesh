"""What a line of the log carries out of its payload, and no more."""

from src.modules.audit_logs.application.dtos.audit_log_dto import SignedAuditLog
from src.modules.audit_logs.domain.entities.audit_log import AuditAction, AuditLog
from src.modules.audit_logs.presentation.api.mappers.audit_log_mapper import (
    to_audit_log_entry_response,
)


def read(payload: dict[str, object] | None):
    log = AuditLog(
        action=AuditAction.TAG_RECOLOR,
        actor_id=1,
        project_id=10,
        old_value="red",
        new_value="violet",
        payload=payload,
        id=1,
    )
    return to_audit_log_entry_response(SignedAuditLog(log, None, None))


def test_a_line_names_the_tag_it_is_about() -> None:
    assert read({"tag": "Suez", "tag_id": 4}).tag == "Suez"


def test_a_line_that_names_no_tag_says_none() -> None:
    assert read({"field": "label"}).tag is None
    assert read(None).tag is None


def test_the_rest_of_the_bookkeeping_stays_out_of_the_response() -> None:
    response = read({"tag": "Suez", "tag_id": 4}).model_dump()

    assert "tag_id" not in response
