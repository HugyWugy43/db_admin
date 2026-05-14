"""postgres clusters + databases.cluster_id

Revision ID: 4f2a8c1d9e00
Revises: 3bce1926ff36
Create Date: 2026-05-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4f2a8c1d9e00"
down_revision: Union[str, None] = "3bce1926ff36"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not insp.has_table("postgres_clusters"):
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
        op.create_index("ix_postgres_clusters_owner_id", "postgres_clusters", ["owner_id"], unique=False)
        op.create_index(op.f("ix_postgres_clusters_id"), "postgres_clusters", ["id"], unique=False)

    def _databases_cluster_fk_exists() -> bool:
        for fk in sa.inspect(bind).get_foreign_keys("databases"):
            if fk.get("referred_table") == "postgres_clusters":
                return True
        return False

    insp = sa.inspect(bind)
    db_cols = {c["name"] for c in insp.get_columns("databases")}
    if "cluster_id" not in db_cols:
        op.add_column("databases", sa.Column("cluster_id", sa.Integer(), nullable=True))

    insp = sa.inspect(bind)
    db_cols = {c["name"] for c in insp.get_columns("databases")}
    if "cluster_id" in db_cols and not _databases_cluster_fk_exists():
        op.create_foreign_key(
            "fk_databases_postgres_cluster",
            "databases",
            "postgres_clusters",
            ["cluster_id"],
            ["id"],
            ondelete="SET NULL",
        )

    insp = sa.inspect(bind)
    db_cols = {c["name"] for c in insp.get_columns("databases")}
    ix_db = {ix["name"] for ix in insp.get_indexes("databases")}
    if "cluster_id" in db_cols and "ix_databases_cluster_id" not in ix_db:
        op.create_index("ix_databases_cluster_id", "databases", ["cluster_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_databases_cluster_id", table_name="databases")
    op.drop_constraint("fk_databases_postgres_cluster", "databases", type_="foreignkey")
    op.drop_column("databases", "cluster_id")
    op.drop_index(op.f("ix_postgres_clusters_id"), table_name="postgres_clusters")
    op.drop_index("ix_postgres_clusters_owner_id", table_name="postgres_clusters")
    op.drop_table("postgres_clusters")
