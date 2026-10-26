from functools import wraps
from flask import request
from core.extensions import limiter
from core.security import protected, digest


def account_key():
    data = request.get_json(silent=True)
    data = data if isinstance(data, dict) else {}
    return 'account:' + digest(str(data.get('email') or data.get('username') or request.remote_addr).lower().strip())


def route(bp, path, handler, method='GET', roles=None, schema=None, limited=False):
    @wraps(handler)
    def view(**kwargs):
        return handler(**kwargs)
    if roles:
        view = protected(*roles)(view)
    if limited:
        view = limiter.limit('10 per minute', key_func=account_key)(view)
        view = limiter.limit('30 per minute')(view)
    view.api_meta = {'roles': roles, 'schema': schema, 'limited': limited}
    bp.add_url_rule(path, view_func=view, methods=[method])
