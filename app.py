import logging
import json

from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler, StaticFileHandler, url
from tornado import gen
from tornado.websocket import WebSocketHandler
from tornado.httpserver import HTTPServer
from tornado.options import options
import tornado.escape
from pycket.session import SessionMixin
from pymongo.errors import DuplicateKeyError

import settings as conf
from core.utils import is_loggedin
from core.forms import RegistrationForm, LoginForm
from core.models import UserModel

logger = logging.getLogger(__name__)


class BaseHandler(RequestHandler, SessionMixin):
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
        return self.request.headers.get('X-Requested-With', '').lower() \
            == 'xmlhttprequest'

    def render_json(self, data):
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(data))

    def get_current_user(self):
        return self.session.get('user', None)

    @property
    def db(self):
        return self.application.db

    @gen.coroutine
    def get_current_user_object(self):
        if self.current_user is not None:
            # TODO cache
            user = yield self.db.accounts.find_one({"_id": self.current_user})
        else:
            user = None
        raise gen.Return(user)


class AuthMixin(object):
    def set_current_user(self, user):
        if user:
            self.set_secure_cookie('user', tornado.escape.json_encode(user))
        else:
            self.clear_cookie('user')

    def set_session(self, user):
        if user:
            self.session.set('user', user)


class MainHandler(BaseHandler):
    # @tornado.web.authenticated
    @gen.coroutine
    def get(self):
        self.render('index.html')


class LoginHandler(BaseHandler, AuthMixin):

    @is_loggedin(redirect_to='index')
    def get(self):
        self.render('account/login.html', form=LoginForm())

    @gen.coroutine
    @is_loggedin(redirect_to='index')
    def post(self):
        form = LoginForm(self.request.arguments)
        if form.validate():
            user = yield UserModel.find_one(self.db, {
                "email": form.email.data})
            if user:
                if user.check_password(form.password.data):
                    self.set_session(str(user.email or user._id))
                    self.redirect(self.reverse_url('index'))
                    return
                else:
                    form.set_field_error('password', 'wrong_password')
            else:
                form.set_field_error('email', 'not_found')
        self.render('account/login.html', form=form)


class LogoutHandler(BaseHandler):
    def get(self):
        self.session.delete('user')
        self.redirect(self.reverse_url('index'))


class SignupHandler(AuthMixin, BaseHandler):
    @is_loggedin(redirect_to='index')
    def get(self):
        self.render('account/signup.html', form=RegistrationForm())

    @tornado.gen.coroutine
    @is_loggedin(redirect_to='index')
    def post(self):
        form = RegistrationForm(self.request.arguments)
        if form.validate():
            user = form.get_object()
            user.set_password(user.password)
            try:
                yield user.insert(self.db)
                # print user
            except DuplicateKeyError:
                form.set_field_error('email', 'email_occupied')
            else:
                # user save succeeded
                self.set_session(str(user.email or user._id))
                self.redirect(self.reverse_url('index'))
                return
        self.render('account/signup.html', form=form)


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


class CalendIO(Application):
    def __init__(self, *args, **kwargs):
        # Init jiaja2 environment
        self.jinja_env = conf.JINJA_ENV
        # Register filters for jinja2
        # self.jinja_env.filters.update(filters.register_filters())
        self.jinja_env.tests.update({})
        self.jinja_env.globals['settings'] = conf.APP_SETTINGS

        url_patterns = [
            url(r'/', MainHandler, name='index'),
            url(r'/login', LoginHandler, name='login'),
            url(r'/logout', LogoutHandler, name='logout'),
            url(r'/signup', SignupHandler, name='signup'),
            # url(r'/profile', ProfileHandler, name='profile'),
            # url(r'/calend', CalendHandler, name='calend'),
            url(r'/ws', WSocketHandler),
            url(r'/static/(.*)', StaticFileHandler, {'path': 'static/'}),
        ]
        super(CalendIO, self).__init__(url_patterns, *args,
                                       **dict(conf.APP_SETTINGS, **kwargs))


def main():
    http_server = HTTPServer(CalendIO(), xheaders=True)
    http_server.listen(options.port)
    # IOLoop.current().add_callback(send_event_notification)
    loop = IOLoop.instance()
    logger.info('Server running on http://localhost:{}'.format(options.port))
    loop.start()


if __name__ == '__main__':
    main()
