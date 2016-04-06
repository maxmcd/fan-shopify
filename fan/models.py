import flask
import json
import os
import uuid
import hashlib

from google.appengine.ext import ndb


class BaseModel(ndb.Model):

    __abstract__ = True

    lastUpdate = ndb.DateTimeProperty(auto_now=True)
    created = ndb.DateTimeProperty(auto_now_add=True)

class Team(BaseModel):

    subdomain = ndb.StringProperty()

class User(BaseModel):

    email = ndb.StringProperty()
    passwordHash = ndb.StringProperty()
    passwordSalt = ndb.StringProperty()
    status = ndb.StringProperty()

    requestAttribute = 'user'
    sessionKey = 'userKey'

    @classmethod
    def get(cls):
        if not hasattr(flask.request, cls.requestAttribute):
            user = None
            if not user:
                user = cls.ensureUser()

            flask.request.user = user

        return flask.request.user

    @classmethod
    def ensureUser(cls):
        """
            Ensure that there _is_ a user. This provides a quick
            check that there is an id in the session, and if there
            isn't, then it'll create a new user.

            TODO: skip for search engines?
        """
        userKey = flask.session.get(cls.sessionKey)
        if userKey is None:
            # create a mock user
            user = cls(status='guest')
            return user
        else:
            return ndb.Key(urlsafe=userKey).get()

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
