import flask
import shopify
from fan.config import CONFIG
from fan.templating import jinjaGlobals

app = flask.Flask(__name__)
app.config['DEBUG'] = True
app.secret_key = "not so secret"
app.jinja_env.globals.update(jinjaGlobals)

shopify.Session.setup(
    api_key=CONFIG['shopify']['api_key'], 
    secret=CONFIG['shopify']['shared_secret']
)

import fan.mainViews
import fan.apiViews
import fan.adminViews