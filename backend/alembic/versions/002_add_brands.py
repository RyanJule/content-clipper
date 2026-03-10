"""add brands table and brand_id to accounts

Revision ID: 002_add_brands
Revises: 001_initial_schema
Create Date: 2026-03-10 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "002_add_brands"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create brands table
    op.create_table(
        "brands",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_brands_id"), "brands", ["id"], unique=False)

    # Add brand_id foreign key to accounts
    op.add_column(
        "accounts",
        sa.Column("brand_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_accounts_brand_id",
        "accounts",
        "brands",
        ["brand_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_accounts_brand_id", "accounts", type_="foreignkey")
    op.drop_column("accounts", "brand_id")

    op.drop_index(op.f("ix_brands_id"), table_name="brands")
    op.drop_table("brands")
