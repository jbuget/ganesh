"""What an address lets one guess about the nature of a link.

Pasting an address is enough to add a link: rather than forcing a choice of
icon, one is suggested from the service it points to. The author has the last
word.
"""

from urllib.parse import urlparse

from src.modules.projects.domain.entities.project_link import LinkIcon

#: Known services, by domain. A subdomain inherits from its own: a team's
#: Slack space lives under `<team>.slack.com`.
_ICON_BY_DOMAIN = {
    "github.com": LinkIcon.REPOSITORY,
    "gitlab.com": LinkIcon.REPOSITORY,
    "bitbucket.org": LinkIcon.REPOSITORY,
    "figma.com": LinkIcon.DESIGN,
    "notion.so": LinkIcon.DOCUMENT,
    "notion.site": LinkIcon.DOCUMENT,
    "slack.com": LinkIcon.DISCUSSION,
    "teams.microsoft.com": LinkIcon.DISCUSSION,
    "monday.com": LinkIcon.TICKET,
    "atlassian.net": LinkIcon.TICKET,
    "linear.app": LinkIcon.TICKET,
    "drive.google.com": LinkIcon.FOLDER,
    "sharepoint.com": LinkIcon.FOLDER,
    "dropbox.com": LinkIcon.FOLDER,
    "meet.google.com": LinkIcon.VIDEO,
    "zoom.us": LinkIcon.VIDEO,
    "loom.com": LinkIcon.VIDEO,
    "youtube.com": LinkIcon.VIDEO,
    "youtu.be": LinkIcon.VIDEO,
}

#: Google serves three tools from `docs.google.com`: only the path tells them apart.
_ICON_BY_GOOGLE_PATH = {
    "document": LinkIcon.DOCUMENT,
    "spreadsheets": LinkIcon.SPREADSHEET,
    "presentation": LinkIcon.PRESENTATION,
}


def guess_icon(url: str) -> LinkIcon:
    """Suggests an icon from the address. An unknown address stays neutral."""
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower()

    if _matches(host, "docs.google.com"):
        first_segment = parsed.path.lstrip("/").split("/")[0]
        return _ICON_BY_GOOGLE_PATH.get(first_segment, LinkIcon.DOCUMENT)

    for domain, icon in _ICON_BY_DOMAIN.items():
        if _matches(host, domain):
            return icon

    return LinkIcon.LINK


def _matches(host: str, domain: str) -> bool:
    """The domain itself, or one of its subdomains — and nothing else.

    The comparison hinges on a dot: without it, `myfigma.com` would pass for
    Figma.
    """
    return host == domain or host.endswith(f".{domain}")
