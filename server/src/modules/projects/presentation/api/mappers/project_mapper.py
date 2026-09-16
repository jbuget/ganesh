"""Traduction des projets en schemas d'API."""

from src.modules.projects.application.use_cases.get_board import Board
from src.modules.projects.application.use_cases.list_projects import ListedProject
from src.modules.projects.domain.entities.project import Project
from src.modules.projects.presentation.api.schemas.project_schemas import (
    BoardCardResponse,
    BoardColumnResponse,
    BoardMemberResponse,
    BoardResponse,
    ProjectResponse,
)


def to_project_response(
    project: Project, is_deletable: bool = False
) -> ProjectResponse:
    assert project.id is not None
    return ProjectResponse(
        id=project.id,
        label=project.label,
        kind=project.kind,
        statut=project.statut,
        parent_id=project.parent_id,
        actif=project.actif,
        estime_j=project.estime_j,
        categorie=project.categorie,
        date_mise_en_service=project.date_mise_en_service,
        position=project.position,
        monday_item_id=project.monday_item_id,
        monday_subitem_id=project.monday_subitem_id,
        is_syncable_to_monday=project.is_syncable_to_monday,
        is_deletable=is_deletable,
    )


def to_listed_project_response(listed: ListedProject) -> ProjectResponse:
    return to_project_response(listed.project, is_deletable=listed.is_deletable)


def initiales(nom: str) -> str:
    """Initiales affichees en pastille sur une carte."""
    mots = [mot for mot in nom.replace(".", " ").split() if mot]
    return "".join(mot[0].upper() for mot in mots[:2])


def to_board_response(board: Board) -> BoardResponse:
    return BoardResponse(
        colonnes=[
            BoardColumnResponse(
                statut=colonne.statut,
                cartes=[
                    BoardCardResponse(
                        project=to_project_response(carte.project),
                        consomme_j=carte.consomme_j,
                        collaborateurs=[
                            BoardMemberResponse(
                                id=membre.id or 0,
                                display_name=membre.display_name,
                                initiales=initiales(membre.display_name),
                            )
                            for membre in carte.collaborateurs
                        ],
                    )
                    for carte in colonne.cartes
                ],
            )
            for colonne in board.colonnes
        ]
    )
