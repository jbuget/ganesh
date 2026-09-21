"""What it takes, in the register, for a project to have moved."""

from src.modules.audit_logs.domain.entities.audit_log import AuditAction

#: The gestures that move a project itself.
#:
#: Declared time is deliberately out. It is most of what the register holds,
#: and a list built on it would answer « who booked days on what », which is
#: the Synthèse d'activité's question and not this one: a project nobody has
#: touched in a month goes on rising to the top as long as somebody books an
#: hour against it.
#:
#: A month being arranged is out for the same reason — lining a project up on
#: one's own month changes the month, not the project. So is a deletion: there
#: is nothing left to go to.
MOVES_A_PROJECT = frozenset(
    {
        AuditAction.PROJECT_CREATE,
        AuditAction.PROJECT_UPDATE,
        AuditAction.PROJECT_STATUS_CHANGE,
        AuditAction.PROJECT_ASSIGN,
        AuditAction.PROJECT_UNASSIGN,
        AuditAction.ATTACHMENT_ADD,
        AuditAction.ATTACHMENT_RENAME,
        AuditAction.ATTACHMENT_REMOVE,
    }
)
