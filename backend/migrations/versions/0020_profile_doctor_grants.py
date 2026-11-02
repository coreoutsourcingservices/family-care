"""Scoped, expiring doctor access for adult and women profiles."""
from alembic import op
from core.models import ProfileDoctorGrant
revision='0020_profile_doctor_grants'
down_revision='0019_child_growth_nutrition'
branch_labels=None
depends_on=None

def upgrade():
    ProfileDoctorGrant.__table__.create(op.get_bind(),checkfirst=True)

def downgrade():
    raise RuntimeError('Doctor consent history requires a reviewed migration')
