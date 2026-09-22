"""record the needs the company expresses

A request is not a mission: no time is booked against it, and it may be
refused or left to sleep. It therefore gets a table of its own, outside the
reference list, with the two short lists it carries — the departments it
concerns and the members of the COMEX it is carried to.

`audit_log` and `notifications` both gain a `request_id` beside their
`project_id`. A conversion writes one log line carrying both, which is what
lets the journal of a mission say which need it was born of; deleting the
mission empties `project_id` and leaves the need's own history alone.

Revision ID: a21bf6391bb2
Revises: 83281d2d6e4f
Create Date: 2026-09-22 23:29:23.103723

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a21bf6391bb2"
down_revision: str | None = "83281d2d6e4f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("requester_id", sa.Integer(), nullable=False),
        sa.Column(
            "state",
            sa.Enum(
                "DRAFT",
                "SUBMITTED",
                "ACCEPTED",
                "REJECTED",
                "DEFERRED",
                "CONVERTED",
                name="request_state",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("problem", sa.Text(), nullable=True),
        sa.Column("impact", sa.Text(), nullable=True),
        sa.Column("expected_outcome", sa.Text(), nullable=True),
        sa.Column("cost_of_inaction", sa.Text(), nullable=True),
        sa.Column("desired_by", sa.Date(), nullable=True),
        sa.Column("envisaged_solution", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by_id", sa.Integer(), nullable=True),
        sa.Column("decision_note", sa.Text(), nullable=True),
        sa.Column("converted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("converted_project_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["converted_project_id"], ["projects.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["decided_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_requests_requester_id"), "requests", ["requester_id"], unique=False
    )
    op.create_index(op.f("ix_requests_state"), "requests", ["state"], unique=False)
    op.create_table(
        "request_departments",
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column(
            "department",
            sa.Enum(
                "FINANCE_ADMIN",
                "LANDLORDS",
                "CONDOMINIUM",
                "CUSTOMER_SERVICE",
                "OPERATIONS",
                "INFORMATION_SYSTEMS",
                "HUMAN_RESOURCES",
                "MARKETING_COMMUNICATION_CSR",
                "COMMERCIAL_REAL_ESTATE",
                "OTHER",
                name="department",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["request_id"], ["requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("request_id", "department"),
    )
    op.create_table(
        "request_sponsors",
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("sponsor_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["request_id"], ["requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sponsor_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("request_id", "sponsor_id"),
    )
    op.add_column("audit_log", sa.Column("request_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_audit_log_request_id"), "audit_log", ["request_id"], unique=False
    )
    op.create_foreign_key(
        "fk_audit_log_request_id_requests",
        "audit_log",
        "requests",
        ["request_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column("notifications", sa.Column("request_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_notifications_request_id"),
        "notifications",
        ["request_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_notifications_request_id_requests",
        "notifications",
        "requests",
        ["request_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_notifications_request_id_requests", "notifications", type_="foreignkey"
    )
    op.drop_index(op.f("ix_notifications_request_id"), table_name="notifications")
    op.drop_column("notifications", "request_id")
    op.drop_constraint(
        "fk_audit_log_request_id_requests", "audit_log", type_="foreignkey"
    )
    op.drop_index(op.f("ix_audit_log_request_id"), table_name="audit_log")
    op.drop_column("audit_log", "request_id")
    op.drop_table("request_sponsors")
    op.drop_table("request_departments")
    op.drop_index(op.f("ix_requests_state"), table_name="requests")
    op.drop_index(op.f("ix_requests_requester_id"), table_name="requests")
    op.drop_table("requests")
