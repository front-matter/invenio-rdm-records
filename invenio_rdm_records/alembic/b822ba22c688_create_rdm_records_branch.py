# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2021 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create RDM-Records branch."""

# revision identifiers, used by Alembic.
revision = "b822ba22c688"
down_revision = None
branch_labels = ("invenio_rdm_records",)
depends_on = "dbdbc1b19cf2"


def upgrade():
    """Upgrade database."""
    # This migration creates the RDM-Records branch in Alembic.
    # It doesn't perform any actual database schema changes.
    # The branch creation is handled by Alembic's metadata system.
    print("Creating invenio_rdm_records Alembic branch.")
    print(
        "This migration establishes the migration branch for RDM Records functionality."
    )
    print("No database schema changes are performed in this migration.")
    pass


def downgrade():
    """Downgrade database."""
    # Branch creation cannot be undone through a downgrade migration.
    # The branch structure is part of Alembic's version history system.
    print("Downgrading invenio_rdm_records branch creation.")
    print("Note: Branch creation is part of Alembic's version history.")
    print("This downgrade does not remove the branch structure itself.")
    print("No database schema changes are reverted in this migration.")
    pass
