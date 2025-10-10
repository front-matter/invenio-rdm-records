#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create files and media files versioning table."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql, postgresql
from sqlalchemy_utils import JSONType, UUIDType

# revision identifiers, used by Alembic.
revision = "a2a6819f14f1"
down_revision = "2186256e8d9b"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    # Get database inspector to check if tables and indexes already exist
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()

    # create version table for record files
    table_name = "rdm_records_files_version"
    if table_name not in existing_tables:
        op.create_table(
            table_name,
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
            sa.Column(
                "transaction_id", sa.BigInteger(), autoincrement=False, nullable=False
            ),
            sa.Column("end_transaction_id", sa.BigInteger(), nullable=True),
            sa.Column("operation_type", sa.SmallInteger(), nullable=False),
            sa.PrimaryKeyConstraint(
                "id", "transaction_id", name=op.f("pk_rdm_records_files_version")
            ),
        )
        print(f"Created table {table_name}.")

        # Create indexes for files version table
        op.create_index(
            "ix_rdm_records_files_version_end_transaction_id",
            table_name,
            ["end_transaction_id"],
            unique=False,
        )
        op.create_index(
            "ix_rdm_records_files_version_operation_type",
            table_name,
            ["operation_type"],
            unique=False,
        )
        op.create_index(
            "ix_rdm_records_files_version_transaction_id",
            table_name,
            ["transaction_id"],
            unique=False,
        )
        print(f"Created indexes for table {table_name}.")
    else:
        print(f"Table {table_name} already exists, skipping creation.")

        # Check and create missing indexes
        existing_indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]

        indexes_to_create = [
            ("ix_rdm_records_files_version_end_transaction_id", ["end_transaction_id"]),
            ("ix_rdm_records_files_version_operation_type", ["operation_type"]),
            ("ix_rdm_records_files_version_transaction_id", ["transaction_id"]),
        ]

        for index_name, columns in indexes_to_create:
            if index_name not in existing_indexes:
                op.create_index(index_name, table_name, columns, unique=False)
                print(f"Created missing index {index_name}.")
            else:
                print(f"Index {index_name} already exists, skipping creation.")

    # create version table for record media files
    media_table_name = "rdm_records_media_files_version"
    if media_table_name not in existing_tables:
        op.create_table(
            media_table_name,
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
            sa.Column(
                "transaction_id", sa.BigInteger(), autoincrement=False, nullable=False
            ),
            sa.Column("end_transaction_id", sa.BigInteger(), nullable=True),
            sa.Column("operation_type", sa.SmallInteger(), nullable=False),
            sa.PrimaryKeyConstraint(
                "id", "transaction_id", name=op.f("pk_rdm_records_media_files_version")
            ),
        )
        print(f"Created table {media_table_name}.")

        # Create indexes for media files version table
        op.create_index(
            "ix_rdm_records_media_files_version_end_transaction_id",
            media_table_name,
            ["end_transaction_id"],
            unique=False,
        )
        op.create_index(
            "ix_rdm_records_media_files_version_operation_type",
            media_table_name,
            ["operation_type"],
            unique=False,
        )
        op.create_index(
            "ix_rdm_records_media_files_version_transaction_id",
            media_table_name,
            ["transaction_id"],
            unique=False,
        )
        print(f"Created indexes for table {media_table_name}.")
    else:
        print(f"Table {media_table_name} already exists, skipping creation.")

        # Check and create missing indexes for media files table
        existing_media_indexes = [
            idx["name"] for idx in inspector.get_indexes(media_table_name)
        ]

        media_indexes_to_create = [
            (
                "ix_rdm_records_media_files_version_end_transaction_id",
                ["end_transaction_id"],
            ),
            ("ix_rdm_records_media_files_version_operation_type", ["operation_type"]),
            ("ix_rdm_records_media_files_version_transaction_id", ["transaction_id"]),
        ]

        for index_name, columns in media_indexes_to_create:
            if index_name not in existing_media_indexes:
                op.create_index(index_name, media_table_name, columns, unique=False)
                print(f"Created missing index {index_name}.")
            else:
                print(f"Index {index_name} already exists, skipping creation.")


def downgrade():
    """Downgrade database."""
    # Get database inspector to check if tables and indexes exist before dropping
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()

    # drop files version table and indices
    files_table_name = "rdm_records_files_version"
    if files_table_name in existing_tables:
        existing_indexes = [
            idx["name"] for idx in inspector.get_indexes(files_table_name)
        ]

        # Drop indexes if they exist
        files_indexes_to_drop = [
            "ix_rdm_records_files_version_end_transaction_id",
            "ix_rdm_records_files_version_operation_type",
            "ix_rdm_records_files_version_transaction_id",
        ]

        for index_name in files_indexes_to_drop:
            if index_name in existing_indexes:
                op.drop_index(index_name, table_name=files_table_name)
                print(f"Dropped index {index_name}.")
            else:
                print(f"Index {index_name} does not exist, skipping drop.")

        op.drop_table(files_table_name)
        print(f"Dropped table {files_table_name}.")
    else:
        print(f"Table {files_table_name} does not exist, skipping drop.")

    # drop media files version table and indices
    media_table_name = "rdm_records_media_files_version"
    if media_table_name in existing_tables:
        existing_media_indexes = [
            idx["name"] for idx in inspector.get_indexes(media_table_name)
        ]

        # Drop indexes if they exist
        media_indexes_to_drop = [
            "ix_rdm_records_media_files_version_end_transaction_id",
            "ix_rdm_records_media_files_version_operation_type",
            "ix_rdm_records_media_files_version_transaction_id",
        ]

        for index_name in media_indexes_to_drop:
            if index_name in existing_media_indexes:
                op.drop_index(index_name, table_name=media_table_name)
                print(f"Dropped index {index_name}.")
            else:
                print(f"Index {index_name} does not exist, skipping drop.")

        op.drop_table(media_table_name)
        print(f"Dropped table {media_table_name}.")
    else:
        print(f"Table {media_table_name} does not exist, skipping drop.")
