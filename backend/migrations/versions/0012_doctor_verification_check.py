"""Persist admin-triggered doctor verification evidence."""
from alembic import op
import sqlalchemy as sa

revision = '0012_doctor_verification_check'
down_revision = '0011_doctor_onboarding'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('doctor_profiles', sa.Column('verification_check', sa.JSON()), schema='familycare')


def downgrade():
    raise RuntimeError('Verification evidence downgrade requires a reviewed data migration')
