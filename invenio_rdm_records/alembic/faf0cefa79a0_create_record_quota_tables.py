#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create record and user quota tables."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types import UUIDType

# revision identifiers, used by Alembic.
revision = "faf0cefa79a0"
down_revision = "ffd725001655"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    # Get database inspector to check if tables already exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()

    # Create rdm_records_quota table if it doesn't exist
    records_quota_table = "rdm_records_quota"
    if records_quota_table not in existing_tables:
        op.create_table(
            records_quota_table,
            sa.Column("created", sa.DateTime(), nullable=False),
            sa.Column("updated", sa.DateTime(), nullable=False),
            sa.Column("id", UUIDType(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("quota_size", sa.BigInteger(), nullable=False),
            sa.Column("max_file_size", sa.BigInteger(), nullable=False),
            sa.Column("notes", sa.Text(), nullable=False),
            sa.Column("parent_id", UUIDType(), nullable=True),
            sa.ForeignKeyConstraint(
                ["parent_id"],
                ["rdm_parents_metadata.id"],
                name=op.f("fk_rdm_records_quota_parent_id_rdm_parents_metadata"),
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_rdm_records_quota")),
            sa.UniqueConstraint(
                "parent_id", name=op.f("uq_rdm_records_quota_parent_id")
            ),
            sa.UniqueConstraint("user_id", name=op.f("uq_rdm_records_quota_user_id")),
        )
        print(f"Created table {records_quota_table}.")
    else:
        print(f"Table {records_quota_table} already exists, skipping creation.")

    # Create rdm_users_quota table if it doesn't exist
    users_quota_table = "rdm_users_quota"
    if users_quota_table not in existing_tables:
        op.create_table(
            users_quota_table,
            sa.Column("created", sa.DateTime(), nullable=False),
            sa.Column("updated", sa.DateTime(), nullable=False),
            sa.Column("id", UUIDType(), nullable=False),
            sa.Column("quota_size", sa.BigInteger(), nullable=False),
            sa.Column("max_file_size", sa.BigInteger(), nullable=False),
            sa.Column("notes", sa.Text(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["accounts_user.id"],
                name=op.f("fk_rdm_users_quota_user_id_accounts_user"),
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_rdm_users_quota")),
            sa.UniqueConstraint("user_id", name=op.f("uq_rdm_users_quota_user_id")),
        )
        print(f"Created table {users_quota_table}.")
    else:
        print(f"Table {users_quota_table} already exists, skipping creation.")


def downgrade():
    """Downgrade database."""
    # Get database inspector to check if tables exist before dropping
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()

    # Drop rdm_users_quota table if it exists
    users_quota_table = "rdm_users_quota"
    if users_quota_table in existing_tables:
        op.drop_table(users_quota_table)
        print(f"Dropped table {users_quota_table}.")
    else:
        print(f"Table {users_quota_table} does not exist, skipping drop.")

    # Drop rdm_records_quota table if it exists
    records_quota_table = "rdm_records_quota"
    if records_quota_table in existing_tables:
        op.drop_table(records_quota_table)
        print(f"Dropped table {records_quota_table}.")
    else:
        print(f"Table {records_quota_table} does not exist, skipping drop.")
