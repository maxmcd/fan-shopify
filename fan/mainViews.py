import flask
import json
import os
import logging
import shopify
import uuid

from google.appengine.api import urlfetch

from fan.models import *
from fan.util import * 
from fan._app import app
from fan import api
from fan.config import CONFIG

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
        return flask.redirect('/app/')

@app.route('/logout/')
def logout():
    User.logout()
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
    EnsureUser()
    return flask.render_template('app.jinja2')

@app.route('/')
def root():
    return flask.render_template('index.jinja2')

@app.errorhandler(404)
def page_not_found(self):
    """Return a custom 404 error."""
    return 'Sorry, nothing at this URL.', 404

@app.errorhandler(RedirectException)
def explicitRedirect(error):
    return flask.redirect(error.location, error.type)

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

@app.route('/shopify/')
def shopifyRoot():
    myshopifyDomain = flask.request.values.get('shop')

    if shopify.Session.validate_params(flask.request.args):

        code = flask.request.values.get('code')
        session = shopify.Session(myshopifyDomain)

        shopifyUser = ShopifyUser.forShop(myshopifyDomain)
        if not shopifyUser:
            shopifyUser = ShopifyUser(myshopifyDomain=myshopifyDomain)

        if shopifyUser.authToken:
            # session = shopify.Session(
            #     shopifyUser.myshopifyDomain,
            #     shopifyUser.authToken
            # )
            # shopify.ShopifyResource.activate_session(session)
            shopifyUser.login()
            return flask.render_template('shopifyRoot.jinja2')
            # try:
            #     flask.request.shop = shopify.Shop.current()
            #     return True
            # except:
            #     return False

        # if there's a code, we need to request an oauth token
        # and then redirect to back to the shop in the users
        # admin
        if code:
            if flask.request.args['state'] != shopifyUser.authState:
                logging.info("auth state provided to shopify does not match returned state")
                flash.abort(400)
            token = session.request_token(flask.request.args)
            shopifyUser.authToken = token
            shopifyUser.put()

            return """
                <script type='text/javascript'>
                  window.top.location.href = "https://%s/admin/apps/%s";
                </script>
            """ % (shopifyUser.myshopifyDomain, CONFIG['shopify']['shopPath'])
        else:
            # if we have neither of those things, then this is
            # an install (or, we're generating a new token), so we have to find/create the user,
            # and start the oauth process
            # if new permissions are added here, the permissions screen will be shown
            scope = [
                'read_products',
            ]

            authState = str(uuid.uuid4())
            shopifyUser.authState = authState
            shopifyUser.put()
            shopifyUser.login()

            permission_url = session.create_permission_url(scope)
            print permission_url
            permission_url += ("&state=" + authState)
            permission_url += ("&redirect_uri=" + "https://7a1424fa.ngrok.io/shopify/")

            return """
                <script type='text/javascript'>
                  window.top.location.href = "%s";
                </script>
            """ % permission_url

    else:
        logging.warning("Misc shopify 400 error")
        flask.abort(400)

@app.route('/facebook-messenger/webhook/', methods=['GET', 'POST'])
def facebookMessangerWebhook():
    print flask.request.values.keys()
    print flask.request.headers
    data = json.loads(flask.request.data)
    print json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))    
    entries = data.get('entry')
    for entry in entries:
        for message in entry.get('messaging'):
            if message.get('message'):
                text = message.get('message').get('text')
                print text
                resp = api.sendFacebookGenericTemplate(message.get('sender'))
                print resp.content
            if message.get('postback'):
                print "got postback!"
                print message.get('postback')
    # # return flask.request.values.get('hub.challenge')
    return "OK"
    # return flask.render_template('shopifyRoot.jinja2')
