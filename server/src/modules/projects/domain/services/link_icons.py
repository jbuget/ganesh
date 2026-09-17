"""Ce qu'une adresse laisse deviner de la nature d'un lien.

Coller une adresse suffit a poser un lien : plutot que d'obliger a choisir une
icone, on la propose a partir du service vise. L'auteur garde le dernier mot.
"""

from urllib.parse import urlparse

from src.modules.projects.domain.entities.project_link import LinkIcon

#: Services reconnus, par domaine. Un sous-domaine herite du sien : l'espace
#: Slack d'une equipe vit sous `<equipe>.slack.com`.
_ICONE_PAR_DOMAINE = {
    "github.com": LinkIcon.DEPOT,
    "gitlab.com": LinkIcon.DEPOT,
    "bitbucket.org": LinkIcon.DEPOT,
    "figma.com": LinkIcon.MAQUETTE,
    "notion.so": LinkIcon.DOCUMENT,
    "notion.site": LinkIcon.DOCUMENT,
    "slack.com": LinkIcon.DISCUSSION,
    "teams.microsoft.com": LinkIcon.DISCUSSION,
    "monday.com": LinkIcon.TICKET,
    "atlassian.net": LinkIcon.TICKET,
    "linear.app": LinkIcon.TICKET,
    "drive.google.com": LinkIcon.DOSSIER,
    "sharepoint.com": LinkIcon.DOSSIER,
    "dropbox.com": LinkIcon.DOSSIER,
    "meet.google.com": LinkIcon.VIDEO,
    "zoom.us": LinkIcon.VIDEO,
    "loom.com": LinkIcon.VIDEO,
    "youtube.com": LinkIcon.VIDEO,
    "youtu.be": LinkIcon.VIDEO,
}

#: Google sert trois outils depuis `docs.google.com` : seul le chemin les separe.
_ICONE_PAR_CHEMIN_GOOGLE = {
    "document": LinkIcon.DOCUMENT,
    "spreadsheets": LinkIcon.TABLEUR,
    "presentation": LinkIcon.PRESENTATION,
}


def deviner_icone(url: str) -> LinkIcon:
    """Propose une icone d'apres l'adresse. Une adresse inconnue reste neutre."""
    adresse = urlparse(url.strip())
    host = (adresse.hostname or "").lower()

    if _correspond(host, "docs.google.com"):
        premier_segment = adresse.path.lstrip("/").split("/")[0]
        return _ICONE_PAR_CHEMIN_GOOGLE.get(premier_segment, LinkIcon.DOCUMENT)

    for domaine, icone in _ICONE_PAR_DOMAINE.items():
        if _correspond(host, domaine):
            return icone

    return LinkIcon.LIEN


def _correspond(host: str, domaine: str) -> bool:
    """Le domaine lui-meme, ou l'un de ses sous-domaines — et rien d'autre.

    La comparaison se fait sur un point : sans lui, `monfigma.com` passerait
    pour Figma.
    """
    return host == domaine or host.endswith(f".{domaine}")
