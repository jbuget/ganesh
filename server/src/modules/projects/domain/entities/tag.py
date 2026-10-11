"""The tag: a label the team puts on a mission to find it again."""

import unicodedata
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from src.shared.exceptions.domain_exceptions import ValidationError

MAX_TAG_NAME_LENGTH = 40


class TagColor(StrEnum):
    """The colour a tag is drawn in.

    The set is closed, as the signs of a reaction are: a free hexadecimal would
    give twenty blues nobody can tell apart, and a colour that is no longer one
    of ten no longer says anything at a glance. The domain names it, the
    interface paints it — and the name is always read beside it, so the colour
    is never the only thing that tells two tags apart.

    The order of the members is the order the palette is drawn in, and the one a
    new tag is given a colour from.
    """

    RED = "red"
    ORANGE = "orange"
    AMBER = "amber"
    LIME = "lime"
    GREEN = "green"
    TEAL = "teal"
    SKY = "sky"
    BLUE = "blue"
    VIOLET = "violet"
    PINK = "pink"


#: The colours in the order they are drawn and handed out. Built by hand rather
#: than `tuple(TagColor)`, which the type checker reads as a tuple of strings.
PALETTE: tuple[TagColor, ...] = tuple(color for color in TagColor)


def least_used_color(worn: Iterable[TagColor]) -> TagColor:
    """The colour worn by the fewest tags, the first of the palette on a tie.

    A tag is born without anybody choosing its colour, so that creating one
    stays a keystroke rather than a form. Spreading the colours is what keeps
    two neighbours on a mission from being drawn alike.
    """
    usage = Counter(worn)
    return min(PALETTE, key=lambda color: usage[color])


def tag_key(name: str) -> str:
    unaccented = unicodedata.normalize("NFKD", name)
    unaccented = "".join(c for c in unaccented if not unicodedata.combining(c))
    separated = unaccented.replace("-", " ").replace("_", " ")
    return " ".join(separated.lower().split())


@dataclass
class Tag:
    """A word the team shares to say what a mission is about.

    « IA », « Frigo », « Chronopost », « Suez », « France Énergie 2030 » — a
    theme, a client, a partner, a programme. A tag classes a mission and never
    says where it stands: that is what the updates are for, and a tag that
    tried would be a phase nobody dated.
    """

    id: int | None
    name: str
    color: TagColor

    def __post_init__(self) -> None:
        self.name = self._checked(self.name)

    @property
    def key(self) -> str:
        """What makes two tags the same one: the name, read without its case,
        its accents, or the way its words are separated.

        « Suez-Env », « suez env » and « Suez_Env » are one tag. Held here
        rather than on a screen, so that no way in — the picker, the import, a
        tool — can open a second one beside it.
        """
        return tag_key(self.name)

    def rename(self, name: str) -> None:
        self.name = self._checked(name)

    def recolor(self, color: TagColor) -> None:
        self.color = color

    @staticmethod
    def _checked(name: str) -> str:
        name = name.strip()
        if not name:
            raise ValidationError("A tag needs a name.")
        if len(name) > MAX_TAG_NAME_LENGTH:
            raise ValidationError(
                f"A tag name holds {MAX_TAG_NAME_LENGTH} characters at most."
            )
        return name


@dataclass(frozen=True)
class TagUsage:
    """A tag, and how many missions carry it."""

    tag: Tag
    project_count: int
