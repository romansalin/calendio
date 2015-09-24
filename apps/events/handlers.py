import logging

from tornado import gen
from tornado.websocket import WebSocketHandler

from ..core.handlers import BaseHandler, AuthMixin
from ..core.utils import authenticated

logger = logging.getLogger(__name__)


class EventsHandler(BaseHandler, AuthMixin):
    @authenticated()
    def get(self):
        self.render('events/events.html')


class EventsWebSocketHandler(WebSocketHandler):
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
