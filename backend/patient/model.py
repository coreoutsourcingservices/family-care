from auth.model import profile

ROLE = 'patient'


def current_profile(user_id, token):
    return profile(user_id, token)
