from unittest.mock import patch
from services.localization import STATES, locate


def test_all_states_and_deduplicated_choices(client):
    items = client.get('/api/v1/localization/states').json['items']
    assert len(items) == 36
    assert sum(x['type'] == 'state' for x in items) == 28
    for item in items:
        codes = [x['code'] for x in item['languages']]
        assert 3 <= len(codes) <= 5
        assert len(codes) == len(set(codes))
        assert 'hi' in codes and 'en' in codes


def test_other_languages_is_complete_without_changing_recommendations(client):
    from services.localization import LANGUAGES
    before = client.get('/api/v1/localization?state=Maharashtra').json
    result = client.get('/api/v1/localization/languages')
    assert result.status_code == 200
    data = result.json
    assert data['total'] == len(LANGUAGES)
    assert {item['code'] for item in data['items']} == set(LANGUAGES)
    assert [item['name'] for item in data['items']] == sorted(LANGUAGES.values(), key=str.casefold)
    assert 'fr' in {item['code'] for item in data['items']}
    assert client.get('/api/v1/localization?state=Maharashtra').json == before
    assert [item['code'] for item in before['languages']] == ['mr', 'hi', 'en']


def test_private_ip_never_looks_up_server_ip(client):
    with patch('services.localization.locate') as lookup:
        result = client.get('/api/v1/localization').json
    lookup.assert_not_called()
    assert result['location']['status'] == 'private_ip'
    assert result['recommended_language'] == 'en'


def test_state_preview_and_invalid_state(client):
    result = client.get('/api/v1/localization?state=Maharashtra').json
    assert [x['code'] for x in result['languages']] == ['mr', 'hi', 'en']
    assert result['location']['status'] == 'manual'
    assert client.get('/api/v1/localization?state=unknown').status_code == 400
    assert client.get('/api/v1/localization?state=Orissa').json['location']['state'] == 'Odisha'


def test_public_ip_and_failure_fallback(client):
    with patch('services.localization.locate', return_value={'success': True, 'country_code': 'IN', 'region': 'Tamil Nadu'}) as lookup:
        result = client.get('/api/v1/localization', environ_overrides={'REMOTE_ADDR': '8.8.8.8'}).json
        assert result['recommended_language'] == 'ta'
        assert lookup.call_args.args[0] == '8.8.8.8'
    with patch('services.localization.locate', side_effect=TimeoutError):
        assert client.get('/api/v1/localization', environ_overrides={'REMOTE_ADDR': '8.8.8.8'}).json['location']['status'] == 'lookup_unavailable'


def test_untrusted_forwarding_ignored_and_trusted_chain(client, app):
    headers = {'X-Forwarded-For': '1.1.1.1, 10.0.0.2'}
    with patch('services.localization.locate') as lookup:
        client.get('/api/v1/localization', headers=headers)
        lookup.assert_not_called()
    with patch.dict(app.config, GEO_TRUSTED_PROXIES='127.0.0.1/32,10.0.0.0/8'):
        with patch('services.localization.locate', return_value={'success': False}) as lookup:
            client.get('/api/v1/localization', headers=headers)
            assert lookup.call_args.args[0] == '1.1.1.1'


def test_catalogs_and_honest_translation_status(client):
    english = client.get('/api/v1/localization/messages/en').json
    hindi = client.get('/api/v1/localization/messages/hi').json
    assert hindi['translation_status'] == 'available'
    assert set(english['messages']) == set(hindi['messages'])
    assert hindi['messages']['Sign in'] != english['messages']['Sign in']
    assert client.get('/api/v1/localization/messages/ta').json['translation_status'] == 'available'
    assert client.get('/api/v1/localization/messages/nyishi').json['messages'] == english['messages']
    assert client.get('/api/v1/localization/messages/unknown').status_code == 404


def test_complete_catalogs_preserve_interpolation_and_translate_story(client):
    import re
    from pathlib import Path
    import json
    root = Path(__file__).resolve().parents[1] / 'locales'
    english = json.loads((root / 'en.json').read_text(encoding='utf-8'))
    for path in root.glob('*.json'):
        translated = json.loads(path.read_text(encoding='utf-8'))
        assert set(translated) == set(english), path.stem
        for key, value in english.items():
            assert sorted(re.findall(r'\{\{.*?\}\}', value)) == sorted(re.findall(r'\{\{.*?\}\}', translated[key])), (path.stem, key)
        if path.stem != 'en':
            assert translated['Better care starts'] != english['Better care starts'], path.stem
            assert translated['Your session has ended. Please sign in again.'] != english['Your session has ended. Please sign in again.'], path.stem
    # An untranslated regional choice must not be the default language.
    result = client.get('/api/v1/localization?state=Arunachal%20Pradesh').json
    assert result['recommended_language'] == 'hi'
