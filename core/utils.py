import hashlib
import uuid
from functools import wraps


def make_pass(password):
    salt = uuid.uuid4().hex
    hash_ = hashlib.sha512(password.encode('utf-8') +
                           salt.encode('utf-8')).hexdigest()
    return salt, hash_


def check_pass(password, hash_, salt):
    return hash_ == hashlib.sha512(password.encode('utf-8') +
                                   salt.encode('utf-8')).hexdigest()


def is_loggedin(redirect_to='index'):
    def decorator(fn):
        @wraps(fn)
        def wrapper(self, *args, **kwargs):
            if self.session.get('user', False):
                self.redirect(self.reverse_url(redirect_to))
                return
            else:
                return fn(self, *args, **kwargs)
        return wrapper
    return decorator


def authenticated(redirect_to='login'):
    def decorator(fn):
        @wraps(fn)
        def wrapper(self, *args, **kwargs):
            if not self.session.get('user', False):
                self.redirect(self.reverse_url(redirect_to))
                return
            else:
                return fn(self, *args, **kwargs)
        return wrapper
    return decorator
