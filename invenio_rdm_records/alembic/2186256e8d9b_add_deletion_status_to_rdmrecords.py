#
# This file is part of Invenio.
# Copyright (C) 2023 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add deletion status to RDMRecords."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2186256e8d9b"
down_revision = "ff860d48fb4b"
branch_labels = ()
depends_on = None


def _get_default_deletion_status():
    """Try to get the default value for record deletion status."""
    try:
        # first try: get the default value from the DB model class
        from invenio_rdm_records.records.models import RDMRecordMetadata

        default_value = RDMRecordMetadata.deletion_status.default.arg
        assert len(default_value) == 1

    except Exception:
        try:
            # second try: try to get the value from the enum (more flaky)
            from invenio_rdm_records.records.systemfields.deletion_status import (
                RecordDeletionStatusEnum,
            )

            default_value = RecordDeletionStatusEnum.PUBLISHED.value
            assert len(default_value) == 1

        except Exception:
            # fallback: just use 'P', as that's the current default (most flaky)
            default_value = "P"

    return default_value


def upgrade():
    """Upgrade database."""
    # Get database inspector to check if columns already exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    # Check if tables exist before trying to modify them
    existing_tables = inspector.get_table_names()

    if "rdm_records_metadata" not in existing_tables:
        print("Table rdm_records_metadata does not exist, skipping column addition.")
        return

    if "rdm_records_metadata_version" not in existing_tables:
        print(
            "Table rdm_records_metadata_version does not exist, skipping column addition."
        )
        return

    # Check if columns already exist
    metadata_columns = [
        col["name"] for col in inspector.get_columns("rdm_records_metadata")
    ]
    metadata_version_columns = [
        col["name"] for col in inspector.get_columns("rdm_records_metadata_version")
    ]

    column_added = False

    # step 1: create the columns, but make them nullable for now
    if "deletion_status" not in metadata_columns:
        op.add_column(
            "rdm_records_metadata",
            sa.Column("deletion_status", sa.String(length=1), nullable=True),
        )
        column_added = True
        print("Added deletion_status column to rdm_records_metadata.")
    else:
        print(
            "Column deletion_status already exists in rdm_records_metadata, skipping addition."
        )

    if "deletion_status" not in metadata_version_columns:
        op.add_column(
            "rdm_records_metadata_version",
            sa.Column(
                "deletion_status",
                sa.String(length=1),
                nullable=True,
            ),
        )
        column_added = True
        print("Added deletion_status column to rdm_records_metadata_version.")
    else:
        print(
            "Column deletion_status already exists in rdm_records_metadata_version, skipping addition."
        )

    # step 2: set default values for existing rows (only if we added columns)
    if column_added:
        default_value = _get_default_deletion_status()
        metadata_table = sa.sql.table(
            "rdm_records_metadata", sa.sql.column("deletion_status")
        )
        metadata_version_table = sa.sql.table(
            "rdm_records_metadata_version", sa.sql.column("deletion_status")
        )

        # Only update rows that have NULL values
        op.execute(
            metadata_table.update()
            .where(sa.sql.column("deletion_status").is_(None))
            .values(deletion_status=default_value)
        )
        op.execute(
            metadata_version_table.update()
            .where(sa.sql.column("deletion_status").is_(None))
            .values(deletion_status=default_value)
        )
        print(
            f"Set default deletion_status values to '{default_value}' for existing rows."
        )

    # step 3: make the original table not nullable (check if it's already NOT NULL)
    if "deletion_status" in metadata_columns:
        # Check if column is already NOT NULL
        metadata_col_info = next(
            (
                col
                for col in inspector.get_columns("rdm_records_metadata")
                if col["name"] == "deletion_status"
            ),
            None,
        )

        if metadata_col_info and metadata_col_info.get("nullable", True):
            op.alter_column("rdm_records_metadata", "deletion_status", nullable=False)
            print("Changed deletion_status column in rdm_records_metadata to NOT NULL.")
        else:
            print(
                "Column deletion_status in rdm_records_metadata is already NOT NULL, skipping alter."
            )
    else:
        print(
            "Column deletion_status does not exist in rdm_records_metadata, skipping nullable constraint."
        )


def downgrade():
    """Downgrade database."""
    # Get database inspector to check if columns exist before dropping
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    # Check if tables exist before trying to modify them
    existing_tables = inspector.get_table_names()

    if "rdm_records_metadata_version" in existing_tables:
        metadata_version_columns = [
            col["name"] for col in inspector.get_columns("rdm_records_metadata_version")
        ]
        if "deletion_status" in metadata_version_columns:
            op.drop_column("rdm_records_metadata_version", "deletion_status")
            print("Dropped deletion_status column from rdm_records_metadata_version.")
        else:
            print(
                "Column deletion_status does not exist in rdm_records_metadata_version, skipping drop."
            )
    else:
        print(
            "Table rdm_records_metadata_version does not exist, skipping column drop."
        )

    if "rdm_records_metadata" in existing_tables:
        metadata_columns = [
            col["name"] for col in inspector.get_columns("rdm_records_metadata")
        ]
        if "deletion_status" in metadata_columns:
            op.drop_column("rdm_records_metadata", "deletion_status")
            print("Dropped deletion_status column from rdm_records_metadata.")
        else:
            print(
                "Column deletion_status does not exist in rdm_records_metadata, skipping drop."
            )
    else:
        print("Table rdm_records_metadata does not exist, skipping column drop.")
