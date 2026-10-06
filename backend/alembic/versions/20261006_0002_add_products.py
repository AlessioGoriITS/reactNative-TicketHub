"""Add the demo product catalog and its ticket association.

Revision ID: 20261006_0002
Revises: 20261005_0001
Create Date: 2026-10-06 12:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20261006_0002"
down_revision: str | Sequence[str] | None = "20261005_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_products_code"),
        sa.UniqueConstraint("name", name="uq_products_name"),
    )
    op.add_column("tickets", sa.Column("product_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_tickets_product_id_products", "tickets", "products", ["product_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_tickets_product_id", "tickets", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_tickets_product_id", table_name="tickets")
    op.drop_constraint("fk_tickets_product_id_products", "tickets", type_="foreignkey")
    op.drop_column("tickets", "product_id")
    op.drop_table("products")
