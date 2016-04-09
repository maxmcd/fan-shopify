

class BasePlatform(object):

    __abstract__ = True

    name = None

    def sendMessage(message, user, **kwargs):
        pass

    def getConversationkey(attribute):
        return "%s|%s", (name, attribute)

class Twilio(BasePlatform)

    name = "twilio"

    def getConversationKey(self, phoneNumber):
        return super(phoneNumber)

