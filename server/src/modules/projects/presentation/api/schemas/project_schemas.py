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


class CreateProjectRequest(BaseModel):
    """Creation d'une mission."""

    label: str = Field(min_length=1, max_length=255)
    kind: ProjectKind
    statut: ProjectStatus | None = None
    parent_id: int | None = None
    estime_j: float | None = None


class ChangeStatusRequest(BaseModel):
    """Changement de phase d'une mission."""

    statut: ProjectStatus


class ProjectResponse(BaseModel):
    """Une mission du referentiel."""

    id: int
    label: str
    kind: ProjectKind
    statut: ProjectStatus | None
    parent_id: int | None
    actif: bool
    estime_j: float | None
    categorie: ProjectCategory | None
    priorite: ProjectPriority | None
    date_mise_en_service: date | None
    position: int
    monday_item_id: str | None
    monday_subitem_id: str | None
    contacts_metier: str | None
    description: str | None
    is_syncable_to_monday: bool
    is_deletable: bool


class ProjectListItemResponse(BaseModel):
    """Une mission du referentiel, avec qui s'en occupe."""

    project: ProjectResponse
    referents: list["BoardMemberResponse"]
    intervenants: list["BoardMemberResponse"]
    #: Jours declares, previsionnel exclu.
    realise_j: float


class UpdateProjectRequest(BaseModel):
    """Modification partielle : seuls les champs fournis sont appliques."""

    label: str | None = Field(default=None, min_length=1, max_length=255)
    statut: ProjectStatus | None = None
    estime_j: float | None = None
    categorie: ProjectCategory | None = None
    priorite: ProjectPriority | None = None
    date_mise_en_service: date | None = None
    actif: bool | None = None
    parent_id: int | None = None
    monday_item_id: str | None = None
    monday_subitem_id: str | None = None


class ImportLineRequest(BaseModel):
    """Une ligne d'import, telle qu'elle sort d'un tableur."""

    label: str
    kind: ProjectKind = ProjectKind.PROJET
    statut: ProjectStatus | None = ProjectStatus.EXPLORATION
    parent_label: str | None = None
    estime_j: float | None = None
    monday_item_id: str | None = None
    monday_subitem_id: str | None = None


class ImportProjectsRequest(BaseModel):
    """Import en masse du referentiel."""

    lignes: list[ImportLineRequest]


class ImportReportResponse(BaseModel):
    """Ce que l'import a fait, ligne par ligne."""

    crees: int
    ignores: int
    erreurs: list[str]


class MoveProjectRequest(BaseModel):
    """Depot d'une carte : colonne d'arrivee et rang voulu."""

    statut: ProjectStatus
    position: int = Field(ge=0)


class BoardMemberResponse(BaseModel):
    """Un intervenant, tel qu'affiche en pastille sur une carte."""

    id: int
    display_name: str
    initiales: str


class BoardParentResponse(BaseModel):
    """Le projet dont un lot releve, tel qu'annonce sur sa carte."""

    id: int
    label: str


class BoardCardResponse(BaseModel):
    """Une carte du tableau de bord."""

    project: ProjectResponse
    consomme_j: float
    intervenants: list[BoardMemberResponse]
    commentaires: int
    sous_projets: int
    parent: BoardParentResponse | None


class BoardColumnResponse(BaseModel):
    """Une phase et ses cartes."""

    statut: ProjectStatus
    cartes: list[BoardCardResponse]


class BoardResponse(BaseModel):
    """Le tableau complet, toutes phases confondues."""

    colonnes: list[BoardColumnResponse]


class ProjectLinkResponse(BaseModel):
    """Un lien utile attache a une mission."""

    id: int
    label: str
    url: str


class AddLinkRequest(BaseModel):
    """Ajout d'un lien : une adresse, et un intitule facultatif."""

    label: str = ""
    url: str


class PhaseReachedResponse(BaseModel):
    """Date a laquelle une mission est entree dans une phase."""

    statut: ProjectStatus
    libelle: str
    reached_at: date


class MonthlyShareResponse(BaseModel):
    """Temps declare sur un mois donne."""

    mois: date
    jours: float


class ProjectContributionResponse(BaseModel):
    """Temps declare par une personne sur la mission."""

    member: BoardMemberResponse
    jours: float
    par_mois: list[MonthlyShareResponse]


class ProjectDetailResponse(BaseModel):
    """La fiche complete d'une mission."""

    project: ProjectResponse
    departements: list[Department]
    liens: list[ProjectLinkResponse]
    phases: list[PhaseReachedResponse]
    referents: list[BoardMemberResponse]
    intervenants: list[BoardMemberResponse]
    consomme_j: float
    contributions: list[ProjectContributionResponse]
    sous_projets: list[ProjectResponse]


class UpdateProjectDetailRequest(BaseModel):
    """Departements concernes et interlocuteurs metier."""

    departements: list[Department] = []
    contacts_metier: str | None = None


class UpdateDescriptionRequest(BaseModel):
    """Fiche de service, en markdown."""

    description: str | None = None


class ProjectUpdateResponse(BaseModel):
    """Une mise a jour du fil de suivi."""

    id: int
    author: BoardMemberResponse
    texte: str
    publiee_le: datetime
    modifiee_le: datetime | None
    est_supprimee: bool
    #: Vrai si le lecteur courant peut la corriger ou la retirer.
    est_la_mienne: bool


class PostUpdateRequest(BaseModel):
    """Publication ou correction d'une mise a jour."""

    texte: str = Field(min_length=1)
