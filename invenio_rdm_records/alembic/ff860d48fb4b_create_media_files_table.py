#
# This file is part of Invenio.
# Copyright (C) 2023-2024 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create media files table."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql, postgresql
from sqlalchemy_utils import JSONType, UUIDType

# revision identifiers, used by Alembic.
revision = "ff860d48fb4b"
down_revision = "cfcb8cb78708"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    # Get database inspector to check if tables and columns already exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()

    # Create rdm_drafts_media_files table if it doesn't exist
    drafts_media_table = "rdm_drafts_media_files"
    if drafts_media_table not in existing_tables:
        op.create_table(
            drafts_media_table,
            sa.Column(
                "created",
                sa.DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql"),
                nullable=False,
            ),
            sa.Column(
                "updated",
                sa.DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql"),
                nullable=False,
            ),
            sa.Column("id", UUIDType(), nullable=False),
            sa.Column(
                "json",
                sa.JSON()
                .with_variant(JSONType(), "mysql")
                .with_variant(
                    postgresql.JSONB(none_as_null=True, astext_type=sa.Text()),
                    "postgresql",
                )
                .with_variant(JSONType(), "sqlite"),
                nullable=True,
            ),
            sa.Column("version_id", sa.Integer(), nullable=False),
            sa.Column(
                "key",
                sa.Text().with_variant(mysql.VARCHAR(length=255), "mysql"),
                nullable=False,
            ),
            sa.Column("record_id", UUIDType(), nullable=False),
            sa.Column("object_version_id", UUIDType(), nullable=True),
            sa.ForeignKeyConstraint(
                ["object_version_id"],
                ["files_object.version_id"],
                name=op.f("fk_rdm_drafts_media_files_object_version_id_files_object"),
                ondelete="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["record_id"],
                ["rdm_drafts_metadata.id"],
                name=op.f("fk_rdm_drafts_media_files_record_id_rdm_drafts_metadata"),
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_rdm_drafts_media_files")),
        )
        print(f"Created table {drafts_media_table}.")

        # Create unique index for drafts media files
        op.create_index(
            "uidx_rdm_drafts_media_files_id_key",
            drafts_media_table,
            ["id", "key"],
            unique=True,
        )
        print(f"Created unique index for {drafts_media_table}.")
    else:
        print(f"Table {drafts_media_table} already exists, skipping creation.")

        # Check if index exists
        existing_indexes = [
            idx["name"] for idx in inspector.get_indexes(drafts_media_table)
        ]
        if "uidx_rdm_drafts_media_files_id_key" not in existing_indexes:
            op.create_index(
                "uidx_rdm_drafts_media_files_id_key",
                drafts_media_table,
                ["id", "key"],
                unique=True,
            )
            print(f"Created missing unique index for {drafts_media_table}.")

    # Create rdm_records_media_files table if it doesn't exist
    records_media_table = "rdm_records_media_files"
    if records_media_table not in existing_tables:
        op.create_table(
            records_media_table,
            sa.Column(
                "created",
                sa.DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql"),
                nullable=False,
            ),
            sa.Column(
                "updated",
                sa.DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql"),
                nullable=False,
            ),
            sa.Column("id", UUIDType(), nullable=False),
            sa.Column(
                "json",
                sa.JSON()
                .with_variant(JSONType(), "mysql")
                .with_variant(
                    postgresql.JSONB(none_as_null=True, astext_type=sa.Text()),
                    "postgresql",
                )
                .with_variant(JSONType(), "sqlite"),
                nullable=True,
            ),
            sa.Column("version_id", sa.Integer(), nullable=False),
            sa.Column(
                "key",
                sa.Text().with_variant(mysql.VARCHAR(length=255), "mysql"),
                nullable=False,
            ),
            sa.Column("record_id", UUIDType(), nullable=False),
            sa.Column("object_version_id", UUIDType(), nullable=True),
            sa.ForeignKeyConstraint(
                ["object_version_id"],
                ["files_object.version_id"],
                name=op.f("fk_rdm_records_media_files_object_version_id_files_object"),
                ondelete="RESTRICT",
            ),
            sa.ForeignKeyConstraint(
                ["record_id"],
                ["rdm_records_metadata.id"],
                name=op.f("fk_rdm_records_media_files_record_id_rdm_records_metadata"),
                ondelete="RESTRICT",
            ),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_rdm_records_media_files")),
        )
        print(f"Created table {records_media_table}.")

        # Create unique index for records media files
        op.create_index(
            "uidx_rdm_records_media_files_id_key",
            records_media_table,
            ["id", "key"],
            unique=True,
        )
        print(f"Created unique index for {records_media_table}.")
    else:
        print(f"Table {records_media_table} already exists, skipping creation.")

        # Check if index exists
        existing_indexes = [
            idx["name"] for idx in inspector.get_indexes(records_media_table)
        ]
        if "uidx_rdm_records_media_files_id_key" not in existing_indexes:
            op.create_index(
                "uidx_rdm_records_media_files_id_key",
                records_media_table,
                ["id", "key"],
                unique=True,
            )
            print(f"Created missing unique index for {records_media_table}.")

    # Add media_bucket_id column to rdm_drafts_metadata
    drafts_metadata_table = "rdm_drafts_metadata"
    if drafts_metadata_table in existing_tables:
        drafts_columns = [
            col["name"] for col in inspector.get_columns(drafts_metadata_table)
        ]
        if "media_bucket_id" not in drafts_columns:
            op.add_column(
                drafts_metadata_table,
                sa.Column("media_bucket_id", UUIDType(), nullable=True),
            )
            print(f"Added media_bucket_id column to {drafts_metadata_table}.")

            # Create foreign key
            op.create_foreign_key(
                op.f("fk_rdm_drafts_metadata_media_bucket_id_files_bucket"),
                drafts_metadata_table,
                "files_bucket",
                ["media_bucket_id"],
                ["id"],
            )
            print(
                f"Created foreign key for media_bucket_id in {drafts_metadata_table}."
            )
        else:
            print(f"Column media_bucket_id already exists in {drafts_metadata_table}.")
    else:
        print(
            f"Table {drafts_metadata_table} does not exist, skipping column addition."
        )

    # Add media_bucket_id column to rdm_records_metadata
    records_metadata_table = "rdm_records_metadata"
    if records_metadata_table in existing_tables:
        records_columns = [
            col["name"] for col in inspector.get_columns(records_metadata_table)
        ]
        if "media_bucket_id" not in records_columns:
            op.add_column(
                records_metadata_table,
                sa.Column("media_bucket_id", UUIDType(), nullable=True),
            )
            print(f"Added media_bucket_id column to {records_metadata_table}.")

            # Create foreign key
            op.create_foreign_key(
                op.f("fk_rdm_records_metadata_media_bucket_id_files_bucket"),
                records_metadata_table,
                "files_bucket",
                ["media_bucket_id"],
                ["id"],
            )
            print(
                f"Created foreign key for media_bucket_id in {records_metadata_table}."
            )
        else:
            print(f"Column media_bucket_id already exists in {records_metadata_table}.")
    else:
        print(
            f"Table {records_metadata_table} does not exist, skipping column addition."
        )

    # Add media_bucket_id column to rdm_records_metadata_version
    records_version_table = "rdm_records_metadata_version"
    if records_version_table in existing_tables:
        version_columns = [
            col["name"] for col in inspector.get_columns(records_version_table)
        ]
        if "media_bucket_id" not in version_columns:
            op.add_column(
                records_version_table,
                sa.Column(
                    "media_bucket_id",
                    UUIDType(),
                    autoincrement=False,
                    nullable=True,
                ),
            )
            print(f"Added media_bucket_id column to {records_version_table}.")
        else:
            print(f"Column media_bucket_id already exists in {records_version_table}.")
    else:
        print(
            f"Table {records_version_table} does not exist, skipping column addition."
        )


def downgrade():
    """Downgrade database."""
    # Get database inspector to check if tables and columns exist before dropping
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()

    # Drop media_bucket_id column from rdm_records_metadata_version
    records_version_table = "rdm_records_metadata_version"
    if records_version_table in existing_tables:
        version_columns = [
            col["name"] for col in inspector.get_columns(records_version_table)
        ]
        if "media_bucket_id" in version_columns:
            op.drop_column(records_version_table, "media_bucket_id")
            print(f"Dropped media_bucket_id column from {records_version_table}.")
        else:
            print(
                f"Column media_bucket_id does not exist in {records_version_table}, skipping drop."
            )
    else:
        print(f"Table {records_version_table} does not exist, skipping column drop.")

    # Drop foreign key and column from rdm_records_metadata
    records_metadata_table = "rdm_records_metadata"
    if records_metadata_table in existing_tables:
        records_columns = [
            col["name"] for col in inspector.get_columns(records_metadata_table)
        ]
        if "media_bucket_id" in records_columns:
            try:
                # Try to drop foreign key first
                op.drop_constraint(
                    op.f("fk_rdm_records_metadata_media_bucket_id_files_bucket"),
                    records_metadata_table,
                    type_="foreignkey",
                )
                print(f"Dropped foreign key from {records_metadata_table}.")
            except Exception as e:
                print(
                    f"Warning: Could not drop foreign key from {records_metadata_table}: {e}"
                )

            op.drop_column(records_metadata_table, "media_bucket_id")
            print(f"Dropped media_bucket_id column from {records_metadata_table}.")
        else:
            print(
                f"Column media_bucket_id does not exist in {records_metadata_table}, skipping drop."
            )
    else:
        print(f"Table {records_metadata_table} does not exist, skipping column drop.")

    # Drop foreign key and column from rdm_drafts_metadata
    drafts_metadata_table = "rdm_drafts_metadata"
    if drafts_metadata_table in existing_tables:
        drafts_columns = [
            col["name"] for col in inspector.get_columns(drafts_metadata_table)
        ]
        if "media_bucket_id" in drafts_columns:
            try:
                # Try to drop foreign key first
                op.drop_constraint(
                    op.f("fk_rdm_drafts_metadata_media_bucket_id_files_bucket"),
                    drafts_metadata_table,
                    type_="foreignkey",
                )
                print(f"Dropped foreign key from {drafts_metadata_table}.")
            except Exception as e:
                print(
                    f"Warning: Could not drop foreign key from {drafts_metadata_table}: {e}"
                )

            op.drop_column(drafts_metadata_table, "media_bucket_id")
            print(f"Dropped media_bucket_id column from {drafts_metadata_table}.")
        else:
            print(
                f"Column media_bucket_id does not exist in {drafts_metadata_table}, skipping drop."
            )
    else:
        print(f"Table {drafts_metadata_table} does not exist, skipping column drop.")

    # Drop rdm_records_media_files table
    records_media_table = "rdm_records_media_files"
    if records_media_table in existing_tables:
        # Drop index first
        existing_indexes = [
            idx["name"] for idx in inspector.get_indexes(records_media_table)
        ]
        if "uidx_rdm_records_media_files_id_key" in existing_indexes:
            op.drop_index(
                "uidx_rdm_records_media_files_id_key", table_name=records_media_table
            )
            print(f"Dropped unique index from {records_media_table}.")

        op.drop_table(records_media_table)
        print(f"Dropped table {records_media_table}.")
    else:
        print(f"Table {records_media_table} does not exist, skipping drop.")

    # Drop rdm_drafts_media_files table
    drafts_media_table = "rdm_drafts_media_files"
    if drafts_media_table in existing_tables:
        # Drop index first
        existing_indexes = [
            idx["name"] for idx in inspector.get_indexes(drafts_media_table)
        ]
        if "uidx_rdm_drafts_media_files_id_key" in existing_indexes:
            op.drop_index(
                "uidx_rdm_drafts_media_files_id_key", table_name=drafts_media_table
            )
            print(f"Dropped unique index from {drafts_media_table}.")

        op.drop_table(drafts_media_table)
        print(f"Dropped table {drafts_media_table}.")
    else:
        print(f"Table {drafts_media_table} does not exist, skipping drop.")
