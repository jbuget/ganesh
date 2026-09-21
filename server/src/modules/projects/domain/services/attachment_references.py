"""Which files a message shows.

An image pasted into an update travels as an ordinary markdown link to the
address the API serves it at — `![capture](/api/v1/projects/4/attachments/12/content)`.
Reading those ids back is what lets a screen warn, before a file is withdrawn,
that a thread is about to show a hole where a picture was.

The id is what carries the file, never the name beside it: a file keeps the
name it was dropped under and the link keeps whatever the writer typed.
"""

import re

#: The address a file is served at, wherever it is cited from. The mission's
#: own id is captured only to be ignored — the file's is what identifies it.
_REFERENCE = re.compile(r"/api/v1/projects/\d+/attachments/(\d+)/content")


def referenced_ids(body: str) -> set[int]:
    """The files a message shows or links to, once each."""
    return {int(match.group(1)) for match in _REFERENCE.finditer(body)}
