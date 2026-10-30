"""Private doctor profile and degree image metadata."""
from alembic import op
import sqlalchemy as sa

revision = '0013_doctor_onboarding_images'
down_revision = '0012_doctor_verification_check'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('doctor_profiles', sa.Column('onboarding_images', sa.JSON()), schema='familycare')


def downgrade():
    raise RuntimeError('Image metadata removal requires a reviewed asset cleanup')
