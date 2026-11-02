"""Opt-in pregnancy stage and sourced educational guidance."""
from alembic import op
from core.models import PregnancyCare
revision='0026_pregnancy_care'
down_revision='0025_health_sharing_consultation'
branch_labels=None
depends_on=None
def upgrade():PregnancyCare.__table__.create(op.get_bind(),checkfirst=True)
def downgrade():raise RuntimeError('Pregnancy care settings require a reviewed downgrade')
