"""How a file is handed to a browser.

Two decisions live here rather than in the router, because both are rules
rather than plumbing, and a rule that is only exercised through HTTP is a rule
nobody reads.
"""

from urllib.parse import quote

#: What a browser may be told to show in place. Anything may be dropped on a
#: mission, an HTML page included — and a page served inline from our own
#: domain would run in the reader's session, under their cookie. Everything
#: outside this list is therefore offered as a download, whatever it is.
SHOWABLE = ("image/", "application/pdf", "text/plain")


def may_be_shown(content_type: str) -> bool:
    """Whether the browser may render the file rather than offer to save it."""
    return content_type.startswith(SHOWABLE)


def disposition(filename: str, *, as_download: bool) -> str:
    """How the browser is told to treat the file.

    The name travels twice: folded down to ASCII for whoever still reads only
    that, and again as `filename*`, which is the one that carries « cahier de
    recette é.pdf » intact. A header is latin-1, and a raw accent in it is a
    500 rather than a download.
    """
    plain = filename.encode("ascii", "replace").decode("ascii").replace('"', "")
    kind = "attachment" if as_download else "inline"
    return f"{kind}; filename=\"{plain}\"; filename*=utf-8''{quote(filename)}"
