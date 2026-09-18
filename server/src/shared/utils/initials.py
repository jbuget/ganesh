"""Initiales affichees en pastille."""


def initials(nom: str) -> str:
    """At most two initials, taken from a display name.

    Directory names come as \u00ab L. Chen \u00bb: the dot separates as much as
    the space does, otherwise \u00ab L. \u00bb would yield a single initial.
    """
    mots = [mot for mot in nom.replace(".", " ").split() if mot]
    return "".join(mot[0].upper() for mot in mots[:2])
