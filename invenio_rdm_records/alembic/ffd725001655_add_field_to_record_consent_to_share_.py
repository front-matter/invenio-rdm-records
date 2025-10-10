#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add field to record consent to share personal data for access request."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ffd725001655"
down_revision = "a2a6819f14f1"
branch_labels = ()
depends_on = "cfcb8cb78708"


def upgrade():
    """Upgrade database."""
    # Get database inspector to check if column already exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    table_name = "rdm_records_access_request_tokens"
    column_name = "consent_to_share_personal_data"

    # Check if table exists before trying to modify it
    if table_name not in inspector.get_table_names():
        print(f"Table {table_name} does not exist, skipping column addition.")
        return

    # Check if column already exists
    existing_columns = [col["name"] for col in inspector.get_columns(table_name)]

    if column_name not in existing_columns:
        op.add_column(
            table_name,
            sa.Column(column_name, sa.String(length=255), nullable=False),
        )
        print(f"Added '{column_name}' column to {table_name}.")
    else:
        print(
            f"Column '{column_name}' already exists in {table_name}, skipping addition."
        )


def downgrade():
    """Downgrade database."""
    # Get database inspector to check if column exists before dropping
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    table_name = "rdm_records_access_request_tokens"
    column_name = "consent_to_share_personal_data"

    # Check if table exists before trying to modify it
    if table_name not in inspector.get_table_names():
        print(f"Table {table_name} does not exist, skipping column removal.")
        return

    # Check if column exists before dropping
    existing_columns = [col["name"] for col in inspector.get_columns(table_name)]

    if column_name in existing_columns:
        op.drop_column(table_name, column_name)
        print(f"Dropped '{column_name}' column from {table_name}.")
    else:
        print(f"Column '{column_name}' does not exist in {table_name}, skipping drop.")
