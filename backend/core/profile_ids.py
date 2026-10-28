"""Allocate independent, transaction-safe public IDs for care profiles."""
from sqlalchemy import text

PREFIXES = {'child': 'CH', 'adult': 'AD', 'women': 'WO'}


def allocate_profile_public_id(context):
    module = context.get_current_parameters()['module']
    prefix = PREFIXES[module]
    schema = 'familycare.' if context.dialect.name == 'postgresql' else ''
    number = context.connection.execute(text(
        f'INSERT INTO {schema}care_profile_id_counters (module, value) VALUES (:module, 1) '
        'ON CONFLICT (module) DO UPDATE SET value = care_profile_id_counters.value + 1 '
        'RETURNING value'), {'module': module}).scalar_one()
    return f'{prefix}{number:06d}'
