"""Traduction des projets en schemas d'API."""

from src.modules.projects.application.use_cases.get_board import Board
from src.modules.projects.application.use_cases.get_project_detail import ProjectDetail
from src.modules.projects.application.use_cases.list_projects import ListedProject
from src.modules.projects.application.use_cases.project_updates import SignedUpdate
from src.modules.projects.domain.entities.project import Project, ProjectStatus
from src.modules.projects.domain.services.phase_history import libelle_de_passage
from src.modules.projects.presentation.api.schemas.project_schemas import (
    BoardCardResponse,
    BoardColumnResponse,
    BoardMemberResponse,
    BoardParentResponse,
    BoardResponse,
    MonthlyShareResponse,
    PhaseReachedResponse,
    ProjectContributionResponse,
    ProjectDetailResponse,
    ProjectLinkResponse,
    ProjectResponse,
    ProjectUpdateResponse,
)
from src.modules.users.domain.entities.user import User
from src.shared.utils.initials import initiales


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
        contacts_metier=project.contacts_metier,
        description=project.description,
        is_syncable_to_monday=project.is_syncable_to_monday,
        is_deletable=is_deletable,
    )


def to_listed_project_response(listed: ListedProject) -> ProjectResponse:
    return to_project_response(listed.project, is_deletable=listed.is_deletable)


def to_board_response(board: Board) -> BoardResponse:
    return BoardResponse(
        colonnes=[
            BoardColumnResponse(
                statut=colonne.statut,
                cartes=[
                    BoardCardResponse(
                        project=to_project_response(carte.project),
                        consomme_j=carte.consomme_j,
                        intervenants=[
                            BoardMemberResponse(
                                id=membre.id or 0,
                                display_name=membre.display_name,
                                initiales=initiales(membre.display_name),
                            )
                            for membre in carte.intervenants
                        ],
                        commentaires=carte.commentaires,
                        sous_projets=carte.sous_projets,
                        parent=(
                            BoardParentResponse(
                                id=carte.parent.id or 0, label=carte.parent.label
                            )
                            if carte.parent is not None
                            else None
                        ),
                    )
                    for carte in colonne.cartes
                ],
            )
            for colonne in board.colonnes
        ]
    )


def to_project_detail_response(detail: ProjectDetail) -> ProjectDetailResponse:
    def en_pastille(user: User) -> BoardMemberResponse:
        assert user.id is not None
        return BoardMemberResponse(
            id=user.id,
            display_name=user.display_name,
            initiales=initiales(user.display_name),
        )

    return ProjectDetailResponse(
        project=to_project_response(detail.project),
        departements=detail.departements,
        liens=[
            ProjectLinkResponse(id=lien.id, label=lien.label, url=lien.url)
            for lien in detail.liens
            if lien.id is not None
        ],
        # Les phases se lisent dans l'ordre nominal, pas dans celui ou la base
        # les rend : une frise se parcourt du debut a la fin.
        phases=[
            PhaseReachedResponse(
                statut=statut,
                libelle=libelle_de_passage(statut),
                reached_at=detail.phases_atteintes[statut],
            )
            for statut in ProjectStatus
            if statut in detail.phases_atteintes
        ],
        referents=[en_pastille(u) for u in detail.referents],
        intervenants=[en_pastille(u) for u in detail.intervenants],
        consomme_j=detail.consomme_j,
        contributions=[
            ProjectContributionResponse(
                member=en_pastille(contribution.user),
                jours=contribution.jours,
                par_mois=[
                    MonthlyShareResponse(mois=mois, jours=jours)
                    for mois, jours in contribution.par_mois
                ],
            )
            for contribution in detail.contributions
        ],
        sous_projets=[to_project_response(lot) for lot in detail.sous_projets],
    )


def to_project_update_response(
    signee: SignedUpdate, lecteur_id: int
) -> ProjectUpdateResponse:
    assert signee.update.id is not None and signee.author.id is not None
    return ProjectUpdateResponse(
        id=signee.update.id,
        author=BoardMemberResponse(
            id=signee.author.id,
            display_name=signee.author.display_name,
            initiales=initiales(signee.author.display_name),
        ),
        texte=signee.update.texte,
        publiee_le=signee.update.publiee_le,
        modifiee_le=signee.update.modifiee_le,
        est_supprimee=signee.update.est_supprimee,
        est_la_mienne=signee.update.author_id == lecteur_id,
    )
