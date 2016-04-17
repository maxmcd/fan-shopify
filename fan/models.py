import flask
import json
import os
import uuid
import hashlib
import shopify

from google.appengine.ext import ndb
from google.appengine.api import search

from fan import api

class BaseModel(ndb.Model):

    __abstract__ = True

    lastUpdate = ndb.DateTimeProperty(auto_now=True)
    created = ndb.DateTimeProperty(auto_now_add=True)

class User(BaseModel):

    # parent = Team

    email = ndb.StringProperty()
    passwordHash = ndb.StringProperty()
    passwordSalt = ndb.StringProperty()

    requestAttribute = 'user'
    sessionKey = 'userKey'

    @classmethod
    def get(cls):
        if not hasattr(flask.request, cls.requestAttribute):
            user = None
            userKey = flask.session.get(cls.sessionKey)
            if userKey:
                user = ndb.Key(urlsafe=userKey).get()

            flask.request.user = user

        return flask.request.user

    @classmethod
    def forEmail(cls, email):
        email = email.lower()
        return cls.query(cls.email == email).get()

    @classmethod
    def logout(cls):
        if cls.sessionKey in flask.session:
            del flask.session[cls.sessionKey]

    def checkPassword(self, password):
        targetHash = hashlib.sha224(self.passwordSalt + password).hexdigest()
        return targetHash == self.passwordHash

    def getJson(self):
        return {
            'email':self.email,
        }

    def login(self):
        flask.session[self.sessionKey] = self.key.urlsafe()
        flask.session.permanent = True
        flask.request.user = self

    def put(self):
        ndb.Model.put(self)
        self.login()

    def setPassword(self, password):
        self.passwordSalt = str(uuid.uuid4())
        self.passwordHash = hashlib.sha224(self.passwordSalt + password).hexdigest()


class Conversation(BaseModel):

    # parent = Team
    integration = ndb.KeyProperty(kind='Integration')

class Integration(BaseModel):

    # parent = Team

    platform = ndb.StringProperty()
    authData = ndb.PickleProperty()

    def toJson(self):
        return {
            'platform':self.platform,
            'key':self.key.urlsafe(),
        }

class Message(ndb.Model):

    created = ndb.DateTimeProperty(auto_now_add=True)
    converstion = ndb.StringProperty()
    body = ndb.TextProperty()
    token = ndb.StringProperty()

    def toJson(self):
        return {
            'token':self.token,
            'msg':self.body, 
            'created':self.created,
        }

class ShopifyUser(User):

    domain = ndb.StringProperty()
    myshopifyDomain = ndb.StringProperty()
    authState = ndb.StringProperty()
    authToken = ndb.StringProperty()
    pageId = ndb.StringProperty()
    facebookPageName = ndb.StringProperty()
    facebookToken = ndb.StringProperty()
    facebookPageToken = ndb.StringProperty()

    requestAttribute = 'shopifyUser'
    sessionKey = 'shopifyUserKey'

    @classmethod
    def forShop(cls, myshopifyDomain):
        return ShopifyUser.query().filter(
            ShopifyUser.myshopifyDomain == \
            myshopifyDomain
        ).get()

    def getJson(self):
        return {
            'pageId':self.pageId,
            'facebookToken':self.facebookToken,
            'facebookPageName':self.facebookPageName,
        }

    def getFacebookPages(self):
        return api.facebook(
            "/me/accounts", 
            method="GET",
            body={
                'is_promotable':True,
            },
            accessToken=self.facebookToken,
        )

    def activateSession(self):
        if self.authToken == None:
            raise Exception(
                "Can't activate a shopify session without an authToken"
            )

        session = shopify.Session(
            self.myshopifyDomain,
            self.authToken
        )
        shopify.ShopifyResource.activate_session(session)

    def getAdminUrl(self):
        return "/admin/shopify-users/%s/" % self.key.urlsafe()

    def getBuyLink(variantId, quantity=1):
        return "%s/cart/%s:%s" % (
            self.domain,
            variantId,
            quantity,
        )

class ShopifyProduct(BaseModel):

    # id is product id
    shopifyUser = ndb.KeyProperty(kind="ShopifyUser")
    title = ndb.StringProperty()
    handle = ndb.StringProperty()
    bodyHtml = ndb.TextProperty()
    variants = ndb.PickleProperty() #[(id, image, price), ]
    image = ndb.StringProperty()
    # created = ndb.DateTimeProperty()
    productType = ndb.StringProperty()
    publishedScope = ndb.StringProperty()
    tags = ndb.StringProperty()
    price = ndb.StringProperty()
    deleted =ndb.BooleanProperty(default=False)

    def getSearchDocument(self):
        # TODO: add date added field 
        # search.DateField(name='birthday', value=datetime(year=1960, month=6, day=19)),
        return search.Document(
            doc_id = str(self.key.id()),
            fields=[
                search.TextField(name='title', value=self.title),
                search.HtmlField(name='description', value=self.bodyHtml),
                search.TextField(name='tags', value=self.tags),
                search.TextField(name='product_type', value=self.productType),
            ]
        )

class ShopifyMessage(BaseModel):

    pass

class ShopifyConversation(BaseModel):

    shopifyUser = ndb.KeyProperty(kind="ShopifyUser")
    active = ndb.BooleanProperty()
    recipientId = ndb.IntegerProperty()

class Team(BaseModel):

    subdomain = ndb.StringProperty()
