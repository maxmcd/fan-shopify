import datetime
import flask
import hashlib
import json
import re
import os
import logging
import shopify
import uuid

from fuzzywuzzy import fuzz

from google.appengine.ext import ndb
from google.appengine.api import search

from fan import api
from fan.models import *

class ShopifyFacebookBot(object):

    def __init__(self, shopifyUser, conversation, message=None):
        self.shopifyUser = shopifyUser
        self.conversation = conversation
        self.responses = []

        if message:
            self.message = message
            ShopifyMessage(
                raw=message,
                shopifyConversation=conversation.key,
            ).put()

    def process(self):
        if self.message.get('message'):
            logging.info("got message")

            text = self.message.get('message').get('text')
            text = text.lower()

            if fuzz.ratio("go shopping", text) >= 90:
                self.startShopping()

            if text.startswith('search for'):
                match = re.search('^search for\s?:?\s?(.*)', text)
                if match:
                    self.sendSearchResults(match.group(1))

            if self.conversation.isStarting():
                self.sendWelcomeMessage()

            logging.info(text)

        elif self.message.get('postback'):
            logging.info("got postback")
            # make conversation active if this happens?
            payload = self.message['postback']['payload']
            if payload == "popularProducts":
                self.sendPopularProducts()
            elif payload == "searchForProducts":
                self.sendSearchPrompt()

        return self.responses

    def sendResponses(self):
        for response in self.responses:
            self.sendFacebookMessage(response)

    def addFbMessageTemplate(self, payload):
        self.responses.append({
            "attachment":{
                "type":"template",
                "payload":payload
            }
        })

    def addFbMessageText(self, text):
        self.responses.append({
            "text":text
        })

    def sendFacebookMessage(self, messageObject):
        body = {
            "recipient":{"id":self.conversation.userId},
            "message":messageObject,
        }
        resp = api.facebook(
            "/me/messages/",
            accessToken=self.shopifyUser.facebookPageToken,
            body=body,
        )
        ShopifyMessage(
            raw=body,
            isInbound=False,
            shopifyConversation=self.conversation.key,
        ).put()
        return resp

    def sendGoodbyeMessage(self):
        message = "Hi! It's us again. Let us know if you'd "+\
            "like to continue shopping. If not, no "+\
            "worries, and we'll look forward to future "+\
            "shopping adventures"

        self.addFbMessageText(message)

    def sendPopularProducts(self):
        self.sendProducts(
            self.shopifyUser.getPopularProducts()
        ) 

    def sendProducts(self, products):
        elements = []

        i = 0
        for product in products:
            i += 1
            if i == 10:
                break
            else:
                elements.append(product.getMessageElement(self.shopifyUser))

        self.addFbMessageTemplate({
            "template_type": "generic",
            "elements": elements,
        })

    def sendSearchPrompt(self):
        self.addFbMessageText(
            "Great! To search products type \"Search for:\" before your search.",
        )

    def sendSearchResults(self, term):
        products = self.shopifyUser.search(term)
        if products:
            self.sendProducts(products)
        else:
            self.addFbMessageText(
                "Whoops! We couldn't find any product matches for \"%s\"." % term,
            )            

    def sendWelcomeMessage(self):
        message = self.shopifyUser.welcomeMessage or \
            "Welcome! Type \"Go Shopping\" to shop right here on Messenger."
        self.addFbMessageText(message)

        self.conversation.welcomeMessageSent = True
        self.conversation.put()

    def startShopping(self):
        self.addFbMessageTemplate({
            "template_type":"button",
            "text":"Hey! What kind of products are you looking for?",
            "buttons":[
                {
                    "type":"postback",
                    "title":"Popular Products",
                    "payload":"popularProducts"
                },
                {
                    "type":"postback",
                    "title":"Items On Sale",
                    "payload":"popularProducts"
                },
                {
                    "type":"postback",
                    "title":"Search For Products",
                    "payload":"searchForProducts"
                },
            ]
        })
        self.conversation.active = True
        self.conversation.put()
