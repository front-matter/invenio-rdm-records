#
# This file is part of Invenio.
# Copyright (C) 2023 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add origin and description to secret links."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a6bfa06b1a6d"
down_revision = "9e0ac518b9df"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    # Get database inspector to check if columns already exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    table_name = "rdm_records_secret_links"

    # Check if table exists before trying to modify it
    if table_name not in inspector.get_table_names():
        print(f"Table {table_name} does not exist, skipping column addition.")
        return

    # Get existing columns
    existing_columns = [col["name"] for col in inspector.get_columns(table_name)]

    # Add origin column if it doesn't exist
    if "origin" not in existing_columns:
        op.add_column(
            table_name,
            sa.Column("origin", sa.String(255), nullable=False, server_default=""),
        )
        print(f"Added 'origin' column to {table_name}.")
    else:
        print(f"Column 'origin' already exists in {table_name}, skipping addition.")

    # Add description column if it doesn't exist
    if "description" not in existing_columns:
        op.add_column(
            table_name,
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
        )
        print(f"Added 'description' column to {table_name}.")
    else:
        print(
            f"Column 'description' already exists in {table_name}, skipping addition."
        )


def downgrade():
    """Downgrade database."""
    # Get database inspector to check if columns exist before dropping
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    table_name = "rdm_records_secret_links"

    # Check if table exists before trying to modify it
    if table_name not in inspector.get_table_names():
        print(f"Table {table_name} does not exist, skipping column removal.")
        return

    # Get existing columns
    existing_columns = [col["name"] for col in inspector.get_columns(table_name)]

    # Drop description column if it exists
    if "description" in existing_columns:
        op.drop_column(table_name, "description")
        print(f"Dropped 'description' column from {table_name}.")
    else:
        print(f"Column 'description' does not exist in {table_name}, skipping drop.")

    # Drop origin column if it exists
    if "origin" in existing_columns:
        op.drop_column(table_name, "origin")
        print(f"Dropped 'origin' column from {table_name}.")
    else:
        print(f"Column 'origin' does not exist in {table_name}, skipping drop.")
