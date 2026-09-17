"""Schemas du referentiel des missions."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from src.modules.projects.domain.entities.project import (
    Department,
    ProjectCategory,
    ProjectKind,
    ProjectPriority,
    ProjectStatus,
)
from src.modules.projects.domain.entities.project_link import LinkIcon


class CreateProjectRequest(BaseModel):
    """Creation d'une mission."""

    label: str = Field(min_length=1, max_length=255)
    kind: ProjectKind
    status: ProjectStatus | None = None
    parent_id: int | None = None
    estimated_days: float | None = None


class ChangeStatusRequest(BaseModel):
    """Changement de phase d'une mission."""

    status: ProjectStatus


class ProjectResponse(BaseModel):
    """Une mission du referentiel."""

    id: int
    label: str
    kind: ProjectKind
    status: ProjectStatus | None
    parent_id: int | None
    is_active: bool
    #: Quand la mission a quitte le referentiel, nulle tant qu'elle y est.
    archived_at: datetime | None
    estimated_days: float | None
    category: ProjectCategory | None
    priority: ProjectPriority | None
    go_live_date: date | None
    position: int
    monday_item_id: str | None
    monday_subitem_id: str | None
    business_contacts: str | None
    description: str | None
    is_syncable_to_monday: bool
    is_deletable: bool


class LastUpdateResponse(BaseModel):
    """De quoi annoncer un fil de suivi sans l'ouvrir."""

    author: "BoardMemberResponse"
    body: str
    published_at: datetime


class ProjectListItemResponse(BaseModel):
    """Une mission du referentiel, avec qui s'en occupe."""

    project: ProjectResponse
    leads: list["BoardMemberResponse"]
    contributors: list["BoardMemberResponse"]
    #: Jours declares, previsionnel exclu.
    delivered_days: float
    #: Mises a jour vivantes du fil de suivi.
    comments: int
    #: La derniere d'entre elles, absente tant que rien ne se lit.
    latest_update: LastUpdateResponse | None


class UpdateProjectRequest(BaseModel):
    """Modification partielle : seuls les champs fournis sont appliques."""

    label: str | None = Field(default=None, min_length=1, max_length=255)
    status: ProjectStatus | None = None
    estimated_days: float | None = None
    category: ProjectCategory | None = None
    priority: ProjectPriority | None = None
    go_live_date: date | None = None
    is_active: bool | None = None
    parent_id: int | None = None
    monday_item_id: str | None = None
    monday_subitem_id: str | None = None


class ImportLineRequest(BaseModel):
    """Une ligne d'import, telle qu'elle sort d'un tableur."""

    label: str
    kind: ProjectKind = ProjectKind.PROJECT
    status: ProjectStatus | None = ProjectStatus.EXPLORATION
    parent_label: str | None = None
    estimated_days: float | None = None
    monday_item_id: str | None = None
    monday_subitem_id: str | None = None


class ImportProjectsRequest(BaseModel):
    """Import en masse du referentiel."""

    rows: list[ImportLineRequest]


class ImportReportResponse(BaseModel):
    """Ce que l'import a fait, ligne par ligne."""

    created: int
    skipped: int
    errors: list[str]


class MoveProjectRequest(BaseModel):
    """Depot d'une carte : colonne d'arrivee et rang voulu."""

    status: ProjectStatus
    position: int = Field(ge=0)


class BoardMemberResponse(BaseModel):
    """Un intervenant, tel qu'affiche en pastille sur une carte."""

    id: int
    display_name: str
    initials: str


class BoardParentResponse(BaseModel):
    """Le projet dont un lot releve, tel qu'annonce sur sa carte."""

    id: int
    label: str


class BoardCardResponse(BaseModel):
    """Une carte du tableau de bord."""

    project: ProjectResponse
    consumed_days: float
    contributors: list[BoardMemberResponse]
    comments: int
    #: Le dernier message du fil, absent tant que rien ne se lit.
    latest_update: LastUpdateResponse | None
    sub_projects: int
    parent: BoardParentResponse | None


class BoardColumnResponse(BaseModel):
    """Une phase et ses cartes."""

    status: ProjectStatus
    cards: list[BoardCardResponse]


class BoardResponse(BaseModel):
    """Le tableau complet, toutes phases confondues."""

    columns: list[BoardColumnResponse]


class ProjectLinkResponse(BaseModel):
    """Un lien utile attache a une mission."""

    id: int
    label: str
    url: str
    icon: LinkIcon


class AddLinkRequest(BaseModel):
    """Ajout d'un lien : une adresse, un intitule et une icone facultatifs.

    Sans icone, le serveur la deduit de l'adresse : l'ecran n'a pas a connaitre
    la liste des services reconnus.
    """

    label: str = ""
    url: str
    icon: LinkIcon | None = None


class PhaseReachedResponse(BaseModel):
    """Date a laquelle une mission est entree dans une phase."""

    status: ProjectStatus
    label: str
    reached_at: date


class MonthlyShareResponse(BaseModel):
    """Temps declare sur un mois donne."""

    month: date
    days: float


class ProjectContributionResponse(BaseModel):
    """Temps declare par une personne sur la mission."""

    member: BoardMemberResponse
    days: float
    by_month: list[MonthlyShareResponse]


class ProjectDetailResponse(BaseModel):
    """La fiche complete d'une mission."""

    project: ProjectResponse
    departments: list[Department]
    links: list[ProjectLinkResponse]
    phases: list[PhaseReachedResponse]
    leads: list[BoardMemberResponse]
    contributors: list[BoardMemberResponse]
    consumed_days: float
    contributions: list[ProjectContributionResponse]
    sub_projects: list[ProjectResponse]


class UpdateProjectDetailRequest(BaseModel):
    """Departements concernes et interlocuteurs metier."""

    departments: list[Department] = []
    business_contacts: str | None = None


class UpdateDescriptionRequest(BaseModel):
    """Fiche de service, en markdown."""

    description: str | None = None


class ProjectUpdateResponse(BaseModel):
    """Une mise a jour du fil de suivi."""

    id: int
    author: BoardMemberResponse
    body: str
    published_at: datetime
    edited_at: datetime | None
    is_deleted: bool
    #: Vrai si le lecteur courant peut la corriger ou la retirer.
    is_mine: bool


class PostUpdateRequest(BaseModel):
    """Publication ou correction d'une mise a jour."""

    body: str = Field(min_length=1)
