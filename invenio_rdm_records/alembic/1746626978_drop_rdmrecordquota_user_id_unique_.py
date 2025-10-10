#
# This file is part of Invenio.
# Copyright (C) 2025 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Drop ``RDMRecordQuota.user_id`` unique constraint."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1746626978"
down_revision = "425b691f768b"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    # Get database inspector to check if constraint exists before dropping
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    table_name = "rdm_records_quota"
    constraint_name = "uq_rdm_records_quota_user_id"

    # Check if table exists
    if table_name not in inspector.get_table_names():
        print(f"Table {table_name} does not exist, skipping constraint drop.")
        return

    # Check if constraint exists before dropping
    try:
        # Get all unique constraints for the table
        unique_constraints = inspector.get_unique_constraints(table_name)
        constraint_exists = any(
            constraint["name"] == constraint_name for constraint in unique_constraints
        )

        if constraint_exists:
            op.drop_constraint(constraint_name, table_name, type_="unique")
            print(
                f"Dropped unique constraint {constraint_name} from table {table_name}."
            )
        else:
            print(
                f"Unique constraint {constraint_name} does not exist on table {table_name}, skipping drop."
            )

    except Exception as e:
        # Fallback: try to drop the constraint anyway (some databases might not support get_unique_constraints)
        try:
            op.drop_constraint(constraint_name, table_name, type_="unique")
            print(
                f"Dropped unique constraint {constraint_name} from table {table_name}."
            )
        except Exception:
            print(
                f"Could not drop constraint {constraint_name} - it may not exist or inspection failed: {e}"
            )


def downgrade():
    """Downgrade database."""
    # Get database inspector to check if constraint exists before creating
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    table_name = "rdm_records_quota"
    constraint_name = "uq_rdm_records_quota_user_id"

    # Check if table exists
    if table_name not in inspector.get_table_names():
        print(f"Table {table_name} does not exist, skipping constraint creation.")
        return

    # Check if user_id column exists
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    if "user_id" not in columns:
        print(
            f"Column user_id does not exist in table {table_name}, skipping constraint creation."
        )
        return

    # Check if constraint already exists before creating
    try:
        # Get all unique constraints for the table
        unique_constraints = inspector.get_unique_constraints(table_name)
        constraint_exists = any(
            constraint["name"] == constraint_name for constraint in unique_constraints
        )

        if not constraint_exists:
            op.create_unique_constraint(constraint_name, table_name, ["user_id"])
            print(f"Created unique constraint {constraint_name} on table {table_name}.")
        else:
            print(
                f"Unique constraint {constraint_name} already exists on table {table_name}, skipping creation."
            )

    except Exception as e:
        # Fallback: try to create the constraint anyway (some databases might not support get_unique_constraints)
        try:
            op.create_unique_constraint(constraint_name, table_name, ["user_id"])
            print(f"Created unique constraint {constraint_name} on table {table_name}.")
        except Exception:
            print(
                f"Could not create constraint {constraint_name} - it may already exist or inspection failed: {e}"
            )
