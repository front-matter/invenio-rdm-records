# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2021 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create parent record table."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql, postgresql
from sqlalchemy_utils import JSONType, UUIDType

# revision identifiers, used by Alembic.
revision = "88d1463de5c0"
down_revision = "4a15e8671f4d"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    # Check which tables and columns already exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # Create parent metadata table if it doesn't exist
    if "rdm_parents_metadata" not in existing_tables:
        op.create_table(
            "rdm_parents_metadata",
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
            sa.Column(
                "id",
                UUIDType(),
                nullable=False,
            ),
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
            sa.Column(
                "version_id",
                sa.Integer(),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint(
                "id",
                name=op.f("pk_rdm_parents_metadata"),
            ),
        )
    else:
        print("Table 'rdm_parents_metadata' already exists, skipping creation.")

    # Add columns to drafts table if they don't exist
    if "rdm_drafts_metadata" in existing_tables:
        drafts_columns = [
            c["name"] for c in inspector.get_columns("rdm_drafts_metadata")
        ]

        if "parent_id" not in drafts_columns:
            op.add_column(
                "rdm_drafts_metadata", sa.Column("parent_id", UUIDType(), nullable=True)
            )
            if "rdm_parents_metadata" in existing_tables:
                op.create_foreign_key(
                    op.f("fk_rdm_drafts_metadata_parent_id_rdm_parents_metadata"),
                    "rdm_drafts_metadata",
                    "rdm_parents_metadata",
                    ["parent_id"],
                    ["id"],
                    ondelete="RESTRICT",
                )

        if "index" not in drafts_columns:
            op.add_column(
                "rdm_drafts_metadata", sa.Column("index", sa.Integer, nullable=True)
            )

    # Add columns to records table if they don't exist
    if "rdm_records_metadata" in existing_tables:
        records_columns = [
            c["name"] for c in inspector.get_columns("rdm_records_metadata")
        ]

        if "parent_id" not in records_columns:
            op.add_column(
                "rdm_records_metadata",
                sa.Column("parent_id", UUIDType(), nullable=True),
            )
            if "rdm_parents_metadata" in existing_tables:
                op.create_foreign_key(
                    op.f("fk_rdm_records_metadata_parent_id_rdm_parents_metadata"),
                    "rdm_records_metadata",
                    "rdm_parents_metadata",
                    ["parent_id"],
                    ["id"],
                    ondelete="RESTRICT",
                )

        if "index" not in records_columns:
            op.add_column(
                "rdm_records_metadata", sa.Column("index", sa.Integer, nullable=True)
            )

    # Add columns to records version table if they don't exist
    if "rdm_records_metadata_version" in existing_tables:
        version_columns = [
            c["name"] for c in inspector.get_columns("rdm_records_metadata_version")
        ]

        if "parent_id" not in version_columns:
            op.add_column(
                "rdm_records_metadata_version",
                sa.Column("parent_id", UUIDType(), nullable=True),
            )

        if "index" not in version_columns:
            op.add_column(
                "rdm_records_metadata_version",
                sa.Column("index", sa.Integer, nullable=True),
            )

    # Create versions state table if it doesn't exist
    if "rdm_versions_state" not in existing_tables:
        op.create_table(
            "rdm_versions_state",
            sa.Column("latest_index", sa.Integer(), nullable=True),
            sa.Column("parent_id", UUIDType(), nullable=False),
            sa.Column("latest_id", UUIDType(), nullable=True),
            sa.Column("next_draft_id", UUIDType(), nullable=True),
            sa.ForeignKeyConstraint(
                ["latest_id"],
                ["rdm_records_metadata.id"],
                name=op.f("fk_rdm_versions_state_latest_id_rdm_records_metadata"),
            ),
            sa.ForeignKeyConstraint(
                ["next_draft_id"],
                ["rdm_drafts_metadata.id"],
                name=op.f("fk_rdm_versions_state_next_draft_id_rdm_drafts_metadata"),
            ),
            sa.ForeignKeyConstraint(
                ["parent_id"],
                ["rdm_parents_metadata.id"],
                name=op.f("fk_rdm_versions_state_parent_id_rdm_parents_metadata"),
                ondelete="CASCADE",
            ),
            sa.PrimaryKeyConstraint("parent_id", name=op.f("pk_rdm_versions_state")),
        )
    else:
        print("Table 'rdm_versions_state' already exists, skipping creation.")


def downgrade():
    """Downgrade database."""
    # Check which tables and columns exist before dropping/removing
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # Drop versions state table if it exists
    if "rdm_versions_state" in existing_tables:
        op.drop_table("rdm_versions_state")
    else:
        print("Table 'rdm_versions_state' does not exist, skipping drop.")

    # Remove columns from records version table if they exist
    if "rdm_records_metadata_version" in existing_tables:
        version_columns = [
            c["name"] for c in inspector.get_columns("rdm_records_metadata_version")
        ]

        if "parent_id" in version_columns:
            op.drop_column("rdm_records_metadata_version", "parent_id")
        if "index" in version_columns:
            op.drop_column("rdm_records_metadata_version", "index")

    # Remove columns from records table if they exist
    if "rdm_records_metadata" in existing_tables:
        records_columns = [
            c["name"] for c in inspector.get_columns("rdm_records_metadata")
        ]

        if "parent_id" in records_columns:
            try:
                op.drop_constraint(
                    op.f("fk_rdm_records_metadata_parent_id_rdm_parents_metadata"),
                    "rdm_records_metadata",
                    type_="foreignkey",
                )
            except Exception:
                pass  # Constraint might not exist
            op.drop_column("rdm_records_metadata", "parent_id")
        if "index" in records_columns:
            op.drop_column("rdm_records_metadata", "index")

    # Remove columns from drafts table if they exist
    if "rdm_drafts_metadata" in existing_tables:
        drafts_columns = [
            c["name"] for c in inspector.get_columns("rdm_drafts_metadata")
        ]

        if "parent_id" in drafts_columns:
            try:
                op.drop_constraint(
                    op.f("fk_rdm_drafts_metadata_parent_id_rdm_parents_metadata"),
                    "rdm_drafts_metadata",
                    type_="foreignkey",
                )
            except Exception:
                pass  # Constraint might not exist
            op.drop_column("rdm_drafts_metadata", "parent_id")
        if "index" in drafts_columns:
            op.drop_column("rdm_drafts_metadata", "index")

    # Drop parent metadata table if it exists
    if "rdm_parents_metadata" in existing_tables:
        op.drop_table("rdm_parents_metadata")
    else:
        print("Table 'rdm_parents_metadata' does not exist, skipping drop.")
