from services.repository import find_user, user_by_id, serialize_user
from patient.model import ROLE


def by_email(email, lock=False):
    return find_user(email, ROLE, lock=lock)
