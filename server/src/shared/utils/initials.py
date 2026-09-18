"""Initials shown in an avatar."""


def initials(name: str) -> str:
    """At most two initials, taken from a display name.

    Directory names come as « L. Chen »: the dot separates as much as
    the space does, otherwise « L. » would yield a single initial.
    """
    words = [word for word in name.replace(".", " ").split() if word]
    return "".join(word[0].upper() for word in words[:2])
