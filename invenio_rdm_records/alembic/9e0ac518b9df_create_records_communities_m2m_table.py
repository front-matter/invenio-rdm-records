# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Create records/communities M2M table."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils import UUIDType

# revision identifiers, used by Alembic.
revision = "9e0ac518b9df"
down_revision = ("8ed1a438601c", "88d1463de5c0")
branch_labels = ()
depends_on = ("de9c14cbb0b2", "a14fa442680f")


def upgrade():
    """Upgrade database."""
    # Check if table already exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "rdm_parents_community" not in inspector.get_table_names():
        op.create_table(
            "rdm_parents_community",
            sa.Column("community_id", UUIDType(), nullable=False),
            sa.Column("record_id", UUIDType(), nullable=False),
            sa.Column("request_id", UUIDType(), nullable=True),
            sa.ForeignKeyConstraint(
                ["community_id"],
                ["communities_metadata.id"],
                name=op.f("fk_rdm_parents_community_community_id_communities_metadata"),
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["record_id"],
                ["rdm_parents_metadata.id"],
                name=op.f("fk_rdm_parents_community_record_id_rdm_parents_metadata"),
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["request_id"],
                ["request_metadata.id"],
                name=op.f("fk_rdm_parents_community_request_id_request_metadata"),
                ondelete="SET NULL",
            ),
            sa.PrimaryKeyConstraint(
                "community_id", "record_id", name=op.f("pk_rdm_parents_community")
            ),
        )
    else:
        print("Table 'rdm_parents_community' already exists, skipping creation.")


def downgrade():
    """Downgrade database."""
    # Check if table exists before dropping
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "rdm_parents_community" in inspector.get_table_names():
        op.drop_table("rdm_parents_community")
    else:
        print("Table 'rdm_parents_community' does not exist, skipping drop.")
