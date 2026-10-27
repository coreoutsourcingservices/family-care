"""Compatibility marker for the existing optional care-profile extension.

The deployed database already records this revision and owns care_profiles and
care_reports, but their migration source is not part of this identity checkout.
This marker deliberately creates, alters and deletes nothing. It lets Alembic
preserve that external revision and upgrade identity features on top of it.
Fresh identity-only installations do not require those optional extension tables.
"""
revision = '0002_care_profiles'
down_revision = '0001_identity'
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    raise RuntimeError('The optional care extension is externally managed; preserve its schema.')
