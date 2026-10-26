from auth.model import profile

ROLE = 'admin'


def current_profile(user_id, token):
    return profile(user_id, token)


from common.supabase import supabase


def list_users(token, offset):
    return supabase('GET', '/rest/v1/profiles', token,
                    params={'select': 'id,full_name,role,created_at',
                            'order': 'created_at.asc,id.asc', 'limit': 100, 'offset': offset})
