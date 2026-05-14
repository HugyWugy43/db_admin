"""Удаление контуров (postgres_clusters), колонка access_privileges.

Revision ID: 6b7d8e9f0a11
Revises: 5c0e1a2b3f40
Create Date: 2026-05-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6b7d8e9f0a11"
down_revision: Union[str, None] = "5c0e1a2b3f40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if insp.has_table("databases"):
        for fk in insp.get_foreign_keys("databases"):
            if fk.get("name") == "fk_databases_postgres_cluster":
                op.drop_constraint("fk_databases_postgres_cluster", "databases", type_="foreignkey")
                break
        insp = sa.inspect(bind)
        ix_names = {ix["name"] for ix in insp.get_indexes("databases")}
        if "ix_databases_cluster_id" in ix_names:
            op.drop_index("ix_databases_cluster_id", table_name="databases")
        insp = sa.inspect(bind)
        cols = {c["name"] for c in insp.get_columns("databases")}
        if "cluster_id" in cols:
            op.drop_column("databases", "cluster_id")

    insp = sa.inspect(bind)
    if insp.has_table("postgres_clusters"):
        op.drop_table("postgres_clusters")

    insp = sa.inspect(bind)
    if insp.has_table("databases"):
        cols = {c["name"] for c in insp.get_columns("databases")}
        if "access_privileges" not in cols:
            op.add_column(
                "databases",
                sa.Column("access_privileges", sa.Text(), nullable=True),
            )


def downgrade() -> None:
    op.drop_column("databases", "access_privileges")
    op.create_table(
        "postgres_clusters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("host", sa.String(length=255), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False, server_default="5432"),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("is_shared", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("databases", sa.Column("cluster_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_databases_postgres_cluster",
        "databases",
        "postgres_clusters",
        ["cluster_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_databases_cluster_id", "databases", ["cluster_id"], unique=False)
