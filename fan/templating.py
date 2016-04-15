from fan.models import User
from fan.config import CONFIG

def user():
    return User.get()

def shopifyApiKey():
    return CONFIG['shopify']['api_key']

jinjaGlobals = {
    'user':user,
    'shopifyApiKey':shopifyApiKey,
}