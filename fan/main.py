import flask
import json
import os

from google.appengine.api import urlfetch

from fan.models import *

app = flask.Flask(__name__)
app.config['DEBUG'] = True

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

class RootHandler():

    @app.route('/')
    def root():
        return flask.render_template('index.jinja2')


    @app.route('/ws/', methods=['POST'])
    def websocket():
        resp = flask.Response()
        
        if "OPEN" in flask.request.data:
            respBody = 'OPEN\r\n'
            resp.headers['Sec-WebSocket-Extensions'] = 'grip; message-prefix=""'
            controlMessage = 'c:{"type": "subscribe", "channel": "test"}'
            respBody += "TEXT %s\r\n%s\r\n" % (hex(len(controlMessage)), controlMessage)
        else:
            result = sendChannelMessage("test", flask.request.data)
            # print result.status_code
            respBody = ""

        resp.set_data(respBody)
        resp.headers['Grip-Channel'] = 'test'
        resp.headers['Content-Type'] = 'application/websocket-events'

        return resp

    @app.errorhandler(404)
    def page_not_found(e):
        """Return a custom 404 error."""
        return 'Sorry, nothing at this URL.', 404
