import datetime
import flask
import json
import logging
import os
import re
import shopify
import uuid

from google.appengine.api import urlfetch
from google.appengine.api import taskqueue
from google.appengine.api import search 

from fan.models import *
from fan.util import * 
from fan._app import app
from fan import api
from fan.config import CONFIG
from fan.bot import ShopifyFacebookBot

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
    return flask.render_template(
        'index.jinja2',
        bodyClass="homepage"
        )

@app.route('/favicon.ico')
def favicon():
    return flask.redirect('/static/images/favicon.png')

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

    def shopifyRootResponse(dev=False):
        return flask.render_template(
            'shopifyRoot.jinja2',
            bodyClass="shopify",
            myshopifyDomain=shopifyUser.myshopifyDomain,
            shopifyUserJson=json.dumps(shopifyUser.getJson()),
            dev=dev,
        )

    referrer = flask.request.referrer or ""
    dev = (CONFIG['dev'] and "shopify" not in referrer)
    
    shopifyUser = ShopifyUser.get()
    if shopifyUser:
        return shopifyRootResponse(dev=dev)

    if dev:
        shopifyUser = ShopifyUser.forShop('fan-shop-5.myshopify.com')
        shopifyUser.login()
        return shopifyRootResponse(dev=True)

    myshopifyDomain = flask.request.values.get('shop')

    if shopify.Session.validate_params(flask.request.args):

        code = flask.request.values.get('code')
        session = shopify.Session(myshopifyDomain)

        shopifyUser = ShopifyUser.forShop(myshopifyDomain)
        if not shopifyUser:
            shopifyUser = ShopifyUser(myshopifyDomain=myshopifyDomain)

        if shopifyUser.authToken:
            shopifyUser.login()
            return shopifyRootResponse()

        # if there's a code, we need to request an oauth token
        # and then redirect to back to the shop in the users
        # admin
        if code:
            if flask.request.args['state'] != shopifyUser.authState:
                logging.info("auth state provided to shopify does not match returned state")
                flash.abort(400)
            token = session.request_token(flask.request.args)
            shopifyUser.authToken = token
            shopifyUser.activateSession()
            shop = shopify.Shop.current()
            shopifyUser.email = shop.email
            taskqueue.add(
                url='/background/shopify/init/', 
                params={
                    'shopifyUser':shopifyUser.key.urlsafe(),
                }, 
            )
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
            redirect_uri = "https://%s/shopify/" % CONFIG['application_host']
            permission_url += ("&redirect_uri=" + redirect_uri)

            return """
                <script type='text/javascript'>
                  window.top.location.href = "%s";
                </script>
            """ % permission_url

    else:
        logging.warning("Session params failed validation")
        flask.abort(400)

@app.route('/shopify/get-facebook-pages/', methods=['GET', 'POST'])
def getFacebookPages():
    shopifyUser = ShopifyUser.get()

    facebookToken = params.get('facebookToken')

    if facebookToken:
        resp = api.facebookExtendToken(facebookToken)
        shopifyUser.facebookToken = resp.get('access_token')
        if resp.get('expires_in'):
            expires = datetime.datetime.now() + datetime.timedelta(seconds=resp.get('expires_in'))
            shopifyUser.tokenExpiresIn = expires
        shopifyUser.put()

    pages = shopifyUser.getFacebookPages()

    return flask.jsonify({'pages':pages})

@app.route('/shopify/select-page/', methods=['GET', 'POST'])
def selectFacebookPage():
    shopifyUser = ShopifyUser.get()

    pageId = params.get('pageId')
    facebookPageToken = params.get('facebookPageToken')
    facebookPageName = params.get('facebookPageName')

    shopifyUser.pageId = pageId
    shopifyUser.facebookPageToken = facebookPageToken
    shopifyUser.facebookPageName = facebookPageName
    shopifyUser.put()

    return flask.jsonify(api.subscribeFacebookPage(facebookPageToken))

@app.route('/shopify/update-user/')
def updateUser():
    shopifyUser = ShopifyUser.get()
    welcomeMessage = params.get('welcomeMessage')
    shopifyUser.welcomeMessage = welcomeMessage
    shopifyUser.put()
    return flask.jsonify(shopifyUser.getJson())

@app.route('/facebook-messenger/webhook/', methods=['GET', 'POST'])
def facebookMessangerWebhook():
    try:
        challenge = params.get('hub.challenge')
        if challenge:
            return challenge

        print flask.request.data
        data = json.loads(flask.request.data)
        logging.info(data)
        # json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
        entries = data.get('entry')
        for entry in entries:
            processWebhookEntry(entry)
    except Exception as e:
        # raise
        if CONFIG['dev']:
            print e
        else:
            raise

    return "OK"

def processWebhookEntry(entry):
    pageId = entry.get('id')
    shopifyUser = ShopifyUser.forPageId(pageId)
    flask.request.shopifyUser = shopifyUser
    if shopifyUser:
        for message in entry.get('messaging'):
            processWebhookMessage(shopifyUser, message)

def processWebhookMessage(shopifyUser, message):
    recipientId = message['recipient']['id']
    senderId = message['sender']['id']
    userId = senderId # on reciept 

    conversation = ShopifyConversation.findOrCreate(shopifyUser, userId)

    bot = ShopifyFacebookBot(shopifyUser, conversation, message)
    bot.process()
    bot.sendResponses()
    logging.info(bot.responses)
