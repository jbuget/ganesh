"""Who a message names.

A mention travels as a markdown link — `@[Nom](mention://user/12)` — and the
person it points at is carried by the **id**, never by the name: a name changes
with a marriage or a typo fixed, and a mention that had to be re-read from the
text would then point at nobody.
"""

import re

#: The shape a mention is written in. The name is captured only to be ignored:
#: it is what the reader sees, not what the link means.
_MENTION = re.compile(r"@\[[^\]]*\]\(mention://user/(\d+)\)")


def mentioned_ids(body: str) -> list[int]:
    """The people a message names, in the order they were named, once each."""
    seen: set[int] = set()
    ids: list[int] = []
    for match in _MENTION.finditer(body):
        who = int(match.group(1))
        if who not in seen:
            seen.add(who)
            ids.append(who)
    return ids
