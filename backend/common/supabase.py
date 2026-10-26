import os
import requests

class UpstreamError(Exception):
    def __init__(self, status):
        self.status = status



def supabase(method, path, token=None, **kwargs):
    url = os.getenv('SUPABASE_URL', '').rstrip('/')
    key = os.getenv('SUPABASE_ANON_KEY', '')
    if not url or not key or 'your-project' in url:
        raise UpstreamError(503)
    headers = {'apikey': key, 'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    response = requests.request(method, url + path, headers=headers, timeout=15, **kwargs)
    if not response.ok:
        raise UpstreamError(response.status_code)
    return response.json() if response.content else {}

