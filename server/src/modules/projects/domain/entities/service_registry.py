"""What the service catalogue needs to know about a mission.

Timesheet steers the mission; the catalogue published on waat.tools describes
the service it produces. These few traits belong to the second reading, and to
it alone: nothing here changes how a month is filled in.
"""

import re
from enum import StrEnum

from src.shared.exceptions.domain_exceptions import ValidationError


class Criticality(StrEnum):
    """How much the company depends on the service running.

    The order declared here runs from the most critical to the least: it is the
    order the choices are offered in, and the order a list reads in.
    """

    CRITICAL = "critical"
    STANDARD = "standard"
    SECONDARY = "secondary"


class ServiceType(StrEnum):
    """The shape of what is delivered."""

    FRONTEND = "frontend"
    BACKEND = "backend"
    API = "api"
    FULLSTACK = "fullstack"
    WORKER = "worker"
    TOOL = "tool"


#: A slug is the address of the public page: lowercase, digits and single
#: hyphens, never leading or trailing.
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

SLUG_MAX_LENGTH = 100


def clean_slug(slug: str | None) -> str | None:
    """Trims a slug and refuses what would not make a readable address.

    The slug is not derived from the label: a published address must survive a
    mission being renamed, so it is chosen once and kept.
    """
    if slug is None:
        return None

    cleaned = slug.strip().lower()
    if not cleaned:
        return None
    if len(cleaned) > SLUG_MAX_LENGTH:
        raise ValidationError(f"A slug cannot exceed {SLUG_MAX_LENGTH} characters.")
    if not _SLUG.match(cleaned):
        raise ValidationError(
            "A slug takes lowercase letters, digits and single hyphens."
        )
    return cleaned
