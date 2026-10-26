from common.supabase import supabase as call


def profile(user_id, token):
    rows = call('GET', '/rest/v1/profiles', token,
                params={'id': f'eq.{user_id}', 'select': 'id,full_name,role'})
    return rows[0] if rows else None
