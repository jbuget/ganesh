"""english schema

Renomme en anglais les colonnes et les valeurs d'enumeration restees en
francais. Les noms de tables etaient deja anglais.

Les colonnes `Enum` sont declarees `native_enum=False` : la base y stocke le
nom du membre Python, pas sa valeur. Renommer les membres du domaine oblige
donc a reecrire les donnees, d'ou les `UPDATE` qui suivent les renommages.

Revision ID: a1b2c3d4e5f6
Revises: c6c51b3985b4
Create Date: 2026-09-18

"""

from collections.abc import Sequence

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "c6c51b3985b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: (table, ancien nom, nouveau nom)
COLONNES = [
    ("audit_log", "jour", "day"),
    ("entries", "jour", "day"),
    ("entries", "valeur", "value"),
    ("entries", "statut_at_entry", "status_at_entry"),
    ("holidays", "jour", "day"),
    ("month_status", "mois", "month"),
    ("project_links", "icone", "icon"),
    ("project_phases_reached", "statut", "status"),
    ("project_updates", "texte", "body"),
    ("project_updates", "publiee_le", "published_at"),
    ("project_updates", "modifiee_le", "edited_at"),
    ("project_updates", "supprimee_le", "deleted_at"),
    ("projects", "statut", "status"),
    ("projects", "actif", "is_active"),
    ("projects", "estime_j", "estimated_days"),
    ("projects", "categorie", "category"),
    ("projects", "date_mise_en_service", "go_live_date"),
    ("projects", "contacts_metier", "business_contacts"),
    ("projects", "priorite", "priority"),
    ("user_missions", "mois", "month"),
    ("users", "actif", "is_active"),
    ("users", "derniere_connexion", "last_login_at"),
]

#: (table, colonne, ancien membre, nouveau membre)
MEMBRES = [
    ("projects", "status", "CADRAGE", "SCOPING"),
    ("projects", "status", "REALISATION", "DEVELOPMENT"),
    ("projects", "status", "DEPLOIEMENT", "DEPLOYMENT"),
    ("projects", "status", "EXPLOITATION", "OPERATIONS"),
    ("projects", "kind", "PROJET", "PROJECT"),
    ("projects", "kind", "LOT", "WORK_PACKAGE"),
    ("projects", "kind", "HORS_PROJET", "OFF_PROJECT"),
    ("projects", "category", "AUTOMATISER", "AUTOMATE"),
    ("projects", "category", "PERENNISER", "SUSTAIN"),
    ("projects", "category", "INNOVER", "INNOVATE"),
    ("projects", "category", "STRUCTURER", "STRUCTURE"),
    ("projects", "priority", "CRITIQUE", "CRITICAL"),
    ("projects", "priority", "HAUTE", "HIGH"),
    ("projects", "priority", "NORMALE", "NORMAL"),
    ("projects", "priority", "BASSE", "LOW"),
    ("entries", "status_at_entry", "CADRAGE", "SCOPING"),
    ("entries", "status_at_entry", "REALISATION", "DEVELOPMENT"),
    ("entries", "status_at_entry", "DEPLOIEMENT", "DEPLOYMENT"),
    ("entries", "status_at_entry", "EXPLOITATION", "OPERATIONS"),
    ("project_phases_reached", "status", "CADRAGE", "SCOPING"),
    ("project_phases_reached", "status", "REALISATION", "DEVELOPMENT"),
    ("project_phases_reached", "status", "DEPLOIEMENT", "DEPLOYMENT"),
    ("project_phases_reached", "status", "EXPLOITATION", "OPERATIONS"),
    ("month_status", "state", "OUVERT", "OPEN"),
    ("month_status", "state", "VALIDE", "VALIDATED"),
    ("project_assignees", "role", "INTERVENANT", "CONTRIBUTOR"),
    ("project_assignees", "role", "REFERENT", "LEAD"),
    ("project_departments", "department", "ADMINISTRATIF_FINANCIER", "FINANCE_ADMIN"),
    ("project_departments", "department", "BAILLEURS", "LANDLORDS"),
    ("project_departments", "department", "COPROPRIETE", "CONDOMINIUM"),
    ("project_departments", "department", "SERVICE_CLIENT", "CUSTOMER_SERVICE"),
    ("project_departments", "department", "SYSTEME_INFORMATION", "INFORMATION_SYSTEMS"),
    ("project_departments", "department", "RESSOURCES_HUMAINES", "HUMAN_RESOURCES"),
    (
        "project_departments",
        "department",
        "MARKETING_COMMUNICATION_RSE",
        "MARKETING_COMMUNICATION_CSR",
    ),
    ("project_departments", "department", "TERTIAIRE", "COMMERCIAL_REAL_ESTATE"),
    ("project_departments", "department", "AUTRE", "OTHER"),
    ("project_links", "icon", "LIEN", "LINK"),
    ("project_links", "icon", "DEPOT", "REPOSITORY"),
    ("project_links", "icon", "MAQUETTE", "DESIGN"),
    ("project_links", "icon", "TABLEUR", "SPREADSHEET"),
    ("project_links", "icon", "DOSSIER", "FOLDER"),
]


def _reecrire(membres: list[tuple[str, str, str, str]]) -> None:
    for table, colonne, avant, apres in membres:
        op.execute(
            f"UPDATE {table} SET {colonne} = '{apres}' WHERE {colonne} = '{avant}'"
        )


def upgrade() -> None:
    for table, avant, apres in COLONNES:
        op.alter_column(table, avant, new_column_name=apres)

    # La contrainte porte le nom de la colonne : elle se refait entierement.
    op.drop_constraint("ck_entry_valeur", "entries", type_="check")
    op.create_check_constraint("ck_entry_value", "entries", "value IN (0.5, 1.0)")

    _reecrire(MEMBRES)


def downgrade() -> None:
    _reecrire([(t, c, apres, avant) for t, c, avant, apres in MEMBRES])

    # La contrainte tombe avant le renommage, et se refait apres : son
    # expression nomme la colonne, qui n'a pas le meme nom des deux cotes.
    op.drop_constraint("ck_entry_value", "entries", type_="check")

    for table, avant, apres in reversed(COLONNES):
        op.alter_column(table, apres, new_column_name=avant)

    op.create_check_constraint("ck_entry_valeur", "entries", "valeur IN (0.5, 1.0)")
