"""Create local signing secrets without printing or committing credentials."""
import secrets
from pathlib import Path
from dotenv import dotenv_values

root = Path(__file__).resolve().parents[1]
target = root / '.env'
values = dict(dotenv_values(target)) if target.exists() else {}
defaults = dotenv_values(root / '.env.example')
for key, value in defaults.items():
    values.setdefault(key, value or '')
for key in ('JWT_SECRET_KEY', 'OTP_HMAC_SECRET'):
    if len(values.get(key) or '') < 32:
        values[key] = secrets.token_urlsafe(48)
# Remove retired credentials from the active configuration. Existing Supabase data is untouched.
for key in ('JWT', 'SUPABASE_ANON_KEY', 'SUPABASE_URL'):
    values.pop(key, None)
target.write_text(''.join(f'{key}="{str(value or "").replace(chr(34), chr(92)+chr(34))}"\n'
                          for key, value in values.items()), encoding='utf-8')
print('Local .env configured. Signing secrets generated/preserved; no values displayed.')
print('Database URL:', 'configured' if values.get('DATABASE_URL') else 'required')
print('SMTP:', 'configured' if values.get('SMTP_HOST') else 'required for OTP delivery')
