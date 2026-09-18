"""english schema

Renames to English the columns and enumeration values that had stayed in
French. Table names were already English.

`Enum` columns are declared `native_enum=False`: the database stores the name
of the Python member, not its value. Renaming the domain's members therefore
forces a rewrite of the data, hence the `UPDATE`s that follow the renames.

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

#: (table, old name, new name)
COLUMNS = [
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

#: (table, old constraint, new constraint)
#:
#: PostgreSQL names NOT NULL constraints after the column at creation time,
#: and renaming the column does not carry them along. They get in the way of
#: nothing — `alembic check` does not even see them — but a schema whose only
#: remaining French names are invisible to the tooling is a trap: nobody will
#: ever fix them, for want of seeing them.
CONSTRAINTS = [
    ("entries", "entries_jour_not_null", "entries_day_not_null"),
    ("entries", "entries_valeur_not_null", "entries_value_not_null"),
    ("holidays", "holidays_jour_not_null", "holidays_day_not_null"),
    ("month_status", "month_status_mois_not_null", "month_status_month_not_null"),
    ("project_links", "project_links_icone_not_null", "project_links_icon_not_null"),
    (
        "project_phases_reached",
        "project_phases_reached_statut_not_null",
        "project_phases_reached_status_not_null",
    ),
    (
        "project_updates",
        "project_updates_publiee_le_not_null",
        "project_updates_published_at_not_null",
    ),
    (
        "project_updates",
        "project_updates_texte_not_null",
        "project_updates_body_not_null",
    ),
    ("projects", "projects_actif_not_null", "projects_is_active_not_null"),
    ("user_missions", "user_missions_mois_not_null", "user_missions_month_not_null"),
    ("users", "users_actif_not_null", "users_is_active_not_null"),
]

#: (old index, new index)
#:
#: Renaming a column does not rename the index that carries it: the schema
#: would stay out of step with the models, and `alembic check` says so.
#: `ALTER INDEX` is enough — the index is kept, not rebuilt.
INDEX = [
    ("ix_entries_jour", "ix_entries_day"),
    ("ix_month_status_mois", "ix_month_status_month"),
    ("ix_projects_actif", "ix_projects_is_active"),
    ("ix_user_missions_mois", "ix_user_missions_month"),
    ("ix_users_actif", "ix_users_is_active"),
]

#: (table, column, old member, new member)
MEMBERS = [
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


def _rename_constraints(constraints: list[tuple[str, str, str]]) -> None:
    for table, before, after in constraints:
        op.execute(f"ALTER TABLE {table} RENAME CONSTRAINT {before} TO {after}")


def _rename_indexes(index: list[tuple[str, str]]) -> None:
    for before, after in index:
        op.execute(f"ALTER INDEX {before} RENAME TO {after}")


def _rewrite_members(members: list[tuple[str, str, str, str]]) -> None:
    for table, column, before, after in members:
        op.execute(
            f"UPDATE {table} SET {column} = '{after}' WHERE {column} = '{before}'"
        )


def upgrade() -> None:
    for table, before, after in COLUMNS:
        op.alter_column(table, before, new_column_name=after)

    _rename_indexes(INDEX)
    _rename_constraints(CONSTRAINTS)

    # The constraint carries the column's name: it is remade in full.
    op.drop_constraint("ck_entry_valeur", "entries", type_="check")
    op.create_check_constraint("ck_entry_value", "entries", "value IN (0.5, 1.0)")

    _rewrite_members(MEMBERS)

    # The audit log names the field it touched in its payload: the key follows
    # the rest, otherwise one and the same trace would read « champ » before the
    # switch and « field » after.
    op.execute(
        """
        UPDATE audit_log
        SET payload = (
            (payload::jsonb - 'champ')
            || jsonb_build_object('field', payload::jsonb -> 'champ')
        )::json
        WHERE payload::text LIKE '%"champ"%'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE audit_log
        SET payload = (
            (payload::jsonb - 'field')
            || jsonb_build_object('champ', payload::jsonb -> 'field')
        )::json
        WHERE payload::text LIKE '%"field"%'
        """
    )

    _rewrite_members([(t, c, after, before) for t, c, before, after in MEMBERS])

    # The constraint is dropped before the rename and remade after: its
    # expression names the column, which does not carry the same name on both
    # sides.
    op.drop_constraint("ck_entry_value", "entries", type_="check")

    _rename_constraints([(t, after, before) for t, before, after in CONSTRAINTS])
    _rename_indexes([(after, before) for before, after in INDEX])

    for table, before, after in reversed(COLUMNS):
        op.alter_column(table, after, new_column_name=before)

    op.create_check_constraint("ck_entry_valeur", "entries", "valeur IN (0.5, 1.0)")
