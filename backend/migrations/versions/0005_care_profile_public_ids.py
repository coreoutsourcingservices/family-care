"""Add stable CH/AD/WO care-profile IDs without changing UUID relationships."""
from alembic import op
import sqlalchemy as sa

revision = '0005_profile_public_ids'
down_revision = '0004_members_cloudinary'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('LOCK TABLE familycare.care_profiles IN EXCLUSIVE MODE')
    op.create_table('care_profile_id_counters',
                    sa.Column('module', sa.String(10), primary_key=True),
                    sa.Column('value', sa.Integer(), nullable=False),
                    sa.CheckConstraint('value >= 1', name='ck_profile_counter_positive'),
                    schema='familycare')
    op.add_column('care_profiles', sa.Column('public_id', sa.String(32)), schema='familycare')
    op.execute("""
        WITH numbered AS (
            SELECT id, module,
                   row_number() OVER (PARTITION BY module ORDER BY created_at, id) AS number
            FROM familycare.care_profiles
        )
        UPDATE familycare.care_profiles AS p
        SET public_id = (CASE n.module WHEN 'child' THEN 'CH' WHEN 'adult' THEN 'AD' ELSE 'WO' END)
                        || lpad(n.number::text, greatest(6, length(n.number::text)), '0')
        FROM numbered AS n WHERE p.id = n.id
    """)
    op.execute("""INSERT INTO familycare.care_profile_id_counters (module, value)
                  SELECT module, count(*) FROM familycare.care_profiles GROUP BY module""")
    op.alter_column('care_profiles', 'public_id', nullable=False, schema='familycare')
    op.create_unique_constraint('uq_care_profiles_public_id', 'care_profiles', ['public_id'], schema='familycare')
    op.create_check_constraint('ck_care_profiles_public_id_format', 'care_profiles',
        "(module = 'child' AND public_id ~ '^CH[0-9]{6,}$') OR "
        "(module = 'adult' AND public_id ~ '^AD[0-9]{6,}$') OR "
        "(module = 'women' AND public_id ~ '^WO[0-9]{6,}$')", schema='familycare')
    # Also supports inserts from an older worker during a rolling restart.
    op.execute("""
        CREATE FUNCTION familycare.assign_care_profile_public_id() RETURNS trigger
        LANGUAGE plpgsql AS $$
        DECLARE n integer; prefix text;
        BEGIN
            IF TG_OP = 'UPDATE' THEN
                IF NEW.public_id IS DISTINCT FROM OLD.public_id OR NEW.module IS DISTINCT FROM OLD.module THEN
                    RAISE EXCEPTION 'Care-profile public ID and module are immutable';
                END IF;
                RETURN NEW;
            END IF;
            IF NEW.public_id IS NULL THEN
                INSERT INTO familycare.care_profile_id_counters(module, value) VALUES (NEW.module, 1)
                ON CONFLICT (module) DO UPDATE SET value = care_profile_id_counters.value + 1
                RETURNING value INTO n;
                prefix := CASE NEW.module WHEN 'child' THEN 'CH' WHEN 'adult' THEN 'AD' WHEN 'women' THEN 'WO' END;
                NEW.public_id := prefix || lpad(n::text, greatest(6, length(n::text)), '0');
            END IF;
            RETURN NEW;
        END;
        $$;
        CREATE TRIGGER care_profile_public_id_insert BEFORE INSERT ON familycare.care_profiles
        FOR EACH ROW EXECUTE FUNCTION familycare.assign_care_profile_public_id();
        CREATE TRIGGER care_profile_public_id_immutable BEFORE UPDATE ON familycare.care_profiles
        FOR EACH ROW EXECUTE FUNCTION familycare.assign_care_profile_public_id();
    """)


def downgrade():
    op.execute('DROP TRIGGER care_profile_public_id_immutable ON familycare.care_profiles')
    op.execute('DROP TRIGGER care_profile_public_id_insert ON familycare.care_profiles')
    op.execute('DROP FUNCTION familycare.assign_care_profile_public_id()')
    op.drop_constraint('ck_care_profiles_public_id_format', 'care_profiles', schema='familycare')
    op.drop_constraint('uq_care_profiles_public_id', 'care_profiles', schema='familycare')
    op.drop_column('care_profiles', 'public_id', schema='familycare')
    op.drop_table('care_profile_id_counters', schema='familycare')
