"""How a file is handed to a browser.

Two decisions live here rather than in the router, because both are rules
rather than plumbing, and a rule that is only exercised through HTTP is a rule
nobody reads.
"""

from urllib.parse import quote

from src.modules.projects.domain.entities.project_attachment import (
    RENDERABLE_IMAGES,
    bare_type,
)

#: What is announced for everything else — and for anything we are not sure
#: of. A type nobody checked never reaches the browser.
DOWNLOAD_TYPE = "application/octet-stream"

#: What a browser may be told to show in place, **named one by one**. The list
#: used to read « image/ », which is the mistake this file exists to prevent:
#: `image/svg+xml` announces itself as an image and is a document that runs
#: scripts, and a prefix cannot tell the two apart. Served inline from our own
#: domain — the BFF hands it over on the application's own origin — it would
#: run under the reader's session. Everything outside this list is offered as
#: a download, whatever it is.
SHOWABLE = RENDERABLE_IMAGES | frozenset({"application/pdf", "text/plain"})

#: The net under the list: a document served from our origin runs nothing and
#: fetches nothing. Should a type ever make the list that should not have, its
#: scripts are refused before the closed list is even the question.
#:
#: `sandbox` is deliberately not in it. It would be stronger, and it would put
#: the document on an opaque origin — which is exactly what a browser's PDF
#: viewer is least sure how to render. `default-src 'none'` covers scripts
#: (which fall back to it) without touching how a PDF is drawn.
CONTENT_POLICY = "default-src 'none'; base-uri 'none'; form-action 'none'"


def served_as(content_type: str) -> str | None:
    """The type a browser may render this under, or nothing at all.

    What comes back is a member of `SHOWABLE`, never the string that was
    stored: the sender chose that one, and a type nobody checked has no
    business being written into a header.
    """
    kind = bare_type(content_type)
    return kind if kind in SHOWABLE else None


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
