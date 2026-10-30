"""Create one persistent VAPID keypair locally. Never print the private key."""
import base64
from email.utils import parseaddr
from pathlib import Path
from dotenv import dotenv_values, set_key
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

root = Path(__file__).resolve().parents[1]
env = root / '.env'
values = dotenv_values(env)
if all(values.get(key) for key in ('PUSH_VAPID_PUBLIC_KEY', 'PUSH_VAPID_PRIVATE_KEY', 'PUSH_VAPID_SUBJECT')):
    print('Web Push is already configured; existing signing keys preserved.')
else:
    path = root / '.webpush-private.pem'
    if path.exists():
        private = serialization.load_pem_private_key(path.read_bytes(), password=None)
    else:
        private = ec.generate_private_key(ec.SECP256R1())
        path.write_bytes(private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    public = private.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    subject = values.get('PUSH_VAPID_SUBJECT') or ('mailto:' + parseaddr(values.get('SMTP_FROM', ''))[1])
    if subject == 'mailto:':
        raise RuntimeError('Set PUSH_VAPID_SUBJECT to your support mailto: address before configuring push.')
    set_key(str(env), 'PUSH_VAPID_PUBLIC_KEY', base64.urlsafe_b64encode(public).rstrip(b'=').decode())
    set_key(str(env), 'PUSH_VAPID_PRIVATE_KEY', str(path).replace('\\', '/'))
    set_key(str(env), 'PUSH_VAPID_SUBJECT', subject)
    print('Web Push configured. Signing key stays in an ignored local file.')
