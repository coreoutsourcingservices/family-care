"""Admin-authored child and women's health articles."""
from alembic import op
from core.models import HealthArticle

revision = '0031_health_articles'
down_revision = '0030_clinical_workflows'
branch_labels = None
depends_on = None


def upgrade():
    HealthArticle.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    raise RuntimeError('Published health articles require a reviewed archival migration')
