from fan.models import User

def user():
    return User.get()

jinjaGlobals = {
    'user':user
}