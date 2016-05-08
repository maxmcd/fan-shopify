import json
from fan.models import User
from fan.config import CONFIG

def user():
    return User.get()

def shopifyApiKey():
    return CONFIG['shopify']['api_key']

def applicationHost():
    return CONFIG['application_host']

def facebookAppId():
    return CONFIG['facebook']['app_id']

def isDev():
    return bool(CONFIG.get('dev'))

def version():
    return CONFIG['hash']

def humanDate(datetime):
    return datetime.strftime("%m/%d/%y %I:%M%p")

def prettyJson(data):
    return json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))

jinjaGlobals = {
    'user':user,
    'shopifyApiKey':shopifyApiKey,
    'applicationHost':applicationHost,
    'facebookAppId':facebookAppId,
    'isDev':isDev,
    'version':version,
    'humanDate':humanDate,
    'prettyJson':prettyJson,
}