"""The part someone plays on a mission."""

from enum import StrEnum


class ProjectRole(StrEnum):
    """On what grounds someone is attached to a mission.

    A contributor has their hands in it now or shortly; a lead answers for the
    choices and the contacts, throughout. The same person often holds both.
    """

    CONTRIBUTOR = "contributor"
    LEAD = "lead"
