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

@app.route('/admin/shopify-users/<shopifyUserKey>/product-search/')
def adminShopifyUserProductSearch(shopifyUserKey):
    shopifyUser = ndb.Key(urlsafe=shopifyUserKey).get()
    query = params.get('q')

    index = search.Index(shopifyUser.myshopifyDomain)
    results = index.search(
        query=search.Query(
            query,
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
        
    return flask.render_template(
        'admin/shopifyProductSearch.jinja2',
        shopifyUser=shopifyUser,
        products=products,
        query=query,
    )
