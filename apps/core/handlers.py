import json
import logging

from tornado.web import RequestHandler
from tornado import gen
import tornado.escape
from pycket.session import SessionMixin

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
