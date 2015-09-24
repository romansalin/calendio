import logging

from tornado import gen
from pymongo.errors import DuplicateKeyError

from ..core.handlers import BaseHandler, AuthMixin
from ..core.utils import is_loggedin, authenticated
from .forms import RegistrationForm, LoginForm, ProfileForm
from .models import User

logger = logging.getLogger(__name__)


class LoginHandler(BaseHandler, AuthMixin):
    @is_loggedin()
    def get(self):
        self.render('account/login.html', form=LoginForm())

    @gen.coroutine
    @is_loggedin()
    def post(self):
        form = LoginForm(self.request.arguments)
        if form.validate():
            user = yield User.find_one(self.db, {
                'email': form.email.data})
            if user and user.check_password(form.password.data):
                self.set_session(str(user.email))
                self.redirect(self.reverse_url('index'))
                return
        form.set_nonfield_error('email_or_password_error')
        self.render('account/login.html', form=form)


class LogoutHandler(BaseHandler):
    def get(self):
        self.session.delete('user')
        self.redirect(self.reverse_url('index'))


class SignupHandler(BaseHandler, AuthMixin):
    @is_loggedin()
    def get(self):
        self.render('account/signup.html', form=RegistrationForm())

    @gen.coroutine
    @is_loggedin()
    def post(self):
        form = RegistrationForm(self.request.arguments)
        if form.validate():
            user = form.get_object()
            user.set_password(user.password)
            try:
                yield user.insert(self.db)
            except DuplicateKeyError:
                form.set_field_error('email', 'email_occupied')
            else:
                self.set_session(str(user.email))
                self.redirect(self.reverse_url('index'))
                return
        self.render('account/signup.html', form=form)


class ProfileHandler(BaseHandler, AuthMixin):
    @gen.coroutine
    @authenticated()
    def get(self):
        obj = yield self.get_current_user_object()
        response = dict(
            form=ProfileForm(),
            obj=obj,
        )
        self.render('account/profile.html', **response)

    @gen.coroutine
    @authenticated()
    def post(self):
        form = ProfileForm(self.request.arguments)
        # if form.validate():
        #     user = form.get_object()
        #     user.set_password(user.password)
        #     try:
        #         yield user.insert(self.db)
        #     except DuplicateKeyError:
        #         form.set_field_error('email', 'email_occupied')
        #     else:
        #         self.set_session(str(user.email))
        #         self.redirect(self.reverse_url('index'))
        #         return
        obj = yield self.get_current_user_object()
        response = dict(
            form=ProfileForm(),
            obj=obj,
        )
        self.render('account/profile.html', **response)
