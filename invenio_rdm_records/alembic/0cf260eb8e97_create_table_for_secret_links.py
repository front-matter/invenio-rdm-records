#
# This file is part of Invenio.
# Copyright (C) 2021 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create table for secret links."""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op

# revision identifiers, used by Alembic.
revision = "0cf260eb8e97"
down_revision = "4a15e8671f4d"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    # Check if table already exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "rdm_records_secret_links" not in inspector.get_table_names():
        op.create_table(
            "rdm_records_secret_links",
            sa.Column("id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
            sa.Column("token", sa.Text, nullable=False),
            sa.Column("created", sa.DateTime(), nullable=False),
            sa.Column("expires_at", sa.DateTime(), nullable=True),
            sa.Column("permission_level", sa.String(), nullable=False),
            sa.PrimaryKeyConstraint("id", name=op.f("pk_rdm_records_secret_links")),
        )
        op.create_index(
            op.f("ix_rdm_records_secret_links_created"),
            "rdm_records_secret_links",
            ["created"],
            unique=False,
        )
    else:
        print("Table 'rdm_records_secret_links' already exists, skipping creation.")


def downgrade():
    """Downgrade database."""
    # Check if table exists before dropping
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "rdm_records_secret_links" in inspector.get_table_names():
        try:
            op.drop_index(
                op.f("ix_rdm_records_secret_links_created"),
                table_name="rdm_records_secret_links",
            )
        except Exception:
            pass  # Index might not exist
        op.drop_table("rdm_records_secret_links")
    else:
        print("Table 'rdm_records_secret_links' does not exist, skipping drop.")
