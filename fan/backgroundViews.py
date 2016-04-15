import flask
import json
import os
import logging
import shopify
import uuid

from google.appengine.api import urlfetch
from google.appengine.api import search

from fan.models import *
from fan.util import params
from fan._app import app
from fan import api
from fan.config import CONFIG

@app.route('/background/shopify/init/')
def importShopifyStore():
    shopifyUser = params.key('shopifyUser').get()
    return "OK"

@app.route('/background/shopify/products/')
def getProducts():
    shopifyUser = params.key('shopifyUser').get()

@app.route('/background/shopify/products/page/')
def getProductsPage():
    shopifyUser = params.key('shopifyUser').get()
    page = params.get('page')
    return "OK"

@app.route('/background/shopify/products/finalize/')
def finalizeProductsTask():
    shopifyUser = params.key('shopifyUser').get()    
