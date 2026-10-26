from auth.model import profile

ROLE = 'doctor'


def current_profile(user_id, token):
    return profile(user_id, token)
