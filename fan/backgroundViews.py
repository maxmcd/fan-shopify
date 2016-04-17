import flask
import json
import os
import logging
import shopify
import uuid
import datetime

from google.appengine.api import urlfetch
from google.appengine.api import search
from google.appengine.ext import ndb
from google.appengine.api import taskqueue

from fan.models import *
from fan.util import params
from fan._app import app
from fan import api
from fan.config import CONFIG

@app.route('/background/shopify/init/', methods=['POST', 'GET'])
def importShopifyStore():
    shopifyUser = params.key('shopifyUser').get()
    taskqueue.add(
        url='/background/shopify/products/', 
        params={
            'shopifyUser':shopifyUser.key.urlsafe(),
        },
        target="default",
    )
    return "OK"

@app.route('/background/shopify/products/', methods=['POST', 'GET'])
def getProducts():
    shopifyUser = params.key('shopifyUser').get()
    shopifyUser.activateSession()
    productCount = shopify.Product.count()
    pageSize = 50
    totalPages = (productCount/pageSize) + 1
    taskqueue.add(
        url="/background/shopify/products/page/",
        params={
            'shopifyUser':shopifyUser.key.urlsafe(),
            'page':1,
            'totalPages':totalPages,
            'pageSize':pageSize,
        },
        target="default",
    )
    return "OK"

@app.route('/background/shopify/products/page/', methods=['POST', 'GET'])
def getProductsPage():
    shopifyUser = params.key('shopifyUser').get()
    page = int(params.get('page'))
    totalPages = int(params.get('totalPages'))
    pageSize = int(params.get('pageSize'))

    logging.info(flask.request.values)
    logging.info(page)
    logging.info(pageSize)

    documents = []

    shopifyUser.activateSession()

    products = shopify.Product.find(limit=pageSize, page=page, published_status="published")
    for product in products:

        variants = []
        images = {}
        for image in product.images:
            images[image.id] = image.src

        for variant in product.variants:
            image = None
            if not variant.image_id:
                image = product.image.src
            else:
                image = images[variant.image_id]

            variants.append((
                variant.id,
                image,
                variant.price
            ))

        shopifyProduct = ShopifyProduct(
            shopifyUser=shopifyUser.key,
            title=product.title,
            bodyHtml=product.body_html,
            image=product.image.src,
            id=product.id,
            handle=product.handle,
            productType=product.product_type,
            tags=product.tags,
            variants=variants,
        )
        shopifyProduct.put()

        documents.append(shopifyProduct.getSearchDocument())

    index = search.Index(name=shopifyUser.myshopifyDomain)
    index.put(documents)

    if page == totalPages:
        taskqueue.add(
            url="/background/shopify/products/finalize/",
            params={'shopifyUser':shopifyUser.key.urlsafe()},
            target="default",
        )
    else:
        page += 1
        taskqueue.add(
            url="/background/shopify/products/page/",
            params={
                'shopifyUser':shopifyUser.key.urlsafe(),
                'page':page,
                'totalPages':totalPages,
            },
            target="default",
        )

    return "OK"

@app.route('/background/shopify/products/finalize/', methods=['POST', 'GET'])
def finalizeProductsTask():
    shopifyUser = params.key('shopifyUser').get()
    expiredProducts = ShopifyProduct.query()\
        .filter(ShopifyProduct.shopifyUser == shopifyUser.key)\
        .filter(ShopifyProduct.lastUpdate > datetime.datetime.now() - datetime.timedelta(days=2))\
        .fetch()

    for product in expiredProducts:
        product.deleted = True

    ndb.put_multi(expiredProducts)

    searchDocumentsToDelete = [str(x.key.id()) for x in expiredProducts]
    index = search.Index(name=shopifyUser.myshopifyDomain)
    index.delete(searchDocumentsToDelete)

    return "OK"
