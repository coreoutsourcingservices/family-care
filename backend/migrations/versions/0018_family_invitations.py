"""Independent adult/women logins linked to the inviting family."""
from alembic import op
from core.models import FamilyInvitation

revision='0018_family_invitations'
down_revision='0017_realtime_notifications'
branch_labels=None
depends_on=None


def upgrade():
    FamilyInvitation.__table__.create(op.get_bind(),checkfirst=True)


def downgrade():
    raise RuntimeError('Family membership requires a reviewed data migration')
