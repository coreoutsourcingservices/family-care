from pathlib import Path
from alembic import op

revision = '0001_identity'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    sql = (Path(__file__).resolve().parents[2] / 'supabase' / '0001_identity.sql').read_text(encoding='utf-8')
    # The same SQL artifact is used by SQL Editor and Alembic.
    if op.get_context().as_sql:
        op.execute(sql)
    else:
        cursor = op.get_bind().connection.driver_connection.cursor()
        cursor.execute(sql, prepare=False)
        cursor.close()


def downgrade():
    raise RuntimeError('Identity data downgrade is destructive. Restore a reviewed backup instead.')
