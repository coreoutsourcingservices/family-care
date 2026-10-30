"""Guardian identity and reversible profile removal."""
from alembic import op
import sqlalchemy as sa
revision='0016_child_profile_controls'
down_revision='0015_adult_records'
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('care_reports',sa.Column('category',sa.String(32),nullable=False,server_default='Others'),schema='familycare')
    op.add_column('care_reports',sa.Column('category_reviewed',sa.Boolean(),nullable=False,server_default=sa.false()),schema='familycare')
    op.add_column('care_profiles',sa.Column('guardian_name',sa.String(120),nullable=False,server_default=''),schema='familycare')
    op.add_column('care_profiles',sa.Column('deleted_at',sa.DateTime()),schema='familycare')

def downgrade():
    raise RuntimeError('Profile history removal needs a reviewed migration')
