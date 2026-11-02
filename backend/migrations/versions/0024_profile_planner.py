"""Private Women and Adult notes and timed tasks; preserve all existing records."""
from alembic import op
from core.models import ProfilePlanner
revision = '0024_profile_planner'
down_revision = '0023_merge_notes_women'
branch_labels = None
depends_on = None

def upgrade():
    ProfilePlanner.__table__.create(op.get_bind(), checkfirst=True)

def downgrade():
    raise RuntimeError('Planner data requires a reviewed data-preserving downgrade')
