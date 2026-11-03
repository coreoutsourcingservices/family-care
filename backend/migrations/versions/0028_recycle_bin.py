"""Keep newly deleted user content recoverable for 30 days."""
from alembic import op
import sqlalchemy as sa
from core.models import RecycleItem

revision='0028_recycle_bin'
down_revision='0027_doctor_handoffs'
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('customer_notes',sa.Column('deleted_at',sa.DateTime(),nullable=True),schema='familycare')
    op.add_column('care_reports',sa.Column('deleted_at',sa.DateTime(),nullable=True),schema='familycare')
    RecycleItem.__table__.create(op.get_bind(),checkfirst=True)

def downgrade():
    raise RuntimeError('Recycle bin retention data requires a reviewed downgrade')
