import json
import logging

from tornado.web import RequestHandler
from tornado import gen
from tornado.websocket import WebSocketHandler
import tornado.escape
from pycket.session import SessionMixin
from pymongo.errors import DuplicateKeyError

from .utils import is_loggedin, authenticated
from .forms import RegistrationForm, LoginForm, ProfileForm
from .models import User

logger = logging.getLogger(__name__)


class BaseHandler(RequestHandler, SessionMixin):
    def __init__(self, application, request, **kwargs):
        self._current_user_object = None
        super(BaseHandler, self).__init__(application, request, **kwargs)

    def render_string(self, template_name, **context):
        context.update({
            'xsrf': self.xsrf_form_html,
            'request': self.request,
            'user': self.current_user,
            'static': self.static_url,
            'handler': self,
            'reverse_url': self.reverse_url,
        })
        return self._jinja_render(path=self.get_template_path(),
                                  filename=template_name,
                                  auto_reload=self.settings['debug'],
                                  **context)

    def _jinja_render(self, path, filename, **context):
        template = self.application.jinja_env.get_template(filename,
                                                           parent=path)
        self.write(template.render(**context))

    @property
    def is_xhr(self):
        return (self.request.headers.get('X-Requested-With', '').lower() ==
                'xmlhttprequest')

    def render_json(self, data):
        self.set_header('Content-Type', 'application/json')
        self.write(json.dumps(data))

    def get_current_user(self):
        return self.session.get('user', None)

    @property
    def db(self):
        return self.application.settings['db']

    @gen.coroutine
    def get_current_user_object(self):
        if not self._current_user_object and self.current_user is not None:
            self._current_user_object = yield self.db.accounts.find_one(
                {'email': self.current_user})
        raise gen.Return(self._current_user_object)


class AuthMixin(object):
    def set_cookie(self, user):
        if user:
            self.set_secure_cookie('user', tornado.escape.json_encode(user))
        else:
            self.clear_cookie('user')

    def set_session(self, user):
        if user:
            self.session.set('user', user)


class MainHandler(BaseHandler):
    @authenticated()
    def get(self):
        self.render('index.html')


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


class EventsHandler(BaseHandler, AuthMixin):
    pass


class WSocketHandler(WebSocketHandler):
    """Tornado Websocket Handler."""

    def check_origin(self, origin):
        return True

    def open(self):
        pass

    def on_close(self):
        pass


@gen.coroutine
def send_event_notification():
    while True:
        pass
