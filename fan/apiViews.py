from fan.models import *
from fan.util import *
from _app import app

def createResponse(name, items):
    out = {
        name: []
    }
    for item in items:
        out[name].append(item.toJson())
    return out

@app.route('/api/v1/messages/')
def messages():
    EnsureUser(True)
    messages = Message.query().order(Message.created).fetch()
    return flask.jsonify(createResponse('messages', messages))

@app.route('/api/v1/platforms/')
def getPlatforms():
    return flask.jsonify({'platforms': [
        {
            'name':'Twilio',
            'logo':'twilio.png',
            'fields':[
                {
                    'type':'text',
                    'name':'accountSid',
                    'label':'Account Sid',
                },
                {
                    'type':'text',
                    'name':'authToken',
                    'label':'Auth Token',
                },
            ],
        }
    ]})

@app.route('/api/v1/integrations/')
def getIntegrations():
    EnsureUser(True)
    user = User.get()
    teamKey = user.key.parent()
    integrations = Integration.query(ancestor=teamKey).fetch()
    return flask.jsonify(createResponse('integrations', integrations))

@app.route('/api/v1/integrations/', methods=['POST'])
def createIntegration():
    EnsureUser(True)
    platform = flask.request.values.get('platform')
    authData = flask.request.values.get('authData')
    user = User.get()
    integration = Integration(
        parent=user.key.parent(),
        platform=platform,
        authData=json.loads(authData),
    )
    integration.put()
    return flask.jsonify(integration.toJson())

