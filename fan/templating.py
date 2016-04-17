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

jinjaGlobals = {
    'user':user,
    'shopifyApiKey':shopifyApiKey,
    'applicationHost':applicationHost,
    'facebookAppId':facebookAppId,
    'isDev':isDev,
}