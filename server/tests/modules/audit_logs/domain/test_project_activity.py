"""What counts as a project having moved, and what does not."""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction
from src.modules.audit_logs.domain.services.project_activity import MOVES_A_PROJECT


def test_dragging_a_card_across_the_board_moves_the_project() -> None:
    assert AuditAction.PROJECT_STATUS_CHANGE in MOVES_A_PROJECT


def test_a_file_put_on_a_project_moves_it() -> None:
    assert AuditAction.ATTACHMENT_ADD in MOVES_A_PROJECT


def test_declaring_time_does_not_move_the_project_it_is_booked_against() -> None:
    assert AuditAction.ENTRY_SET not in MOVES_A_PROJECT
    assert AuditAction.ENTRY_CLEAR not in MOVES_A_PROJECT


def test_arranging_ones_own_month_moves_the_month_not_the_project() -> None:
    assert AuditAction.MONTH_PROJECT_ADD not in MOVES_A_PROJECT
    assert AuditAction.MONTH_PROJECT_REMOVE not in MOVES_A_PROJECT


def test_a_deleted_project_has_nowhere_to_lead() -> None:
    assert AuditAction.PROJECT_DELETE not in MOVES_A_PROJECT


def test_every_gesture_read_is_one_the_register_writes() -> None:
    assert set(AuditAction) >= MOVES_A_PROJECT
