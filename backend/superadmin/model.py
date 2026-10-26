from auth.model import profile

ROLE = 'super_admin'


def current_profile(user_id, token):
    return profile(user_id, token)


from common.supabase import supabase


def set_role(token, user_id, role):
    return supabase('POST', '/rest/v1/rpc/set_user_role', token,
                    json={'target_id': str(user_id), 'new_role': role})
