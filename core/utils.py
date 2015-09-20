import re
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


phone_pattern = re.compile(r'''
            # don't match beginning of string, number can start anywhere
(\d{3})     # area code is 3 digits (e.g. '800')
\D*         # optional separator is any number of non-digits
(\d{3})     # trunk is 3 digits (e.g. '555')
\D*         # optional separator
(\d{4})     # rest of number is 4 digits (e.g. '1212')
\D*         # optional separator
(\d*)       # extension is optional and can be any number of digits
$           # end of string
''', re.VERBOSE)
