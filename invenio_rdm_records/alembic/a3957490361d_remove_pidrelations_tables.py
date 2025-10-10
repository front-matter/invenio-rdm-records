#
# This file is part of Invenio.
# Copyright (C) 2021 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Remove PIDRelations tables."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a3957490361d"
down_revision = "88d1463de5c0"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    # Get database inspector to check if tables exist before dropping
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()

    # List of PID relations tables that might exist
    pidrelations_tables = [
        "pidrelations_pidrelation",
        "pidrelations_relation_metadata",  # Additional table that might exist
        "pidrelations_pidrelation_version",  # Version table that might exist
    ]

    tables_dropped = False

    for table_name in pidrelations_tables:
        if table_name in existing_tables:
            # Check if table has any indexes before dropping (for safety)
            try:
                indexes = inspector.get_indexes(table_name)
                if indexes:
                    print(
                        f"Table {table_name} has {len(indexes)} indexes, dropping table will remove them."
                    )

                op.drop_table(table_name)
                print(f"Dropped PIDRelations table: {table_name}")
                tables_dropped = True
            except Exception as e:
                print(f"Warning: Could not drop table {table_name}: {e}")
        else:
            print(f"PIDRelations table {table_name} does not exist, skipping drop.")

    if not tables_dropped:
        print("No PIDRelations tables found to drop.")
    else:
        print("PIDRelations tables cleanup completed.")


def downgrade():
    """Downgrade database."""
    # No turning back - PIDRelations tables cannot be recreated safely
    # because the data structure and dependencies are complex and
    # the original data would be lost after the upgrade.
    print("WARNING: Downgrade not possible for PIDRelations table removal.")
    print("This is a destructive migration that cannot be reversed.")
    print("PIDRelations tables and their data have been permanently removed.")
    print("If you need PIDRelations functionality, you must:")
    print("1. Restore from a backup taken before this migration")
    print("2. Or manually recreate the tables and data structure")
    pass
