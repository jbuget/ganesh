"""Which log a request writes to, and why it takes no lookup to decide.

The key is read from the public half of the token alone: no database call, no
hash, no authentication. A line is only ever written on a route that opened
its own machine door and checked the key there — a forged token never reaches
a use case at all.
"""

from src.modules.audit_logs.infrastructure.database.repositories.audit_log_repository_impl import (
    SqlAuditLogRepository,
)
from src.modules.audit_logs.infrastructure.machine_stamped_repository import (
    MachineStampedAuditLog,
)
from src.modules.entries.presentation.dependencies import get_audit_log_repository


class FakeSession:
    """Enough of a session for a repository to be built around it."""


def repository_for(authorization: str | None):  # type: ignore[no-untyped-def]
    return get_audit_log_repository(
        session=FakeSession(),  # type: ignore[arg-type]
        authorization=authorization,
    )


def test_a_teammate_writes_to_the_plain_log() -> None:
    assert isinstance(repository_for("Bearer an.entra.token"), SqlAuditLogRepository)


def test_a_call_with_no_header_writes_to_the_plain_log() -> None:
    assert isinstance(repository_for(None), SqlAuditLogRepository)


def test_a_machine_writes_to_a_log_that_names_its_key() -> None:
    stamped = repository_for("Bearer jns_ab12cd34ef56_" + "s" * 43)

    assert isinstance(stamped, MachineStampedAuditLog)
    # The public half alone, which is what the table of keys already shows.
    # What it then does with it is that class's own test.
    assert stamped.api_key == "jns_ab12cd34ef56"


def test_a_token_that_only_looks_like_ours_changes_nothing() -> None:
    # Malformed is not machine. The route will turn it away; the log does not
    # have to guess on its behalf.
    assert isinstance(repository_for("Bearer jns_broken"), SqlAuditLogRepository)
