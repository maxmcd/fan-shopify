import flask
import json
import os

from google.appengine.api import urlfetch

from fan.models import *
from fan.templating import jinjaGlobals

app = flask.Flask(__name__)
app.config['DEBUG'] = True
app.secret_key = "not so secret"
app.jinja_env.globals.update(jinjaGlobals)

def sendChannelMessage(channel, message):

    # meh
    message = message.split("\r\n")[1]

    payload = { 
        "items": [ 
            {
                "channel": channel,
                "formats": { 
                    "ws-message": {"content": message} 
                } 
            } 
        ] 
    }
    
    body = json.dumps(payload)
    return urlfetch.fetch(
        "http://localhost:5561/publish/",
        method="POST",
        payload=body,
    )

class UserHandler():

    @app.route('/login/')
    def getLogin():
        return flask.render_template('login.jinja2')

    @app.route('/login/', methods=['POST'])
    def postLogin():
        email = flask.request.values.get('email')
        password = flask.request.values.get('password')
        user = User.forEmail(email)
        if not user:
            return flask.render_template(
                'login.jinja2',
                notice="Whoops, there is no user with that email."
            )
        elif user.checkPassword(password) == False:
            return flask.render_template(
                'login.jinja2',
                notice="Whoops, that password is incorrect."
            )
        else:
            user.login()
            return flask.redirect('/')

    @app.route('/signup/')
    def getSignup():
        return flask.render_template('signup.jinja2')

    @app.route('/signup/', methods=['POST'])
    def postSignup():
        email = flask.request.values.get('email').lower()
        password = flask.request.values.get('password')
        if not email or not password:
            return flask.abort(400)
        else:
            user = User(email=email)
            user.setPassword(password)
            user.put()
            return flask.redirect('/')

class AppHandler():
    @app.route('/app/')
    def app():
        return flask.render_template('app.jinja2')


class RootHandler():

    @app.route('/')
    def root():
        return flask.render_template('index.jinja2')

    @app.errorhandler(404)
    def page_not_found():
        """Return a custom 404 error."""
        return 'Sorry, nothing at this URL.', 404

class WebsocketHandler():

    @app.route('/ws/', methods=['POST'])
    def websocket():
        resp = flask.Response()

        user = User.get()
        
        if "OPEN" in flask.request.data:
            respBody = 'OPEN\r\n'
            resp.headers['Sec-WebSocket-Extensions'] = 'grip; message-prefix=""'
            controlMessage = 'c:{"type": "subscribe", "channel": "%s"}' % user.key.urlsafe()
            respBody += "TEXT %s\r\n%s\r\n" % (hex(len(controlMessage)), controlMessage)
        else:
            result = sendChannelMessage(user.key.urlsafe(), flask.request.data)
            # print result.status_code
            respBody = ""

        resp.set_data(respBody)
        resp.headers['Grip-Channel'] = 'test'
        resp.headers['Content-Type'] = 'application/websocket-events'

        return resp

