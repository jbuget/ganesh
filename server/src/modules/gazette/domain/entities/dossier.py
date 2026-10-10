"""What the model reads: the facts of the month, and what the team wrote."""

from dataclasses import dataclass, field

from src.modules.gazette.domain.entities.brief import Brief


@dataclass(frozen=True)
class ProjectMaterial:
    """What a reader would need to understand one project from outside."""

    project_id: int
    #: As the register spells it.
    label: str
    #: The service sheet's one line, when the team wrote one: what the project
    #: is for, told to someone who has never heard of it.
    summary: str | None = None
    #: What the team posted on it during the month, oldest first. Anonymous:
    #: who wrote a line is not what the gazette tells.
    excerpts: tuple[str, ...] = ()


@dataclass(frozen=True)
class Dossier:
    """The brief, and the material for the projects worth telling.

    Only the brief is kept with the digest. The material is read once, to be
    written over, and is not an archive: the updates it quotes are still in
    the project's thread. Without the background the editorial would have only
    three projects' words to go on, and would fill the rest with generalities.
    """

    brief: Brief
    material: dict[int, ProjectMaterial] = field(default_factory=dict)
    #: The other projects that moved or were written about, most telling first.
    #: They are context for the editorial and nothing more: no spotlight, no
    #: figure a text may quote, and none of it is kept with the digest.
    background: tuple[ProjectMaterial, ...] = ()
    #: Projects opened and closed within the month with nothing written on
    #: them. Left out of what the model is told: the register keeps them, a
    #: sentence about them would only be noise.
    quiet: frozenset[int] = frozenset()
