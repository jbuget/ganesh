"""Turning a name into an address."""

import re
import unicodedata


def slugify(value: str) -> str:
    """Lowercase letters, digits and single hyphens, nothing else.

    Accents are folded rather than dropped: « Jérémy » gives `jeremy`, not
    `jrmy`. What the catalogue names by handle is derived this way, so the two
    sides agree without a table to keep in step.
    """
    folded = unicodedata.normalize("NFD", value)
    plain = "".join(char for char in folded if not unicodedata.combining(char))
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", plain.lower())).strip("-")
