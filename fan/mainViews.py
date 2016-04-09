import flask
import json
import os
import logging

from google.appengine.api import urlfetch

from fan.models import *
from fan._app import app

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

@app.route('/app/')
def appIndex():
    return flask.render_template('app.jinja2')


@app.route('/')
def root():
    return flask.render_template('index.jinja2')

@app.errorhandler(404)
def page_not_found(self):
    """Return a custom 404 error."""
    return 'Sorry, nothing at this URL.', 404


def sendChannelMessage(channel, message):

    payload = { 
        "items": [ 
            {
                "channel": channel,
                "formats": { 
                    "ws-message": {"content": json.dumps(message)} 
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

@app.route('/ws/', methods=['POST'])
def websocket():
    resp = flask.Response()
    resp.headers['Content-Type'] = 'application/websocket-events'

    respBody = "" # response can't be None

    user = User.get()
    channelName = user.key.urlsafe()
    
    message = flask.request.data
    logging.info(message)

    parts = message.split('\r\n')
    verb = parts.pop(0)
    body = "\r\n".join(parts)
    # does not support multi-part messages

    if verb == "OPEN":
        respBody = 'OPEN\r\n'
        resp.headers['Sec-WebSocket-Extensions'] = 'grip; message-prefix=""'
        controlMessage = 'c:{"type": "subscribe", "channel": "%s"}' % channelName
        respBody += "TEXT %s\r\n%s\r\n" % (hex(len(controlMessage)), controlMessage)
    elif "TEXT" in verb:
        messageData = json.loads(body)
        message = Message(
            converstion="test", 
            body=messageData['msg'], 
            token=messageData['token'],
        )
        result = sendChannelMessage(channelName, message.toJson())
        message.put()

    resp.set_data(respBody)

    return resp
