"""Retain deleted activity entries for 30 days."""
from alembic import op
import sqlalchemy as sa
revision='0029_activity_retention'
down_revision='0028_recycle_bin'
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('audit_logs',sa.Column('deleted_at',sa.DateTime(),nullable=True),schema='familycare')

def downgrade():
    raise RuntimeError('Activity retention requires a reviewed downgrade')
