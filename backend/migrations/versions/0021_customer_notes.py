"""Private main-customer notes."""
from alembic import op
from core.models import CustomerNote
from sqlalchemy import Column, String, inspect
revision='0021_customer_notes'
down_revision='0020_profile_doctor_grants'
branch_labels=None
depends_on=None


def upgrade():
    CustomerNote.__table__.create(op.get_bind(),checkfirst=True)
    if 'gender' not in {col['name'] for col in inspect(op.get_bind()).get_columns('care_profiles',schema='familycare')}:
        op.add_column('care_profiles',Column('gender',String(16),nullable=False,server_default=''),schema='familycare')


def downgrade():
    raise RuntimeError('Customer notes require a reviewed data-preserving downgrade')
