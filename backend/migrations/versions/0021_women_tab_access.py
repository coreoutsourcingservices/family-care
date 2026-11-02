"""Women diary and recipient-specific timed tab permissions."""
from alembic import op
from core.models import WomenAccessGrant, WomenDiaryRecord
revision = '0021_women_tab_access'
down_revision = '0020_profile_doctor_grants'
branch_labels = None
depends_on = None


def upgrade():
    for model in (WomenAccessGrant, WomenDiaryRecord):
        model.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    raise RuntimeError('Women diary and consent history require a reviewed migration')
