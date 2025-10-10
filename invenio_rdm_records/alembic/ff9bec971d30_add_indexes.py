#
# This file is part of Invenio.
# Copyright (C) 2023-2024 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Add indexes."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ff9bec971d30"
down_revision = "faf0cefa79a0"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    # Get database inspector to check if indexes already exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()

    # Define all indexes to create with their table names
    indexes_to_create = [
        ("ix_rdm_drafts_metadata_bucket_id", "rdm_drafts_metadata", ["bucket_id"]),
        (
            "ix_rdm_drafts_metadata_media_bucket_id",
            "rdm_drafts_metadata",
            ["media_bucket_id"],
        ),
        ("ix_rdm_records_metadata_bucket_id", "rdm_records_metadata", ["bucket_id"]),
        (
            "ix_rdm_records_metadata_media_bucket_id",
            "rdm_records_metadata",
            ["media_bucket_id"],
        ),
        (
            "ix_rdm_records_metadata_version_bucket_id",
            "rdm_records_metadata_version",
            ["bucket_id"],
        ),
        (
            "ix_rdm_records_metadata_version_media_bucket_id",
            "rdm_records_metadata_version",
            ["media_bucket_id"],
        ),
        (
            "ix_rdm_drafts_files_object_version_id",
            "rdm_drafts_files",
            ["object_version_id"],
        ),
        (
            "ix_rdm_drafts_media_files_object_version_id",
            "rdm_drafts_media_files",
            ["object_version_id"],
        ),
        (
            "ix_rdm_records_files_object_version_id",
            "rdm_records_files",
            ["object_version_id"],
        ),
        (
            "ix_rdm_records_files_version_object_version_id",
            "rdm_records_files_version",
            ["object_version_id"],
        ),
        (
            "ix_rdm_records_media_files_object_version_id",
            "rdm_records_media_files",
            ["object_version_id"],
        ),
        (
            "ix_rdm_records_media_files_version_object_version_id",
            "rdm_records_media_files_version",
            ["object_version_id"],
        ),
    ]

    created_indexes = 0
    skipped_indexes = 0

    for index_name, table_name, columns in indexes_to_create:
        # Check if table exists
        if table_name not in existing_tables:
            print(f"Table {table_name} does not exist, skipping index {index_name}.")
            skipped_indexes += 1
            continue

        # Check if index already exists
        existing_indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]

        if index_name not in existing_indexes:
            try:
                op.create_index(
                    op.f(index_name),
                    table_name,
                    columns,
                    unique=False,
                )
                print(f"Created index {index_name} on table {table_name}.")
                created_indexes += 1
            except Exception as e:
                print(
                    f"Warning: Could not create index {index_name} on table {table_name}: {e}"
                )
                skipped_indexes += 1
        else:
            print(
                f"Index {index_name} already exists on table {table_name}, skipping creation."
            )
            skipped_indexes += 1

    print(
        f"Index creation summary: {created_indexes} created, {skipped_indexes} skipped."
    )


def downgrade():
    """Downgrade database."""
    # Get database inspector to check if indexes exist before dropping
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()

    # Define all indexes to drop with their table names (in reverse order of creation)
    indexes_to_drop = [
        (
            "ix_rdm_records_media_files_version_object_version_id",
            "rdm_records_media_files_version",
        ),
        ("ix_rdm_records_media_files_object_version_id", "rdm_records_media_files"),
        ("ix_rdm_records_files_version_object_version_id", "rdm_records_files_version"),
        ("ix_rdm_records_files_object_version_id", "rdm_records_files"),
        ("ix_rdm_drafts_media_files_object_version_id", "rdm_drafts_media_files"),
        ("ix_rdm_drafts_files_object_version_id", "rdm_drafts_files"),
        (
            "ix_rdm_records_metadata_version_media_bucket_id",
            "rdm_records_metadata_version",
        ),
        ("ix_rdm_records_metadata_version_bucket_id", "rdm_records_metadata_version"),
        ("ix_rdm_records_metadata_media_bucket_id", "rdm_records_metadata"),
        ("ix_rdm_records_metadata_bucket_id", "rdm_records_metadata"),
        ("ix_rdm_drafts_metadata_media_bucket_id", "rdm_drafts_metadata"),
        ("ix_rdm_drafts_metadata_bucket_id", "rdm_drafts_metadata"),
    ]

    dropped_indexes = 0
    skipped_indexes = 0

    for index_name, table_name in indexes_to_drop:
        # Check if table exists
        if table_name not in existing_tables:
            print(
                f"Table {table_name} does not exist, skipping index {index_name} drop."
            )
            skipped_indexes += 1
            continue

        # Check if index exists before dropping
        existing_indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]

        if index_name in existing_indexes:
            try:
                op.drop_index(op.f(index_name), table_name=table_name)
                print(f"Dropped index {index_name} from table {table_name}.")
                dropped_indexes += 1
            except Exception as e:
                print(
                    f"Warning: Could not drop index {index_name} from table {table_name}: {e}"
                )
                skipped_indexes += 1
        else:
            print(
                f"Index {index_name} does not exist on table {table_name}, skipping drop."
            )
            skipped_indexes += 1

    print(
        f"Index removal summary: {dropped_indexes} dropped, {skipped_indexes} skipped."
    )
