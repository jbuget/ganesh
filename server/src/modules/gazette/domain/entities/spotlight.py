"""A project the month is told through, in a few sentences."""

from dataclasses import dataclass

from src.shared.exceptions.domain_exceptions import ValidationError


@dataclass(frozen=True)
class Spotlight:
    """What a model wrote about one of the month's projects.

    The project is chosen by rule, never by the model: it only turns the
    phrase. The text goes through the same figure rule as the editorial, and
    a spotlight that breaks it is dropped alone.
    """

    project_id: int
    #: As the register spelled it that month.
    label: str
    text: str
    #: Which model wrote it, kept with the text: a numéro may hold a
    #: spotlight and no editorial, and a reader weighs both as machine-written.
    model: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "label", self.label.strip())
        object.__setattr__(self, "text", self.text.strip())
        if not self.label:
            raise ValidationError("A spotlight names its project.")
        object.__setattr__(self, "model", self.model.strip())
        if not self.text:
            raise ValidationError("A spotlight cannot be empty.")
        if not self.model:
            raise ValidationError("A spotlight says which model wrote it.")
