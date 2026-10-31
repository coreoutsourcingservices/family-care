"""Per-child doctor control of age-based educational guidance."""
from alembic import op
from core.models import ChildGrowthNutritionSetting
revision='0019_child_growth_nutrition'
down_revision='0018_family_invitations'
branch_labels=None
depends_on=None

def upgrade():
    ChildGrowthNutritionSetting.__table__.create(op.get_bind(),checkfirst=True)

def downgrade():
    raise RuntimeError('Guidance visibility history requires a reviewed migration')
