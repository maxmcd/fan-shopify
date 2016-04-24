import datetime
import flask
import hashlib
import json
import os
import shopify
import uuid

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
    facebookPageHandle = ndb.StringProperty()
    tokenExpiresIn = ndb.DateTimeProperty()
    welcomeMessage = ndb.StringProperty()
    requestAttribute = 'shopifyUser'
    sessionKey = 'shopifyUserKey'

    @classmethod
    def forShop(cls, myshopifyDomain):
        return ShopifyUser.query().filter(
            ShopifyUser.myshopifyDomain == \
            myshopifyDomain
        ).get()

    @classmethod
    def forPageId(cls, pageId):
        if pageId:
            return ShopifyUser.query().filter(
                ShopifyUser.pageId == \
                str(pageId)
            ).get()

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

    def getBuyLink(self, variantId, quantity=1):
        return "%s/cart/%s:%s?utm_source=FanCommerce" % (
            self.myshopifyDomain,
            variantId,
            quantity,
        )

    def getViewLink(self, handle, variantId=None):
        url = "http://%s/products/%s?utm_source=FanCommerce" % (
            self.myshopifyDomain, 
            handle,
        )
        if variantId:
            url += ("?variant=" + str(variantId))

        return url

    def getFacebookPages(self):
        return api.facebook(
            "/me/accounts",
            method="GET",
            body={
                'is_promotable':True,
            },
            accessToken=self.facebookToken,
        )

    def _getProductsQuery(self):
        return ShopifyProduct.query()\
            .filter(ShopifyProduct.shopifyUser == self.key)\

    def _getConversationsQuery(self):
        return ShopifyConversation.query()\
            .filter(ShopifyConversation.shopifyUser == self.key)\

    def getProducts(self):
        return self._getProductsQuery().fetch()

    def getConversations(self):
        return self._getConversationsQuery().fetch()

    def getProductCount(self):
        return self._getProductsQuery().count()

    def getConversationCount(self):
        return self._getConversationsQuery().count()

    def getJson(self):
        return {
            'pageId':self.pageId,
            'facebookToken':self.facebookToken,
            'facebookPageName':self.facebookPageName,
            'facebookPageHandle':self.facebookPageHandle,
            'welcomeMessage':self.welcomeMessage,
        }

    def getPopularProducts(self):
        return ShopifyProduct.query()\
            .filter(ShopifyProduct.shopifyUser == self.key)\
            .order(-ShopifyProduct.orderCount)\
            .fetch(limit=10)

    def search(self, term):
        index = search.Index(self.myshopifyDomain)
        results = index.search(
            query=search.Query(
                term,
                options=search.QueryOptions(
                    limit=10,
                    cursor=search.Cursor()
                )
            )
        )
        keys = []
        for result in results.results:
            keys.append(ndb.Key(ShopifyProduct, int(result.doc_id)))

        products = ndb.get_multi(keys)
        return products


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
    deleted = ndb.BooleanProperty(default=False)
    orderCount = ndb.IntegerProperty(default=0)

    def getMessageElement(self, shopifyUser):
        if len(self.variants) > 1:
            buyLink = {
                "type": "postback",
                "title": "Buy Item",
            }
            buyLink["payload"] = "postback://showVariants?id=%d" % self.key.id()
        else:
            url = shopifyUser.getBuyLink(self.variants[0][0])
            buyLink = {
                "type": "web_url",
                "url": url,
                "title": "Buy Item",
            }

        viewUrl = shopifyUser.getViewLink(self.handle)
        return {
            "title": self.title,
            "image_url": self.image,
            "subtitle": self.bodyHtml,
            "buttons": [
                {
                    "type": "web_url",
                    "url": viewUrl,
                    "title": "View Item"
                },
                buyLink,
            ]
        }

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

    def getVariantElements(self):
        pass

class ShopifyMessage(BaseModel):

    shopifyConversation = ndb.KeyProperty(kind="ShopifyConversation")
    isInbound = ndb.BooleanProperty(default=True)
    raw = ndb.PickleProperty()

class ShopifyConversation(BaseModel):

    shopifyUser = ndb.KeyProperty(kind="ShopifyUser")
    active = ndb.BooleanProperty(default=False)
    welcomeMessageSent = ndb.BooleanProperty(default=False)
    searching = ndb.BooleanProperty(default=False)
    userId = ndb.IntegerProperty()

    @classmethod
    def findOrCreate(self, shopifyUser, userId):
        existing = self.query()\
        .filter(self.shopifyUser == shopifyUser.key)\
        .filter(self.userId == userId)\
        .get()
        if existing:
            return existing
        else:
            sc = self(
                shopifyUser=shopifyUser.key,
                userId=userId,
            )
            sc.put()
            return sc

    @classmethod
    def getActive(cls):
        return cls.query()\
            .filter(cls.active == True)\
            .fetch()

    def isStarting(self):
        return bool(not self.welcomeMessageSent and not self.active)

    def getMessageCount(self):
        return ShopifyMessage.query()\
            .filter(ShopifyMessage.shopifyConversation == self.key)\
            .count()

    def recentMessageCount(self, minutes=20):
        return ShopifyMessage.query()\
            .filter(ShopifyMessage.shopifyConversation == self.key)\
            .filter(ShopifyMessage.created < \
                datetime.datetime.now() - \
                datetime.timedelta(minutes=minutes))\
            .count()


class Team(BaseModel):

    subdomain = ndb.StringProperty()
