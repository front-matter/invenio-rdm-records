#
# This file is part of Invenio.
# Copyright (C) 2023 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create access request tokens table."""

import sqlalchemy as sa
import sqlalchemy_utils as utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "cfcb8cb78708"
down_revision = "a6bfa06b1a6d"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    # Get database inspector to check if table already exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    table_name = "rdm_records_access_request_tokens"

    if table_name not in inspector.get_table_names():
        op.create_table(
            table_name,
            sa.Column("id", utils.types.uuid.UUIDType(), nullable=False),
            sa.Column("token", sa.String(512), nullable=False),
            sa.Column("created", sa.DateTime(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=False),
            sa.Column("email", sa.String(255), nullable=False),
            sa.Column("full_name", sa.String(255), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("record_pid", sa.String(255), nullable=False),
            sa.PrimaryKeyConstraint(
                "id", name=op.f("pk_rdm_records_access_request_tokens")
            ),
        )

        # Create index only if table was created
        op.create_index(
            op.f("ix_rdm_records_access_request_tokens_created"),
            table_name,
            ["created"],
            unique=False,
        )
        print(f"Created table {table_name} and its index.")
    else:
        print(f"Table {table_name} already exists, skipping creation.")

        # Check if index exists and create it if missing
        existing_indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
        index_name = "ix_rdm_records_access_request_tokens_created"
        if index_name not in existing_indexes:
            op.create_index(
                op.f(index_name),
                table_name,
                ["created"],
                unique=False,
            )
            print(f"Created missing index {index_name}.")
        else:
            print(f"Index {index_name} already exists, skipping creation.")


def downgrade():
    """Downgrade database."""
    # Get database inspector to check if table exists before dropping
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    table_name = "rdm_records_access_request_tokens"

    if table_name in inspector.get_table_names():
        # Check if index exists before dropping
        existing_indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
        index_name = "ix_rdm_records_access_request_tokens_created"

        if index_name in existing_indexes:
            op.drop_index(
                op.f(index_name),
                table_name=table_name,
            )
            print(f"Dropped index {index_name}.")
        else:
            print(f"Index {index_name} does not exist, skipping drop.")

        op.drop_table(table_name)
        print(f"Dropped table {table_name}.")
    else:
        print(f"Table {table_name} does not exist, skipping drop.")
