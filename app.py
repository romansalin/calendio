import logging

from tornado.ioloop import IOLoop
from tornado.web import Application, StaticFileHandler, url
from tornado.httpserver import HTTPServer
from tornado.options import options

import settings as conf
from core.handlers import (MainHandler, LoginHandler, LogoutHandler,
                           SignupHandler, WSocketHandler, ProfileHandler,
                           EventsHandler)

logger = logging.getLogger(__name__)


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
            url(r'/profile', ProfileHandler, name='profile'),
            url(r'/events', EventsHandler, name='events'),
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
    logger.info('Server running on http://localhost:{0}'.format(options.port))
    loop.start()


if __name__ == '__main__':
    main()
