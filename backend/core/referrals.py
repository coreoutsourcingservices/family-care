"""Stable referral identifiers derived from a doctor's name and existing public ID."""
import re
import unicodedata


def make_referral_id(full_name, public_id):
    name = re.sub(r'^(?:dr|doctor)\b[.\s]*', '', full_name.strip(), flags=re.IGNORECASE)
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    slug = re.sub(r'[^a-z0-9]', '', name.lower())[:120] or 'doctor'
    return slug + public_id
