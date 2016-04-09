import flask
from fan.templating import jinjaGlobals

app = flask.Flask(__name__)
app.config['DEBUG'] = True
app.secret_key = "not so secret"
app.jinja_env.globals.update(jinjaGlobals)

import fan.mainViews
import fan.apiViews