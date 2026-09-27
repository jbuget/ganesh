"""The part someone plays on a mission."""

from enum import StrEnum


class ProjectRole(StrEnum):
    """On what grounds someone is attached to a mission.

    A contributor has their hands in it now or shortly; a lead answers for the
    choices and the contacts, throughout; a technical lead is who to call when
    the service breaks, whether or not they are working on it this week. The
    same person often holds several of them.

    The three are read side by side rather than ranked: « qui y travaille en
    ce moment » and « qui saurait réparer » are two questions, and a list
    answering both would answer neither.
    """

    CONTRIBUTOR = "contributor"
    LEAD = "lead"
    TECH_LEAD = "tech_lead"
