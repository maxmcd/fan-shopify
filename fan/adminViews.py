import flask
import json
import os
import logging
import shopify
import uuid

from google.appengine.api import urlfetch
from google.appengine.api import search 

from fan.models import *
from fan.util import * 
from fan._app import app
from fan import api
from fan.config import CONFIG

@app.route('/admin/')
def adminRoot():
    return flask.render_template('admin/adminRoot.jinja2')

@app.route('/admin/shopify-users/')
def adminShopifyUsers():
    shopifyUsers = ShopifyUser.query().fetch()
    return flask.render_template(
        'admin/shopifyUsers.jinja2',
        shopifyUsers=shopifyUsers,
    )

@app.route('/admin/shopify-users/<shopifyUserKey>/')
def adminShopifyUser(shopifyUserKey):
    shopifyUser = ndb.Key(urlsafe=shopifyUserKey).get()
    productCount = ShopifyProduct.query()\
        .filter(ShopifyProduct.shopifyUser == shopifyUser.key)\
        .count()

    return flask.render_template(
        'admin/shopifyUser.jinja2',
        shopifyUser=shopifyUser,
        productCount=productCount,
    )

@app.route('/admin/shopify-users/<shopifyUserKey>/products/')
def adminShopifyUserProducts(shopifyUserKey):
    shopifyUser = ndb.Key(urlsafe=shopifyUserKey).get()
    products = shopifyUser.getProducts()
    return flask.render_template(
        'admin/shopifyProducts.jinja2',
        shopifyUser=shopifyUser,
        products=products,
    )

@app.route('/admin/shopify-users/<shopifyUserKey>/conversations/')
def adminShopifyUserConversations(shopifyUserKey):
    shopifyUser = ndb.Key(urlsafe=shopifyUserKey).get()
    conversations = shopifyUser.getConversations()
    return flask.render_template(
        'admin/shopifyConversations.jinja2',
        shopifyUser=shopifyUser,
        conversations=conversations,
    )

@app.route('/admin/shopify-users/<shopifyUserKey>/conversations/<conversationKey>/')
def adminShopifyUserConversation(shopifyUserKey, conversationKey):
    shopifyUser = ndb.Key(urlsafe=shopifyUserKey).get()
    conversation = ndb.Key(urlsafe=conversationKey).get()
    return flask.render_template(
        'admin/shopifyConversation.jinja2',
        shopifyUser=shopifyUser,
        conversation=conversation,
    )


@app.route('/admin/shopify-users/<shopifyUserKey>/product-search/')
def adminShopifyUserProductSearch(shopifyUserKey):
    shopifyUser = ndb.Key(urlsafe=shopifyUserKey).get()
    query = params.get('q')
    products = shopifyUser.search(query)
        
    return flask.render_template(
        'admin/shopifyProductSearch.jinja2',
        shopifyUser=shopifyUser,
        products=products,
        query=query,
    )
