"""Schemas d'entree et de sortie des saisies."""

from datetime import date

from pydantic import BaseModel, Field

from src.modules.projects.domain.entities.project import ProjectKind


class SetEntryRequest(BaseModel):
    """Demande d'ecriture d'une saisie."""

    project_id: int
    jour: date
    valeur: float = Field(description="0.5 pour une demi-journee, 1 pour une journee")


class EntryResponse(BaseModel):
    """Une saisie enregistree."""

    project_id: int
    jour: date
    valeur: float


class CalendarDayResponse(BaseModel):
    """Un jour du mois et sa nature."""

    jour: date
    kind: str
    label: str | None = None
    is_off_day: bool


class GridRowResponse(BaseModel):
    """Une ligne de la matrice : une mission et ses saisies."""

    project_id: int
    label: str
    kind: ProjectKind
    estime_j: float | None
    values: dict[date, float]
    total_realise: float
    total_prevu: float
    total: float
    consomme_total_j: float


class DayTotalResponse(BaseModel):
    """Total saisi sur une journee."""

    jour: date
    total: float
    exceeds_capacity: bool


class MonthGridResponse(BaseModel):
    """La matrice complete d'un mois."""

    user_id: int
    mois: date
    days: list[CalendarDayResponse]
    rows: list[GridRowResponse]
    day_totals: list[DayTotalResponse]
    working_days: int
    is_writable: bool
    total_realise: float
    total_prevu: float
