"""Projet, lot et activite hors projet : le referentiel des missions."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from src.shared.exceptions.domain_exceptions import ValidationError


class ProjectKind(StrEnum):
    """Nature d'une mission."""

    PROJET = "projet"
    LOT = "lot"
    HORS_PROJET = "hors_projet"


class ProjectStatus(StrEnum):
    """Phase de vie d'un projet ou d'un lot.

    L'ordre declare ici est l'ordre nominal, et celui des colonnes du tableau de
    bord. Un projet peut revenir en arriere : aucune transition n'est interdite.
    """

    EXPLORATION = "exploration"
    CADRAGE = "cadrage"
    REALISATION = "realisation"
    VALIDATION = "validation"
    DEPLOIEMENT = "deploiement"
    EXPLOITATION = "exploitation"


class ProjectPriority(StrEnum):
    """Urgence relative d'une mission, telle que l'equipe la declare.

    L'ordre declare ici va du plus urgent au moins urgent : c'est celui dans
    lequel les choix se presentent, et celui dans lequel on lit une liste.
    """

    CRITIQUE = "critique"
    HAUTE = "haute"
    NORMALE = "normale"
    BASSE = "basse"


class Department(StrEnum):
    """Departement de l'entreprise concerne par une mission.

    Une mission peut en servir plusieurs : un portail bailleurs qui outille
    aussi le service client concerne les deux, et le pilotage veut le voir.
    """

    ADMINISTRATIF_FINANCIER = "administratif_financier"
    BAILLEURS = "bailleurs"
    COPROPRIETE = "copropriete"
    SERVICE_CLIENT = "service_client"
    OPERATIONS = "operations"
    SYSTEME_INFORMATION = "systeme_information"
    RESSOURCES_HUMAINES = "ressources_humaines"
    MARKETING_COMMUNICATION_RSE = "marketing_communication_rse"
    TERTIAIRE = "tertiaire"
    AUTRE = "autre"


class ProjectCategory(StrEnum):
    """Axe strategique auquel un projet se rattache."""

    AUTOMATISER = "automatiser_fluidifier"
    PERENNISER = "perenniser_croissance"
    INNOVER = "innover_differencier"
    STRUCTURER = "structurer_plateforme"


@dataclass
class Project:
    """Une mission sur laquelle du temps peut etre impute."""

    id: int | None
    label: str
    kind: ProjectKind
    statut: ProjectStatus | None = ProjectStatus.EXPLORATION
    parent_id: int | None = None
    actif: bool = True
    estime_j: float | None = None
    categorie: ProjectCategory | None = None
    #: Urgence declaree. Facultative : une mission n'en porte que si l'equipe a
    #: juge utile de la situer par rapport aux autres.
    priorite: ProjectPriority | None = None
    date_mise_en_service: date | None = None
    #: Rang dans sa colonne du tableau de bord, choisi par l'equipe.
    position: int = 0
    monday_item_id: str | None = None
    monday_subitem_id: str | None = None
    #: Fiche de service en markdown : le probleme, la solution, ce qu'elle
    #: couvre. Destinee a nourrir la fiche publique du service.
    description: str | None = None
    #: Interlocuteurs metier, en texte libre : des noms, un service, un mail.
    contacts_metier: str | None = None

    def __post_init__(self) -> None:
        self.label = self.label.strip()
        if not self.label:
            raise ValidationError("Le libelle d'une mission ne peut pas etre vide.")

        if self.kind is ProjectKind.HORS_PROJET and self.statut is not None:
            raise ValidationError(
                "Une activite hors projet ne porte pas de statut de phase."
            )
        if self.kind is not ProjectKind.HORS_PROJET and self.statut is None:
            raise ValidationError("Un projet ou un lot doit porter un statut de phase.")

        if self.kind is ProjectKind.LOT and self.parent_id is None:
            raise ValidationError("Un lot doit etre rattache a un projet parent.")

        if self.position < 0:
            raise ValidationError("Le rang d'une mission ne peut pas etre negatif.")

    @property
    def is_off_project(self) -> bool:
        return self.kind is ProjectKind.HORS_PROJET

    @property
    def appears_on_board(self) -> bool:
        """Seul ce qui porte une phase se pilote sur le tableau de bord."""
        return not self.is_off_project

    @property
    def is_syncable_to_monday(self) -> bool:
        """Seules les missions rattachees a Monday remontent vers Monday."""
        if self.is_off_project:
            return False
        return bool(self.monday_item_id or self.monday_subitem_id)

    def change_status(self, new_status: ProjectStatus) -> None:
        """Change la phase du projet. Toute transition est permise."""
        if self.is_off_project:
            raise ValidationError(
                "Une activite hors projet ne porte pas de statut de phase."
            )
        self.statut = new_status
