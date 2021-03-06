import flask
import re
import math
import collections

from google.appengine.ext import ndb

from fan.models import *


class RedirectException(Exception):

    def __init__(self, location, type=302):
        self.location = location
        self.type = type


def EnsureUser(abort=False):
    user = User.get()
    print user
    if not user:
        if abort:
            flask.abort(400)
        else:
            raise RedirectException('/login/', 302)
        return False
    return True

class params(object):

    @classmethod
    def get(cls, paramName):
        return flask.request.values.get(paramName)

    @classmethod
    def key(cls, paramName):
        return ndb.Key(
            urlsafe=flask.request.values.get(paramName)
        )