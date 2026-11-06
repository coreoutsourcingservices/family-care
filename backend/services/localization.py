"""Product language recommendations; not a list of official state languages."""
import ipaddress
import json
import time
from functools import lru_cache
from pathlib import Path
from urllib.request import urlopen
from flask import Blueprint, request, jsonify, current_app
from core.routing import route

STATE_DATA = """Andhra Pradesh|Telugu
Arunachal Pradesh|Nyishi,Adi,Apatani,Monpa
Assam|Assamese,Bodo,Bengali
Bihar|Bhojpuri,Maithili,Magahi
Chhattisgarh|Chhattisgarhi,Gondi
Goa|Konkani,Marathi
Gujarat|Gujarati,Kutchi
Haryana|Haryanvi
Himachal Pradesh|Kangri,Mandeali,Pahari
Jharkhand|Santali,Nagpuri,Mundari
Karnataka|Kannada,Tulu,Konkani
Kerala|Malayalam
Madhya Pradesh|Bundeli,Bagheli,Malvi,Gondi
Maharashtra|Marathi
Manipur|Manipuri,Tangkhul
Meghalaya|Khasi,Garo
Mizoram|Mizo
Nagaland|Ao,Angami,Sumi,Nagamese
Odisha|Odia,Santali
Punjab|Punjabi
Rajasthan|Marwari,Mewari,Dhundhari
Sikkim|Nepali,Bhutia,Lepcha
Tamil Nadu|Tamil
Telangana|Telugu,Urdu
Tripura|Bengali,Kokborok
Uttar Pradesh|Hindi,Awadhi,Bhojpuri,Braj
Uttarakhand|Garhwali,Kumaoni
West Bengal|Bengali,Nepali,Santali
Andaman and Nicobar Islands|Nicobarese,Bengali,Tamil
Chandigarh|Punjabi
Dadra and Nagar Haveli and Daman and Diu|Gujarati,Konkani,Marathi,Warli
Delhi|Hindi,Punjabi,Urdu
Jammu and Kashmir|Kashmiri,Dogri
Ladakh|Ladakhi,Balti,Purgi
Lakshadweep|Malayalam,Jeseri,Mahl
Puducherry|Tamil,Telugu,Malayalam,French"""
STATES = dict(line.split('|') for line in STATE_DATA.splitlines())
CODES = dict(zip('English Hindi Marathi Tamil Gujarati Telugu Bengali Kannada Malayalam Punjabi Urdu Odia Assamese Nepali French'.split(), 'en hi mr ta gu te bn kn ml pa ur or as ne fr'.split()))
LANGUAGES = {CODES.get(name, name.lower()): name for name in {'English','Hindi',*(n for names in STATES.values() for n in names.split(','))}}
NATIVE_NAMES = {'en':'English','hi':'हिन्दी','mr':'मराठी','ta':'தமிழ்','gu':'ગુજરાતી','te':'తెలుగు',
                'bn':'বাংলা','kn':'ಕನ್ನಡ','ml':'മലയാളം','pa':'ਪੰਜਾਬੀ','ur':'اردو','or':'ଓଡ଼ିଆ',
                'as':'অসমীয়া','ne':'नेपाली','fr':'Français','bhojpuri':'भोजपुरी','maithili':'मैथिली',
                'konkani':'कोंकणी','manipuri':'ꯃꯤꯇꯩꯂꯣꯟ','mizo':'Mizo','dogri':'डोगरी',
                'awadhi':'अवधी','marwari':'मारवाड़ी','khasi':'Khasi','santali':'ᱥᱟᱱᱛᱟᱲᱤ',
                'tulu':'ತುಳು','kokborok':'Kokborok'}

def normalize(value):
    return value.lower().replace('&','and').replace('-', ' ').strip()

def find_state(value):
    value = normalize(value)
    value = {'orissa':'odisha','pondicherry':'puducherry','nct of delhi':'delhi','national capital territory of delhi':'delhi','uttaranchal':'uttarakhand'}.get(value,value)
    return next((name for name in STATES if normalize(name)==value), None)

@lru_cache(maxsize=2048)
def locate(address, hour):
    # Fixed HTTPS host and validated global IP: no arbitrary URL or server-IP lookup.
    with urlopen('https://ipwho.is/' + address + '?fields=success,country_code,region', timeout=3) as response:
        data = json.loads(response.read(16384))
    return data

def caller_ip():
    address = request.remote_addr or ''
    # Only explicitly configured network proxies may supply forwarding information.
    networks = [ipaddress.ip_network(n.strip()) for n in current_app.config.get('GEO_TRUSTED_PROXIES','').split(',') if n.strip()]
    chain = [x.strip() for x in request.headers.get('X-Forwarded-For','').split(',') if x.strip()]
    try:
        while chain and any(ipaddress.ip_address(address) in network for network in networks):
            address = chain.pop()
        return ipaddress.ip_address(address)
    except ValueError:
        return None

@lru_cache(maxsize=128)
def load_catalog(code):
    """Static deployment assets; restart workers after changing a catalog."""
    root=Path(__file__).resolve().parents[1] / 'locales'
    path=root/(code+'.json')
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def translation_status(code):
    translated=load_catalog(code)
    if not translated:
        return 'english_fallback'
    english=load_catalog('en')
    return 'available' if set(english)<=set(translated) else 'partial'

def language_option(code):
    return dict(code=code,name=LANGUAGES[code],native_name=NATIVE_NAMES.get(code,LANGUAGES[code]),translation_status=translation_status(code),fallback_language='en',direction='rtl' if code=='ur' else 'ltr')

def language_options(state):
    names = STATES.get(state,'').split(',') if state else []
    names = list(dict.fromkeys([n for n in names if n and n not in ('Hindi','English')]))[:3] + ['Hindi','English']
    return [language_option(CODES.get(n,n.lower())) for n in names]

bp = Blueprint('localization', __name__, url_prefix='/api/v1/localization')

def recommendations():
    preview = request.args.get('state')
    state = find_state(preview) if preview else None
    status = 'manual' if state else 'unknown'
    country = 'IN' if state else None
    if preview and not state:
        return jsonify(error=dict(code='invalid_state',message='Choose a state from /api/v1/localization/states')),400
    if not preview:
        address = caller_ip()
        if not address or not address.is_global:
            status='private_ip'
        else:
            try:
                data=locate(str(address),int(time.time()//3600))
                if data.get('success'):
                    country=data.get('country_code')
                    state=find_state(data.get('region','')) if country=='IN' else None
                    status='detected' if state else 'outside_supported_region'
                else:
                    status='lookup_unavailable'
            except (OSError,ValueError,TimeoutError):
                status='lookup_unavailable'
    options=language_options(state)
    return jsonify(location=dict(country_code=country,state=state,status=status,approximate=True),languages=options,recommended_language=next((o['code'] for o in options if o['translation_status']=='available'), 'en') if state else 'en',fallback_language='en',manual_state_selection=True)

def states():
    return jsonify(items=[dict(name=name,type='state' if i<28 else 'union_territory',languages=language_options(name),regional_languages=names.split(',')) for i,(name,names) in enumerate(STATES.items())])

def all_languages():
    items = [language_option(code) for code in sorted(LANGUAGES, key=lambda code: LANGUAGES[code].casefold())]
    return jsonify(items=items, total=len(items))


def messages(language):
    if language not in LANGUAGES:
        return jsonify(error=dict(code='unsupported_language',message='Unknown language code')),404
    english=load_catalog('en')
    translated=load_catalog(language)
    return jsonify(language=language,fallback_language='en',translation_status=translation_status(language),messages={**english,**translated})

route(bp,'',recommendations)
route(bp,'/states',states)
route(bp,'/languages',all_languages)
route(bp,'/messages/<language>',messages)
