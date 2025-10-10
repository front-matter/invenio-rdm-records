#
# This file is part of Invenio.
# Copyright (C) 2021 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Migrate secret links permission levels."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8ed1a438601c"
down_revision = "0cf260eb8e97"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    # Check if table exists before updating
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "rdm_records_secret_links" in inspector.get_table_names():
        # The permission level "read" and "read_files" where renamed to "view"
        op.execute(
            "UPDATE rdm_records_secret_links"
            " SET permission_level='view'"
            " WHERE permission_level='read' or permission_level='read_files'"
        )
    else:
        print("Table 'rdm_records_secret_links' does not exist, skipping migration.")


def downgrade():
    """Downgrade database."""
    # Check if table exists before updating
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "rdm_records_secret_links" in inspector.get_table_names():
        # Reverse the permission level changes
        op.execute(
            "UPDATE rdm_records_secret_links"
            " SET permission_level='read'"
            " WHERE permission_level='view'"
        )
    else:
        print("Table 'rdm_records_secret_links' does not exist, skipping downgrade.")
