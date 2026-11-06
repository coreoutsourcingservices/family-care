"""Women article categories and pregnancy timing."""
from alembic import op
import sqlalchemy as sa

revision = '0032_women_articles'
down_revision = '0031_health_articles'
branch_labels = None
depends_on = None


def upgrade():
    from core.models import WomenArticleVisibility
    # 0031 creates from current metadata on fresh installs.
    columns = {c['name'] for c in sa.inspect(op.get_bind()).get_columns('health_articles', schema='familycare')}
    for name, kind, nullable, default in [('category', sa.String(24), True, None),
                                        ('stage_month', sa.Integer(), True, None),
                                        ('time_label', sa.String(100), False, '')]:
        if name not in columns:
            op.add_column('health_articles', sa.Column(name, kind, nullable=nullable, server_default=default), schema='familycare')
    WomenArticleVisibility.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    raise RuntimeError('Article timing requires a reviewed migration')
