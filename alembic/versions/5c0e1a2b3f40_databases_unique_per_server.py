"""Уникальность подключения: (owner, host, port, database_name), не только имя.

Revision ID: 5c0e1a2b3f40
Revises: 4f2a8c1d9e00
Create Date: 2026-05-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5c0e1a2b3f40"
down_revision: Union[str, None] = "4f2a8c1d9e00"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    for uc in insp.get_unique_constraints("databases"):
        if uc.get("name") == "unique_owner_database_name":
            op.drop_constraint("unique_owner_database_name", "databases", type_="unique")
            break
    insp = sa.inspect(bind)
    names = {uc.get("name") for uc in insp.get_unique_constraints("databases")}
    if "unique_owner_host_port_database_name" not in names:
        op.create_unique_constraint(
            "unique_owner_host_port_database_name",
            "databases",
            ["owner_id", "host", "port", "database_name"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    for uc in insp.get_unique_constraints("databases"):
        if uc.get("name") == "unique_owner_host_port_database_name":
            op.drop_constraint("unique_owner_host_port_database_name", "databases", type_="unique")
            break
    names = {uc.get("name") for uc in sa.inspect(bind).get_unique_constraints("databases")}
    if "unique_owner_database_name" not in names:
        op.create_unique_constraint(
            "unique_owner_database_name",
            "databases",
            ["owner_id", "name"],
        )
