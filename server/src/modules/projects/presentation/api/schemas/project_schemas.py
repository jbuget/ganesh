"""Schemas du referentiel des missions."""

from datetime import date

from pydantic import BaseModel, Field

from src.modules.projects.domain.entities.project import (
    ProjectCategory,
    ProjectKind,
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
    date_mise_en_service: date | None
    position: int
    monday_item_id: str | None
    monday_subitem_id: str | None
    is_syncable_to_monday: bool
    is_deletable: bool


class UpdateProjectRequest(BaseModel):
    """Modification partielle : seuls les champs fournis sont appliques."""

    label: str | None = Field(default=None, min_length=1, max_length=255)
    statut: ProjectStatus | None = None
    estime_j: float | None = None
    categorie: ProjectCategory | None = None
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


class BoardCardResponse(BaseModel):
    """Une carte du tableau de bord."""

    project: ProjectResponse
    consomme_j: float
    collaborateurs: list[BoardMemberResponse]


class BoardColumnResponse(BaseModel):
    """Une phase et ses cartes."""

    statut: ProjectStatus
    cartes: list[BoardCardResponse]


class BoardResponse(BaseModel):
    """Le tableau complet, toutes phases confondues."""

    colonnes: list[BoardColumnResponse]
