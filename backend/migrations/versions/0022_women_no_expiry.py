"""Allow explicit non-expiring Women access grants."""
from alembic import op
import sqlalchemy as sa
revision = '0022_women_no_expiry'
down_revision = '0021_women_tab_access'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('women_access_grants', 'expires_at', schema='familycare',
                    existing_type=sa.DateTime(), nullable=True)


def downgrade():
    raise RuntimeError('Revoke or expire unlimited grants before a reviewed downgrade')
