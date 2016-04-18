import flask
import json
import os
import logging

from google.appengine.api import urlfetch

from fan.config import CONFIG

def facebook(path, method="POST", body=None, accessToken=None):
    version = "v2.6"
    url = "https://graph.facebook.com/%s%s?access_token=%s" % (
        version,
        path,
        accessToken,
    )
    resp = urlfetch.Fetch(
        url,
        method=method,
        payload=json.dumps(body),
        headers={'content-type':'application/json'}
    )
    if resp.status_code == 200:
        jsonBody = json.loads(resp.content)
        logging.info(jsonBody)
        return jsonBody
    else:
        logging.info(resp.content)
        raise Exception

def subscribeFacebookPage(accessToken):
    return facebook('/me/subscribed_apps', accessToken=accessToken)

def sendFacebookMessage(userId, message, accessToken):
    resp = facebook('/me/messages/', body={
        "recipient":{"id":userId}, 
        "message":message,
    }, accessToken=shopifyUser.accessToken)
    recipient_id = resp.get('recipient_id')
    message_id = resp.get('message_id')
    return resp


def facebookExtendToken(token):
    return facebook('/oauth/access_token',
        body={
            'grant_type':'fb_exchange_token',
            'fb_exchange_token':token,
            'client_id':CONFIG['facebook']['app_id'],
            'client_secret':CONFIG['facebook']['app_secret'],
        }
    )


def sendFacebookTemplate(userId, payload):
    return sendFacebookMessage(userId, {
        "attachment":{
            "type":"template",
            "payload":payload
        }
    })

def sendFacebookButtonTemplate(userId, message):
    return sendFacebookTemplate(userId, {
        "template_type":"button",
        "text":message,
        "buttons":[
            {
                "type":"web_url",
                "url":"https://petersapparel.parseapp.com",
                "title":"Show Website"
            },
            {
                "type":"postback",
                "title":"Start Chatting",
                "payload":"USER_DEFINED_PAYLOAD"
            },
        ]
    })

def sendFacebookGenericTemplate(userId, message=None):
    # Limits!
    # Title: 45 characters
    # Subtitle: 80 characters
    # Call-to-action title: 20 characters
    # Call-to-action items: 3 buttons
    # Bubbles per message (horizontal scroll): 10 elements

    return sendFacebookTemplate(userId, {
        "template_type": "generic",
        "elements": [
            {
                "title": "Classic White T-Shirt",
                "image_url": "http://petersapparel.parseapp.com/img/item100-thumb.png",
                "subtitle": "Soft white cotton t-shirt is back in style",
                "buttons": [
                    {
                        "type": "web_url",
                        "url": "https://petersapparel.parseapp.com/view_item?item_id=100",
                        "title": "View Item"
                    },
                    {
                        "type": "web_url",
                        "url": "https://petersapparel.parseapp.com/buy_item?item_id=100",
                        "title": "Buy Item"
                    },
                    {
                        "type": "postback",
                        "title": "Bookmark Item",
                        "payload": "USER_DEFINED_PAYLOAD_FOR_ITEM100"
                    }
                ]
            },
            {
                "title": "Classic Grey T-Shirt",
                "image_url": "http://petersapparel.parseapp.com/img/item101-thumb.png",
                "subtitle": "Soft gray cotton t-shirt is back in style",
                "buttons": [
                    {
                        "type": "web_url",
                        "url": "https://petersapparel.parseapp.com/view_item?item_id=101",
                        "title": "View Item"
                    },
                    {
                        "type": "web_url",
                        "url": "https://petersapparel.parseapp.com/buy_item?item_id=101",
                        "title": "Buy Item"
                    },
                    {
                        "type": "postback",
                        "title": "Bookmark Item",
                        "payload": "USER_DEFINED_PAYLOAD_FOR_ITEM101"
                    }
                ]
            }
        ]
    })
