import hashlib
import uuid
from functools import wraps


def make_pass(password):
    salt = uuid.uuid4().hex
    hash_ = hashlib.sha512(password + salt).hexdigest()
    return salt, hash_


def check_pass(password, hash_, salt):
    return hash_ == hashlib.sha512(password + salt).hexdigest()


def is_loggedin(redirect_to='index'):
    def decorator(method):
        @wraps(method)
        def wrapper(self, *args, **kwds):
            if self.session.get('user', False):
                self.redirect(self.reverse_url(redirect_to))
                return
            else:
                return method(self, *args, **kwds)
        return wrapper
    return decorator
